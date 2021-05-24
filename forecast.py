"""Module to get forecast using REST from WeatherFlow."""
import asyncio
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError
from datetime import datetime
from typing import Optional, OrderedDict

import logging

from const import (
    BASE_URL,
    CONDITION_CLASSES,
    DEFAULT_TIMEOUT,
    FORECAST_HOURLY_HOURS,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
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
        condition_state = next(
            (k for k, v in CONDITION_CLASSES.items() if current_icon in v),
            None,
        )
        condition_data["weather"] = condition_state

        forecast_data = json_data.get("forecast")

        # We also need Day hign and low Temp from Today
        temp_high_today = forecast_data[FORECAST_TYPE_DAILY][0]["air_temp_high"]
        temp_low_today = forecast_data[FORECAST_TYPE_DAILY][0]["air_temp_low"]

        # Process Daily Forecast
        fcst_data = OrderedDict()
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
            sum_wind_bearing = sum(wind_bearing) / len(wind_bearing)

            item = {
                "timestamp": forecast_time.isoformat(),
                "epochtime": row["day_start_local"],
                "conditions": row["conditions"],
                "icon": row["icon"],
                "sunrise": datetime.fromtimestamp(row["sunrise"]).isoformat(),
                "sunset": datetime.fromtimestamp(row["sunset"]).isoformat(),
                "air_temp_high": row["air_temp_high"],
                "air_temp_low": row["air_temp_low"],
                "precip": await cnv.rain(precip),
                "precip_probability": row["precip_probability"],
                "precip_icon": row.get("precip_icon", ""),
                "precip_type": row.get("precip_type", ""),
                "wind_avg": await cnv.speed(sum_wind_avg),
                "wind_bearing": sum_wind_bearing,
                "current_condition": current_condition,
                "current_icon": current_icon,
                "temp_high_today": temp_high_today,
                "temp_low_today": temp_low_today,
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
                "timestamp": datetime.fromtimestamp(row["time"]).isoformat(),
                "epochtime": row["time"],
                "conditions": row["conditions"],
                "icon": row["icon"],
                "air_temperature": row["air_temperature"],
                "sea_level_pressure": await cnv.pressure(row["sea_level_pressure"]),
                "relative_humidity": row["relative_humidity"],
                "precip": await cnv.rain(row["precip"]),
                "precip_probability": row["precip_probability"],
                "precip_icon": row.get("precip_icon", ""),
                "precip_type": row.get("precip_type", ""),
                "wind_avg": await cnv.speed(row["wind_avg"]),
                "wind_gust": await cnv.speed(row["wind_gust"]),
                "wind_direction": row["wind_direction"],
                "wind_direction_cardinal": row["wind_direction_cardinal"],
                "uv": row["uv"],
                "feels_like": row["feels_like"],
                "current_condition": current_condition,
                "current_icon": current_icon,
                "temp_high_today": temp_high_today,
                "temp_low_today": temp_low_today,
            }
            items.append(item)
            # Limit number of Hours
            cnt += 1
            if cnt >= FORECAST_HOURLY_HOURS:
                break
        fcst_data["hourly_forecast"] = items

        return condition_data, fcst_data

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
