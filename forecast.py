"""Module to get forecast using REST from WeatherFlow."""
import asyncio
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError
from datetime import datetime
from typing import Optional, OrderedDict

import logging

from const import (
    ATTRIBUTION,
    ATTR_ATTRIBUTION,
    ATTR_BRAND,
    BRAND,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_PRESSURE,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    BASE_URL,
    CONDITION_CLASSES,
    DEFAULT_TIMEOUT,
    FORECAST_HOURLY_HOURS,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
    UTC,
)
from helpers import ConversionFunctions

_LOGGER = logging.getLogger(__name__)

class Forecast:

    def __init__(self, station_id, unit_system, token, session: Optional[ClientSession] = None,):
        self._station_id = station_id
        self._token = token
        self._unit_system = unit_system
        self._session: ClientSession = session
        self.req = session

    async def update_forecast(self):
        """Return the formatted forecast data."""
        endpoint = f"better_forecast?station_id={self._station_id}&token={self._token}"
        json_data = await self.async_request("get", endpoint)
        items = []
        cnv = ConversionFunctions(self._unit_system)

        # We need a few Items from the Current Conditions section
        current_cond = json_data.get("current_conditions")
        current_condition = current_cond["conditions"]
        current_icon = current_cond["icon"]
        today = datetime.date(datetime.now())

        # Prepare for MQTT
        condition_data = OrderedDict()
        condition_state = await self.ha_condition_value(current_icon)
        condition_data["weather"] = condition_state

        forecast_data = json_data.get("forecast")

        # We also need Day hign and low Temp from Today
        temp_high_today = await cnv.temperature(forecast_data[FORECAST_TYPE_DAILY][0]["air_temp_high"])
        temp_low_today = await cnv.temperature(forecast_data[FORECAST_TYPE_DAILY][0]["air_temp_low"])

        # Process Daily Forecast
        fcst_data = OrderedDict()
        fcst_data[ATTR_ATTRIBUTION] = ATTRIBUTION
        fcst_data[ATTR_BRAND] = BRAND
        fcst_data["temp_high_today"] = temp_high_today
        fcst_data["temp_low_today"] = temp_low_today

        for row in forecast_data[FORECAST_TYPE_DAILY]:
            # Skip over past forecasts - seems the API sometimes returns old forecasts
            forecast_time = datetime.date(datetime.fromtimestamp(row["day_start_local"]))
            if today > forecast_time:
                continue

            # Calculate data from hourly that's not summed up in the daily.
            precip = 0
            wind_avg = []
            wind_bearing = []
            for hourly in forecast_data["hourly"]:
                if hourly["local_day"] == row["day_num"]:
                    precip += hourly["precip"]
                    wind_avg.append(hourly["wind_avg"])
                    wind_bearing.append(hourly["wind_direction"])
            sum_wind_avg = sum(wind_avg) / len(wind_avg)
            sum_wind_bearing = sum(wind_bearing) / len(wind_bearing) % 360

            item = {
                ATTR_FORECAST_TIME: datetime.utcfromtimestamp(row["day_start_local"]).replace(tzinfo=UTC).isoformat(),
                "conditions": row["conditions"],
                ATTR_FORECAST_CONDITION: await self.ha_condition_value(row["icon"]),
                ATTR_FORECAST_TEMP: await cnv.temperature(row["air_temp_high"]),
                ATTR_FORECAST_TEMP_LOW: await cnv.temperature(row["air_temp_low"]),
                ATTR_FORECAST_PRECIPITATION: await cnv.rain(precip),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: row["precip_probability"],
                "precip_icon": row.get("precip_icon", ""),
                "precip_type": row.get("precip_type", ""),
                ATTR_FORECAST_WIND_SPEED: await cnv.speed(sum_wind_avg, True),
                ATTR_FORECAST_WIND_BEARING: int(sum_wind_bearing),
                "wind_direction_cardinal": await cnv.direction(int(sum_wind_bearing)),
            }
            items.append(item)
        fcst_data["daily_forecast"] = items

        cnt = 0
        items = []
        for row in forecast_data[FORECAST_TYPE_HOURLY]:
            # Skip over past forecasts - seems the API sometimes returns old forecasts
            forecast_time = datetime.fromtimestamp(row["time"])
            if datetime.now() > forecast_time:
                continue

            item = {
                ATTR_FORECAST_TIME: datetime.utcfromtimestamp(row["time"]).replace(tzinfo=UTC).isoformat(),
                "conditions": row["conditions"],
                ATTR_FORECAST_CONDITION: await self.ha_condition_value(row["icon"]),
                ATTR_FORECAST_TEMP: await cnv.temperature(row["air_temperature"]),
                ATTR_FORECAST_PRESSURE: await cnv.pressure(row["sea_level_pressure"]),
                ATTR_FORECAST_HUMIDITY: row["relative_humidity"],
                ATTR_FORECAST_PRECIPITATION: await cnv.rain(row["precip"]),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: row["precip_probability"],
                "precip_icon": row.get("precip_icon", ""),
                "precip_type": row.get("precip_type", ""),
                ATTR_FORECAST_WIND_SPEED: await cnv.speed(row["wind_avg"], True),
                "wind_gust": await cnv.speed(row["wind_gust"], True),
                ATTR_FORECAST_WIND_BEARING: row["wind_direction"],
                "wind_direction_cardinal": row["wind_direction_cardinal"],
                "uv": row["uv"],
                "feels_like": await cnv.temperature(row["feels_like"]),
            }
            items.append(item)
            # Limit number of Hours
            cnt += 1
            if cnt >= FORECAST_HOURLY_HOURS:
                break
        fcst_data["hourly_forecast"] = items

        return condition_data, fcst_data

    async def ha_condition_value(self, value):
        """Returns the Home Assistant Condition."""
        return next(
            (k for k, v in CONDITION_CLASSES.items() if value in v),
            None,
        )

    async def async_request(self, method: str, endpoint: str) -> dict:
        """Make a request against the SmartWeather API."""

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(method, f"{BASE_URL}/{endpoint}") as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data
        except asyncio.TimeoutError as timeout_err:
            _LOGGER.debug("Request to endpoint timed out: %s", endpoint)
        except ClientError as err:
            if "Unauthorized" in str(err):
                _LOGGER.debug("Your API Key is invalid or does not support this operation")
            if "Not Found" in str(err):
                _LOGGER.debug("The Station ID does not exis")
        except Exception as e:
            _LOGGER.debug("Error requesting data from %s Error: ", endpoint, e)

        finally:
            if not use_running_session:
                await session.close()
