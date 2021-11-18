"""Module to get forecast using REST from WeatherFlow."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, OrderedDict

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .const import (
    ATTR_ATTRIBUTION,
    ATTR_BRAND,
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
    ATTRIBUTION,
    BASE_URL,
    BRAND,
    CONDITION_CLASSES,
    DEFAULT_TIMEOUT,
    FORECAST_HOURLY_HOURS,
    FORECAST_TYPE_DAILY,
    FORECAST_TYPE_HOURLY,
    LANGUAGE_ENGLISH,
    UNITS_METRIC,
    UTC,
)
from .helpers import ConversionFunctions

_LOGGER = logging.getLogger(__name__)


@dataclass
class ForecastConfig:
    """Forecast config."""

    station_id: str
    token: str
    interval: int = 30


class Forecast:
    """Forecast."""

    def __init__(
        self,
        station_id: str,
        token: str,
        interval: int = 30,
        conversions: ConversionFunctions = ConversionFunctions(
            unit_system=UNITS_METRIC, language=LANGUAGE_ENGLISH
        ),
        session: ClientSession | None = None,
    ):
        """Initialize a Forecast object."""
        self.station_id = station_id
        self.token = token
        self.interval = interval
        self.conversions = conversions
        self._session: ClientSession = session

    @classmethod
    def from_config(
        cls,
        config: ForecastConfig,
        conversions: ConversionFunctions = ConversionFunctions(
            unit_system=UNITS_METRIC, language=LANGUAGE_ENGLISH
        ),
        session: ClientSession | None = None,
    ) -> Forecast:
        """Create a Forecast from a Forecast Config."""
        return cls(
            station_id=config.station_id,
            token=config.token,
            interval=config.interval,
            conversions=conversions,
            session=session,
        )

    async def update_forecast(self):
        """Return the formatted forecast data."""
        json_data = await self.async_request(
            method="get",
            endpoint=f"better_forecast?station_id={self.station_id}&token={self.token}",
        )
        items = []

        if json_data is not None:
            # We need a few Items from the Current Conditions section
            current_cond = json_data.get("current_conditions")
            current_icon = current_cond["icon"]
            today = datetime.date(datetime.now())

            # Prepare for MQTT
            condition_data = OrderedDict()
            condition_state = self.ha_condition_value(current_icon)
            condition_data["weather"] = condition_state

            forecast_data = json_data.get("forecast")

            # We also need Day hign and low Temp from Today
            temp_high_today = self.conversions.temperature(
                forecast_data[FORECAST_TYPE_DAILY][0]["air_temp_high"]
            )
            temp_low_today = self.conversions.temperature(
                forecast_data[FORECAST_TYPE_DAILY][0]["air_temp_low"]
            )

            # Process Daily Forecast
            fcst_data = OrderedDict()
            fcst_data[ATTR_ATTRIBUTION] = ATTRIBUTION
            fcst_data[ATTR_BRAND] = BRAND
            fcst_data["temp_high_today"] = temp_high_today
            fcst_data["temp_low_today"] = temp_low_today

            for row in forecast_data[FORECAST_TYPE_DAILY]:
                # Skip over past forecasts - seems the API sometimes returns old forecasts
                forecast_time = datetime.date(
                    datetime.fromtimestamp(row["day_start_local"])
                )
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
                    ATTR_FORECAST_TIME: datetime.utcfromtimestamp(
                        row["day_start_local"]
                    )
                    .replace(tzinfo=UTC)
                    .isoformat(),
                    "conditions": row["conditions"],
                    ATTR_FORECAST_CONDITION: self.ha_condition_value(row["icon"]),
                    ATTR_FORECAST_TEMP: self.conversions.temperature(
                        row["air_temp_high"]
                    ),
                    ATTR_FORECAST_TEMP_LOW: self.conversions.temperature(
                        row["air_temp_low"]
                    ),
                    ATTR_FORECAST_PRECIPITATION: self.conversions.rain(precip),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY: row["precip_probability"],
                    "precip_icon": row.get("precip_icon", ""),
                    "precip_type": row.get("precip_type", ""),
                    ATTR_FORECAST_WIND_SPEED: self.conversions.speed(
                        sum_wind_avg, True
                    ),
                    ATTR_FORECAST_WIND_BEARING: int(sum_wind_bearing),
                    "wind_direction_cardinal": self.conversions.direction(
                        int(sum_wind_bearing)
                    ),
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
                    ATTR_FORECAST_TIME: datetime.utcfromtimestamp(row["time"])
                    .replace(tzinfo=UTC)
                    .isoformat(),
                    "conditions": row["conditions"],
                    ATTR_FORECAST_CONDITION: self.ha_condition_value(row.get("icon")),
                    ATTR_FORECAST_TEMP: self.conversions.temperature(
                        row["air_temperature"]
                    ),
                    ATTR_FORECAST_PRESSURE: self.conversions.pressure(
                        row["sea_level_pressure"]
                    ),
                    ATTR_FORECAST_HUMIDITY: row["relative_humidity"],
                    ATTR_FORECAST_PRECIPITATION: self.conversions.rain(row["precip"]),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY: row["precip_probability"],
                    "precip_icon": row.get("precip_icon", ""),
                    "precip_type": row.get("precip_type", ""),
                    ATTR_FORECAST_WIND_SPEED: self.conversions.speed(
                        row["wind_avg"], True
                    ),
                    "wind_gust": self.conversions.speed(row["wind_gust"], True),
                    ATTR_FORECAST_WIND_BEARING: row["wind_direction"],
                    "wind_direction_cardinal": self.conversions.translations[
                        "wind_dir"
                    ][row["wind_direction_cardinal"]],
                    "uv": row["uv"],
                    "feels_like": self.conversions.temperature(row["feels_like"]),
                }
                items.append(item)
                # Limit number of Hours
                cnt += 1
                if cnt >= FORECAST_HOURLY_HOURS:
                    break
            fcst_data["hourly_forecast"] = items

            return condition_data, fcst_data

        # Return None if we could not retrieve data
        _LOGGER.warning("Forecast Server was unresponsive. Skipping forecast update")
        return None, None

    async def async_request(self, method: str, endpoint: str) -> dict[str, Any]:
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
                _LOGGER.error(
                    "Your API Key is invalid or does not support this operation"
                )
            if "Not Found" in str(err):
                _LOGGER.error("The Station ID does not exist")
        except Exception as e:
            _LOGGER.debug("Error requesting data from %s Error: ", endpoint, e)

        finally:
            if not use_running_session:
                await session.close()

    def ha_condition_value(self, value: str) -> str | None:
        """Returns the Home Assistant Condition."""
        try:
            return next(
                (k for k, v in CONDITION_CLASSES.items() if value in v),
                None,
            )
        except Exception as e:
            _LOGGER.debug(
                "Could not find icon with value: %s. Error message: %s", value, e
            )
            return None
