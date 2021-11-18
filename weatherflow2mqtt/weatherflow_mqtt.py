"""Program listening to the UDP Broadcast from a WeatherFlow Weather Station and publishing sensor data to MQTT."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, OrderedDict

from paho.mqtt.client import Client as MqttClient

from .__version__ import VERSION
from .aioudp import LocalEndpoint, open_local_endpoint
from .const import (
    ATTR_ATTRIBUTION,
    ATTR_BRAND,
    ATTRIBUTION,
    BRAND,
    DATABASE,
    DOMAIN,
    EVENT_AIR_DATA,
    EVENT_DEVICE_STATUS,
    EVENT_FORECAST,
    EVENT_HIGH_LOW,
    EVENT_HUB_STATUS,
    EVENT_PRECIP_START,
    EVENT_RAPID_WIND,
    EVENT_SKY_DATA,
    EVENT_STRIKE,
    EVENT_TEMPEST_DATA,
    EXTERNAL_DIRECTORY,
    FORECAST_ENTITY,
    HIGH_LOW_TIMER,
    LANGUAGE_ENGLISH,
    OBSOLETE_SENSORS,
    SENSOR_CLASS,
    SENSOR_DEVICE,
    SENSOR_EXTRA_ATT,
    SENSOR_ICON,
    SENSOR_ID,
    SENSOR_LAST_RESET,
    SENSOR_NAME,
    SENSOR_SHOW_MIN_ATT,
    SENSOR_STATE_CLASS,
    SENSOR_UNIT_I,
    SENSOR_UNIT_M,
    TEMP_CELSIUS,
    UNITS_IMPERIAL,
    UNITS_METRIC,
    WEATHERFLOW_SENSORS,
)
from .forecast import Forecast, ForecastConfig
from .helpers import ConversionFunctions, read_config, truebool
from .sqlite import SQLFunctions

_LOGGER = logging.getLogger(__name__)


@dataclass
class HostPortConfig:
    """Dataclass to define a Host/Port configuration."""

    host: str
    port: int


@dataclass
class MqttConfig(HostPortConfig):
    """Dataclass to define a MQTT configuration."""

    host: str = "127.0.0.1"
    port: int = 1883
    username: str | None = None
    password: str | None = None
    debug: bool = False


@dataclass
class WeatherFlowUdpConfig(HostPortConfig):
    """Dataclass to define a UDP configuration."""

    host: str = "0.0.0.0"
    port: int = 50222


class WeatherFlowMqtt:
    """Class to handle WeatherFlow to MQTT communication."""

    def __init__(
        self,
        is_tempest: bool = True,
        elevation: float = 0,
        unit_system: str = UNITS_METRIC,
        rapid_wind_interval: int = 0,
        language: str = LANGUAGE_ENGLISH,
        mqtt_config: MqttConfig = MqttConfig(),
        udp_config: WeatherFlowUdpConfig = WeatherFlowUdpConfig(),
        forecast_config: ForecastConfig = None,
        database_file: str = None,
    ) -> None:
        """Initialize a WeatherFlow MQTT."""
        self.is_tempest = is_tempest
        self.elevation = elevation
        self.unit_system = unit_system
        self.rapid_wind_interval = rapid_wind_interval

        self.conversions = ConversionFunctions(unit_system, language)

        self.mqtt_config = mqtt_config
        self.udp_config = udp_config

        self.forecast = (
            Forecast.from_config(config=forecast_config, conversions=self.conversions)
            if forecast_config is not None
            else None
        )

        self.mqtt_client: MqttClient = None
        self.endpoint: LocalEndpoint = None
        self._init_sql_db(database_file=database_file)

        # Set timer variables
        self.rapid_last_run = 1621229580.583215  # A time in the past
        self.forecast_last_run = 1621229580.583215  # A time in the past
        self.high_low_last_run = 1621229580.583215  # A time in the past
        self.current_day = datetime.today().weekday()
        self.last_midnight = self.conversions.utc_last_midnight()

        # Read stored Values and set variable values
        self.wind_speed = None
        self.solar_radiation = None

    def _init_sql_db(self, database_file: str = None) -> None:
        """Initialize the self.sqlite DB."""
        self.sql = SQLFunctions(self.unit_system)
        database_exist = os.path.isfile(database_file)
        self.sql.create_connection(database_file)
        if not database_exist:
            self.sql.createInitialDataset()
        # Upgrade Database if needed
        self.sql.upgradeDatabase()

        self.storage = self.sql.readStorage()

    async def connect(self) -> None:
        if self.mqtt_client is None:
            self._setup_mqtt_client()

        try:
            self.mqtt_client.connect(
                self.mqtt_config.host, port=self.mqtt_config.port, keepalive=300
            )
            _LOGGER.info(
                "Connected to the MQTT server at %s:%s",
                self.mqtt_config.host,
                self.mqtt_config.port,
            )
        except Exception as e:
            _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
            sys.exit(1)

        try:
            self.endpoint = await open_local_endpoint(
                host=self.udp_config.host, port=self.udp_config.port
            )
            _LOGGER.info(
                "The UDP server is listening on port %s", self.endpoint.address[1]
            )
        except Exception as e:
            _LOGGER.error(
                "Could not start listening to the UDP Socket. Error is: %s", e
            )
            sys.exit(1)

    def _setup_mqtt_client(self) -> MqttClient:
        """Setup the MQTT client."""
        if (
            anonymous := not self.mqtt_config.username or not self.mqtt_config.password
        ) and self.mqtt_config.debug:
            _LOGGER.debug("MQTT Credentials not needed")

        self.mqtt_client = client = MqttClient()
        client.max_inflight_messages_set(240)

        if not anonymous:
            client.username_pw_set(
                username=self.mqtt_config.username, password=self.mqtt_config.password
            )
        if self.mqtt_config.debug:
            client.enable_logger()
            _LOGGER.debug(
                "MQTT Credentials: %s - %s",
                self.mqtt_config.username,
                self.mqtt_config.password,
            )

    async def setup_sensors(
        self, filter_sensors: list[str] | None, invert_filter: bool
    ):
        """Setup the Sensors in Home Assistant."""
        # Get Hub Information
        while True:
            data, (host, port) = await self.endpoint.receive()
            json_response = json.loads(data.decode("utf-8"))
            msg_type = json_response.get("type")
            if msg_type == EVENT_HUB_STATUS:
                serial_number = json_response.get("serial_number")
                firmware = json_response.get("firmware_revision")
                break

        # Create the config for the Sensors
        units = SENSOR_UNIT_I if self.unit_system == UNITS_IMPERIAL else SENSOR_UNIT_M
        for sensor in WEATHERFLOW_SENSORS:
            sensor_name = sensor[SENSOR_NAME]
            # Don't add the Weather Sensor if forecast disabled
            if self.forecast is None and sensor[SENSOR_DEVICE] == EVENT_FORECAST:
                _LOGGER.debug(
                    "Skipping Forecast sensor %s",
                    sensor[SENSOR_DEVICE],
                )
                continue
            # Don't add the AIR & SKY Unit Battery and device sensors if this is a Tempest Device
            if self.is_tempest and (
                sensor[SENSOR_ID] == "battery_air"
                or sensor[SENSOR_ID] == "battery_level_air"
                or sensor[SENSOR_ID] == "battery_level_sky"
                or sensor[SENSOR_ID] == "air_status"
                or sensor[SENSOR_ID] == "sky_status"
            ):
                continue
            # Don't add the TEMPEST Battery sensor and Battery Mode if this is a AIR or SKY Device
            if not self.is_tempest and (
                sensor[SENSOR_ID] == "battery_level_tempest"
                or sensor[SENSOR_ID] == "battery_mode"
                or sensor[SENSOR_ID] == "tempest_status"
            ):
                continue
            # Modify name of Battery Device if Tempest Unit
            if self.is_tempest and sensor[SENSOR_ID] == "battery":
                sensor_name = "Voltage TEMPEST"

            state_topic = "homeassistant/sensor/{}/{}/state".format(
                DOMAIN, sensor[SENSOR_DEVICE]
            )
            attr_topic = "homeassistant/sensor/{}/{}/attributes".format(
                DOMAIN, sensor[SENSOR_ID]
            )
            discovery_topic = "homeassistant/sensor/{}/{}/config".format(
                DOMAIN, sensor[SENSOR_ID]
            )
            last_reset_topic = "homeassistant/sensor/{}/{}/last_reset_topic".format(
                DOMAIN, sensor[SENSOR_ID]
            )
            highlow_topic = "homeassistant/sensor/{}/{}/attributes".format(
                DOMAIN, EVENT_HIGH_LOW
            )

            attribution = OrderedDict()
            payload = OrderedDict()

            if filter_sensors is None or (
                (sensor[SENSOR_ID] in filter_sensors) is not invert_filter
            ):
                _LOGGER.info("SETTING UP %s SENSOR", sensor_name)

                # Payload
                payload["name"] = "{}".format(f"WF {sensor_name}")
                payload["unique_id"] = "{}-{}".format(serial_number, sensor[SENSOR_ID])
                if sensor[units] is not None:
                    payload["unit_of_measurement"] = sensor[units]
                if sensor[SENSOR_CLASS] is not None:
                    payload["device_class"] = sensor[SENSOR_CLASS]
                if sensor[SENSOR_STATE_CLASS] is not None:
                    payload["state_class"] = sensor[SENSOR_STATE_CLASS]
                if sensor[SENSOR_ICON] is not None:
                    payload["icon"] = f"mdi:{sensor[SENSOR_ICON]}"
                payload["state_topic"] = state_topic
                payload["value_template"] = "{{{{ value_json.{} }}}}".format(
                    sensor[SENSOR_ID]
                )
                payload["json_attributes_topic"] = attr_topic
                # if sensor[SENSOR_LAST_RESET]:
                #     payload["last_reset_topic"] = state_topic
                #     payload["last_reset_value_template"] = "{{ value_json.last_reset_midnight }}"
                payload["device"] = {
                    "identifiers": ["WeatherFlow_{}".format(serial_number)],
                    "connections": [["mac", serial_number]],
                    "manufacturer": "WeatherFlow",
                    "name": "WeatherFlow2MQTT",
                    "model": f"WeatherFlow Weather Station V{VERSION}",
                    "sw_version": firmware,
                }

                # Attributes
                attribution[ATTR_ATTRIBUTION] = ATTRIBUTION
                attribution[ATTR_BRAND] = BRAND
                # Add additional attributes to some sensors
                if sensor[SENSOR_ID] == "pressure_trend":
                    payload["json_attributes_topic"] = state_topic
                    template = OrderedDict()
                    template = attribution
                    template["trend_value"] = "{{ value_json.pressure_trend_value }}"
                    payload["json_attributes_template"] = json.dumps(template)
                if sensor[SENSOR_ID] == "battery_mode":
                    payload["json_attributes_topic"] = state_topic
                    template = OrderedDict()
                    template = attribution
                    template["description"] = "{{ value_json.battery_desc }}"
                    payload["json_attributes_template"] = json.dumps(template)
                if sensor[SENSOR_ID] == "beaufort":
                    payload["json_attributes_topic"] = state_topic
                    template = OrderedDict()
                    template = attribution
                    template["description"] = "{{ value_json.beaufort_text }}"
                    payload["json_attributes_template"] = json.dumps(template)
                if sensor[SENSOR_EXTRA_ATT]:
                    payload["json_attributes_topic"] = highlow_topic
                    template = OrderedDict()
                    template = attribution
                    template["max_day"] = "{{{{ value_json.{}['max_day'] }}}}".format(
                        sensor[SENSOR_ID]
                    )
                    template[
                        "max_day_time"
                    ] = "{{{{ value_json.{}['max_day_time'] }}}}".format(
                        sensor[SENSOR_ID]
                    )
                    template[
                        "max_month"
                    ] = "{{{{ value_json.{}['max_month'] }}}}".format(sensor[SENSOR_ID])
                    template[
                        "max_month_time"
                    ] = "{{{{ value_json.{}['max_month_time'] }}}}".format(
                        sensor[SENSOR_ID]
                    )
                    template["max_all"] = "{{{{ value_json.{}['max_all'] }}}}".format(
                        sensor[SENSOR_ID]
                    )
                    template[
                        "max_all_time"
                    ] = "{{{{ value_json.{}['max_all_time'] }}}}".format(
                        sensor[SENSOR_ID]
                    )
                    if sensor[SENSOR_SHOW_MIN_ATT]:
                        template[
                            "min_day"
                        ] = "{{{{ value_json.{}['min_day'] }}}}".format(
                            sensor[SENSOR_ID]
                        )
                        template[
                            "min_day_time"
                        ] = "{{{{ value_json.{}['min_day_time'] }}}}".format(
                            sensor[SENSOR_ID]
                        )
                        template[
                            "min_month"
                        ] = "{{{{ value_json.{}['min_month'] }}}}".format(
                            sensor[SENSOR_ID]
                        )
                        template[
                            "min_month_time"
                        ] = "{{{{ value_json.{}['min_month_time'] }}}}".format(
                            sensor[SENSOR_ID]
                        )
                        template[
                            "min_all"
                        ] = "{{{{ value_json.{}['min_all'] }}}}".format(
                            sensor[SENSOR_ID]
                        )
                        template[
                            "min_all_time"
                        ] = "{{{{ value_json.{}['min_all_time'] }}}}".format(
                            sensor[SENSOR_ID]
                        )
                    payload["json_attributes_template"] = json.dumps(template)

            try:
                await self.publish_mqtt(
                    discovery_topic, json.dumps(payload), qos=1, retain=True
                )
                await self.publish_mqtt(
                    attr_topic, json.dumps(attribution), qos=1, retain=True
                )
            except Exception as e:
                _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
                break

        # cleanup obsolete sensors
        for sensor in OBSOLETE_SENSORS:
            try:
                await self.publish_mqtt(
                    topic=f"homeassistant/sensor/{DOMAIN}/{sensor}/config"
                )
            except Exception as e:
                _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
                break

    async def listen(self) -> None:
        data, (host, port) = await self.endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")

        # Run New day function if Midnight
        if self.current_day != datetime.today().weekday():
            self.storage["rain_yesterday"] = self.storage["rain_today"]
            self.storage["rain_duration_yesterday"] = self.storage[
                "rain_duration_today"
            ]
            self.storage["rain_today"] = 0
            self.storage["rain_duration_today"] = 0
            self.storage["lightning_count_today"] = 0
            self.last_midnight = self.conversions.utc_last_midnight()
            self.sql.writeStorage(self.storage)
            self.sql.dailyHousekeeping()
            self.current_day = datetime.today().weekday()

        # Update High and Low values if it is time
        now = datetime.now().timestamp()
        if (now - self.high_low_last_run) >= HIGH_LOW_TIMER:
            highlow_topic = "homeassistant/sensor/{}/{}/attributes".format(
                DOMAIN, EVENT_HIGH_LOW
            )
            high_low_data = self.sql.readHighLow()
            await self.publish_mqtt(
                highlow_topic, json.dumps(high_low_data), qos=1, retain=True
            )
            self.high_low_last_run = datetime.now().timestamp()

        # Update the Forecast if it is time and enabled
        if (
            self.forecast is not None
            and ((now := datetime.now().timestamp()) - self.forecast_last_run)
            >= self.forecast.interval * 60
        ):
            fcst_state_topic = "homeassistant/sensor/{}/{}/state".format(
                DOMAIN, FORECAST_ENTITY
            )
            fcst_attr_topic = "homeassistant/sensor/{}/{}/attributes".format(
                DOMAIN, FORECAST_ENTITY
            )
            condition_data, fcst_data = await self.forecast.update_forecast()
            if condition_data is not None:
                await self.publish_mqtt(fcst_state_topic, json.dumps(condition_data))
                await self.publish_mqtt(fcst_attr_topic, json.dumps(fcst_data))
            self.forecast_last_run = now

        # Process the data
        if msg_type is not None:
            data = OrderedDict()
            state_topic = "homeassistant/sensor/{}/{}/state".format(DOMAIN, msg_type)
            if msg_type in EVENT_RAPID_WIND:
                now = datetime.now().timestamp()
                if (now - self.rapid_last_run) >= self.rapid_wind_interval:
                    obs = json_response["ob"]
                    data["wind_speed"] = self.conversions.speed(obs[1])
                    data["wind_bearing"] = obs[2]
                    data["wind_direction"] = self.conversions.direction(obs[2])
                    self.wind_speed = obs[1]
                    await self.publish_mqtt(state_topic, json.dumps(data), retain=False)
                    self.rapid_last_run = datetime.now().timestamp()
            elif msg_type in EVENT_HUB_STATUS:
                data["hub_status"] = self.conversions.humanize_time(
                    json_response.get("uptime")
                )
                await self.publish_mqtt(state_topic, json.dumps(data), retain=False)
                attr_topic = "homeassistant/sensor/{}/{}/attributes".format(
                    DOMAIN, "hub_status"
                )
                attr = OrderedDict()
                attr[ATTR_ATTRIBUTION] = ATTRIBUTION
                attr[ATTR_BRAND] = BRAND
                attr["serial_number"] = json_response.get("serial_number")
                attr["firmware_revision"] = json_response.get("firmware_revision")
                attr["rssi"] = json_response.get("rssi")
                attr["reset_flags"] = json_response.get("reset_flags")
                await self.publish_mqtt(attr_topic, json.dumps(attr), retain=False)
                await asyncio.sleep(0.01)

                # if show_debug:
                _LOGGER.debug("HUB Reset Flags: %s", json_response.get("reset_flags"))
            elif msg_type in EVENT_PRECIP_START:
                obs = json_response["evt"]
                self.storage["rain_start"] = obs[0]
                self.sql.writeStorage(self.storage)
            elif msg_type in EVENT_STRIKE:
                obs = json_response["evt"]
                self.sql.writeLightning()
                self.storage["lightning_count_today"] += 1
                self.storage["last_lightning_distance"] = self.conversions.distance(
                    obs[1]
                )
                self.storage["last_lightning_energy"] = obs[2]
                self.storage["last_lightning_time"] = time.time()
                self.sql.writeStorage(self.storage)
            elif msg_type in EVENT_AIR_DATA:
                obs = json_response["obs"][0]
                data["station_pressure"] = self.conversions.pressure(obs[1])
                data["air_temperature"] = self.conversions.temperature(obs[2])
                data["relative_humidity"] = obs[3]
                data["lightning_strike_count"] = obs[4]
                data["lightning_strike_count_1hr"] = self.sql.readLightningCount(1)
                data["lightning_strike_count_3hr"] = self.sql.readLightningCount(3)
                data["lightning_strike_count_today"] = self.storage[
                    "lightning_count_today"
                ]
                data["lightning_strike_distance"] = self.storage[
                    "last_lightning_distance"
                ]
                data["lightning_strike_energy"] = self.storage["last_lightning_energy"]
                data["lightning_strike_time"] = datetime.fromtimestamp(
                    self.storage["last_lightning_time"]
                ).isoformat()
                data["battery_air"] = round(obs[6], 2)
                data["battery_level_air"] = self.conversions.battery_level(
                    obs[6], False
                )
                data["sealevel_pressure"] = self.conversions.sea_level_pressure(
                    obs[1], self.elevation
                )
                trend_text, trend_value = self.sql.readPressureTrend(
                    data["sealevel_pressure"], self.translations
                )
                data["pressure_trend"] = trend_text
                data["pressure_trend_value"] = trend_value
                data["air_density"] = self.conversions.air_density(obs[2], obs[1])
                data["dewpoint"] = self.conversions.dewpoint(obs[2], obs[3])
                data["feelslike"] = self.conversions.feels_like(
                    obs[2], obs[3], self.wind_speed
                )
                data["wetbulb"] = self.conversions.wetbulb(obs[2], obs[3], obs[1])
                data["delta_t"] = self.conversions.delta_t(obs[2], obs[3], obs[1])
                data["dewpoint_description"] = self.conversions.dewpoint_level(
                    data["dewpoint"]
                )
                data["temperature_description"] = self.conversions.temperature_level(
                    obs[2]
                )
                data["visibility"] = self.conversions.visibility(
                    self.elevation, obs[2], obs[3]
                )
                data["absolute_humidity"] = self.conversions.absolute_humidity(
                    obs[2], obs[3]
                )
                data["wbgt"] = self.conversions.wbgt(
                    obs[2], obs[3], obs[1], self.solar_radiation
                )
                data["last_reset_midnight"] = self.last_midnight
                await self.publish_mqtt(state_topic, json.dumps(data), retain=False)
                self.sql.writePressure(data["sealevel_pressure"])
                self.sql.updateHighLow(data)
                # self.sql.updateDayData(data)
                await asyncio.sleep(0.01)
            elif msg_type in EVENT_SKY_DATA:
                obs = json_response["obs"][0]
                data["illuminance"] = obs[1]
                data["uv"] = obs[2]
                self.storage["rain_today"] += obs[3]
                data["rain_today"] = self.conversions.rain(self.storage["rain_today"])
                data["rain_yesterday"] = self.conversions.rain(
                    self.storage["rain_yesterday"]
                )
                data["rain_duration_today"] = self.storage["rain_duration_today"]
                data["rain_duration_yesterday"] = self.storage[
                    "rain_duration_yesterday"
                ]
                data["rain_start_time"] = datetime.fromtimestamp(
                    self.storage["rain_start"]
                ).isoformat()
                data["wind_lull"] = self.conversions.speed(obs[4])
                data["wind_speed_avg"] = self.conversions.speed(obs[5])
                data["wind_gust"] = self.conversions.speed(obs[6])
                data["wind_bearing_avg"] = obs[7]
                data["wind_direction_avg"] = self.conversions.direction(obs[7])
                data["battery"] = round(obs[8], 2)
                data["battery_level_sky"] = self.conversions.battery_level(
                    obs[8], False
                )
                self.solar_radiation = obs[10]
                data["solar_radiation"] = obs[10]
                data["precipitation_type"] = self.conversions.rain_type(obs[12])
                data["rain_rate"] = self.conversions.rain_rate(obs[3])
                data["uv_description"] = self.conversions.uv_level(obs[2])
                bft_value, bft_text = self.conversions.beaufort(obs[5])
                data["beaufort"] = bft_value
                data["beaufort_text"] = bft_text
                data["last_reset_midnight"] = self.last_midnight
                await self.publish_mqtt(state_topic, json.dumps(data), retain=False)
                self.sql.updateHighLow(data)
                # self.sql.updateDayData(data)
                await asyncio.sleep(0.01)
                if obs[3] > 0:
                    self.storage["rain_duration_today"] += 1
                    self.sql.writeStorage(self.storage)
            elif msg_type in EVENT_TEMPEST_DATA:
                obs = json_response["obs"][0]

                state_topic = "homeassistant/sensor/{}/{}/state".format(
                    DOMAIN, EVENT_SKY_DATA
                )
                data["wind_lull"] = self.conversions.speed(obs[1])
                data["wind_speed_avg"] = self.conversions.speed(obs[2])
                data["wind_gust"] = self.conversions.speed(obs[3])
                data["wind_bearing_avg"] = obs[4]
                data["wind_direction_avg"] = self.conversions.direction(obs[4])
                data["illuminance"] = obs[9]
                data["uv"] = obs[10]
                data["solar_radiation"] = obs[11]
                self.storage["rain_today"] += obs[12]
                data["rain_today"] = self.conversions.rain(self.storage["rain_today"])
                data["rain_yesterday"] = self.conversions.rain(
                    self.storage["rain_yesterday"]
                )
                data["rain_duration_today"] = self.storage["rain_duration_today"]
                data["rain_duration_yesterday"] = self.storage[
                    "rain_duration_yesterday"
                ]
                data["rain_start_time"] = datetime.fromtimestamp(
                    self.storage["rain_start"]
                ).isoformat()
                data["precipitation_type"] = self.conversions.rain_type(obs[13])
                data["battery"] = round(obs[16], 2)
                data["battery_level_tempest"] = self.conversions.battery_level(
                    obs[16], True
                )
                bat_mode, bat_desc = self.conversions.battery_mode(obs[16], obs[11])
                data["battery_mode"] = bat_mode
                data["battery_desc"] = bat_desc
                data["rain_rate"] = self.conversions.rain_rate(obs[12])
                data["rain_intensity"] = self.conversions.rain_intensity(
                    data["rain_rate"]
                )
                data["uv_description"] = self.conversions.uv_level(obs[10])
                bft_value, bft_text = self.conversions.beaufort(obs[2])
                data["beaufort"] = bft_value
                data["beaufort_text"] = bft_text
                data["last_reset_midnight"] = self.last_midnight
                await self.publish_mqtt(state_topic, json.dumps(data))
                self.sql.updateHighLow(data)
                # self.sql.updateDayData(data)
                await asyncio.sleep(0.01)

                state_topic = "homeassistant/sensor/{}/{}/state".format(
                    DOMAIN, EVENT_AIR_DATA
                )
                data = OrderedDict()
                data["station_pressure"] = self.conversions.pressure(obs[6])
                data["air_temperature"] = self.conversions.temperature(obs[7])
                data["relative_humidity"] = obs[8]
                data["lightning_strike_count"] = obs[15]
                data["lightning_strike_count_1hr"] = self.sql.readLightningCount(1)
                data["lightning_strike_count_3hr"] = self.sql.readLightningCount(3)
                data["lightning_strike_count_today"] = self.storage[
                    "lightning_count_today"
                ]
                data["lightning_strike_distance"] = self.storage[
                    "last_lightning_distance"
                ]
                data["lightning_strike_energy"] = self.storage["last_lightning_energy"]
                data["lightning_strike_time"] = datetime.fromtimestamp(
                    self.storage["last_lightning_time"]
                ).isoformat()
                data["sealevel_pressure"] = self.conversions.sea_level_pressure(
                    obs[6], self.elevation
                )
                trend_text, trend_value = self.sql.readPressureTrend(
                    data["sealevel_pressure"], self.conversions.translations
                )
                data["pressure_trend"] = trend_text
                data["pressure_trend_value"] = trend_value
                data["air_density"] = self.conversions.air_density(obs[7], obs[6])
                data["dewpoint"] = self.conversions.dewpoint(obs[7], obs[8])
                data["feelslike"] = self.conversions.feels_like(
                    obs[7], obs[8], self.wind_speed
                )
                data["wetbulb"] = self.conversions.wetbulb(obs[7], obs[8], obs[6])
                data["delta_t"] = self.conversions.delta_t(obs[7], obs[8], obs[6])
                data["visibility"] = self.conversions.visibility(
                    self.elevation, obs[7], obs[8]
                )
                data["absolute_humidity"] = self.conversions.absolute_humidity(
                    obs[7], obs[8]
                )
                data["wbgt"] = self.conversions.wbgt(obs[7], obs[8], obs[6], obs[11])
                data["dewpoint_description"] = self.conversions.dewpoint_level(
                    data["dewpoint"]
                )
                data["temperature_description"] = self.conversions.temperature_level(
                    obs[7]
                )
                data["last_reset_midnight"] = self.last_midnight
                await self.publish_mqtt(state_topic, json.dumps(data))
                self.sql.writePressure(data["sealevel_pressure"])
                self.sql.updateHighLow(data)
                # self.sql.updateDayData(data)
                await asyncio.sleep(0.01)

                if obs[12] > 0:
                    self.storage["rain_duration_today"] += 1
                    self.sql.writeStorage(self.storage)
            elif msg_type in EVENT_DEVICE_STATUS:
                now = datetime.now()
                serial_number = json_response.get("serial_number")
                firmware_revision = json_response.get("firmware_revision")
                voltage = json_response.get("voltage")
                uptime = self.conversions.humanize_time(json_response.get("uptime"))
                sensor_status = json_response.get("sensor_status")

                device_status = None
                if sensor_status is not None and sensor_status != 0:
                    device_status = self.conversions.device_status(sensor_status)
                    if device_status:  # and show_debug:
                        _LOGGER.debug(
                            "Device %s has reported a sensor fault. Reason: %s",
                            serial_number,
                            device_status,
                        )

                data = OrderedDict()
                if (prefix := serial_number[0:2]) == "ST":
                    device_name = "tempest_status"
                elif prefix == "AR":
                    device_name = "air_status"
                elif prefix == "SK":
                    device_name = "sky_status"

                data[device_name] = uptime
                attr_topic = "homeassistant/sensor/{}/{}/attributes".format(
                    DOMAIN, device_name
                )
                attr = OrderedDict()
                attr[ATTR_ATTRIBUTION] = ATTRIBUTION
                attr[ATTR_BRAND] = BRAND
                attr["serial_number"] = serial_number
                attr["firmware_revision"] = firmware_revision
                attr["voltage"] = voltage
                attr["rssi"] = json_response.get("rssi")
                attr["sensor_status"] = device_status
                await self.publish_mqtt(attr_topic, json.dumps(attr))

                await self.publish_mqtt(state_topic, json.dumps(data))

                # if show_debug:
                _LOGGER.debug(
                    "DEVICE STATUS TRIGGERED AT %s\n  -- Device: %s\n -- Firmware Revision: %s\n -- Voltage: %s",
                    str(now),
                    serial_number,
                    firmware_revision,
                    voltage,
                )
            else:
                _LOGGER.debug(
                    "Received unknown message: %s - %s", msg_type, json_response
                )

            # if show_debug:
            _LOGGER.debug(
                "Event type %s has been processed, with payload: %s",
                msg_type,
                json.dumps(data),
            )

    async def publish_mqtt(self, topic, payload=None, qos=0, retain=False) -> None:
        """Publish a MQTT topic with payload."""
        self.mqtt_client.publish(topic, payload, qos=qos, retain=retain)
        await asyncio.sleep(0.01)


async def main():
    logging.basicConfig(level=logging.INFO)

    if is_supervisor := truebool(os.getenv("HA_SUPERVISOR")):
        config = await get_supervisor_configuration()
    else:
        config = os.environ

    _LOGGER.info("Timezone is %s", os.environ.get("TZ"))

    # Read the config Settings
    is_tempest = truebool(config.get("TEMPEST_DEVICE", True))
    elevation = float(config.get("ELEVATION", 0))
    unit_system = config.get("UNIT_SYSTEM", UNITS_METRIC)
    rw_interval = int(config.get("RAPID_WIND_INTERVAL", 0))
    language = config.get("LANGUAGE", LANGUAGE_ENGLISH).lower()

    mqtt_config = MqttConfig(
        host=config.get("MQTT_HOST", "127.0.0.1"),
        port=int(config.get("MQTT_PORT", 1883)),
        username=config.get("MQTT_USERNAME"),
        password=config.get("MQTT_PASSWORD"),
        debug=truebool(config.get("MQTT_DEBUG")),
    )

    udp_config = WeatherFlowUdpConfig(
        host=config.get("WF_HOST", "0.0.0.0"), port=int(config.get("WF_PORT", 50222))
    )

    forecast_config = (
        ForecastConfig(
            station_id=station_id,
            token=station_token,
            interval=int(config.get("FORECAST_INTERVAL", 30)),
        )
        if (
            (station_id := config.get("STATION_ID"))
            and (station_token := config.get("STATION_TOKEN"))
        )
        else None
    )

    if show_debug := truebool(config.get("DEBUG")):
        logging.getLogger().setLevel(logging.DEBUG)

    if isinstance(filter_sensors := config.get("FILTER_SENSORS"), str):
        filter_sensors = [sensor.strip() for sensor in filter_sensors.split(",")]
    invert_filter = truebool(config.get("INVERT_FILTER"))

    # Read the sensor config
    if filter_sensors is None and not is_supervisor:
        filter_sensors = read_config()

    weatherflowmqtt = WeatherFlowMqtt(
        is_tempest=is_tempest,
        elevation=elevation,
        unit_system=unit_system,
        rapid_wind_interval=rw_interval,
        language=language,
        mqtt_config=mqtt_config,
        udp_config=udp_config,
        forecast_config=forecast_config,
        database_file=DATABASE,
    )
    await weatherflowmqtt.connect()

    # Configure Sensors in MQTT
    _LOGGER.info("Defining Sensors for Home Assistant")
    await weatherflowmqtt.setup_sensors(filter_sensors, invert_filter)

    # Watch for message from the UDP socket
    while True:
        await weatherflowmqtt.listen()


async def get_supervisor_configuration() -> dict[str, Any]:
    """Get the configuration from Home Assistant Supervisor."""
    from aiohttp import ClientSession

    _LOGGER.info("🏠 Home Assistant Supervisor Mode 🏠")

    config: dict[str, Any] = {}

    supervisor_url = "http://supervisor"
    headers = {"Authorization": "Bearer " + os.getenv("SUPERVISOR_TOKEN")}

    async with ClientSession() as session:
        try:
            async with session.get(
                supervisor_url + "/core/api/config",
                headers=headers,
            ) as resp:
                if (data := await resp.json()) is not None:
                    config.update(
                        {
                            "ELEVATION": data.get("elevation"),
                            "UNIT_SYSTEM": UNITS_METRIC
                            if data.get("unit_system", {}).get("temperature")
                            == TEMP_CELSIUS
                            else UNITS_IMPERIAL,
                        }
                    )
        except Exception as e:
            _LOGGER.error("Could not read Home Assistant core config: %s", e)

        try:
            async with session.get(
                supervisor_url + "/services/mqtt",
                headers=headers,
            ) as resp:
                resp_json = await resp.json()
                if "ok" in resp_json.get("result"):
                    data = resp_json["data"]
                    config.update(
                        {
                            "MQTT_HOST": data["host"],
                            "MQTT_PORT": data["port"],
                            "MQTT_USERNAME": data["username"],
                            "MQTT_PASSWORD": data["password"],
                        }
                    )
        except Exception as e:
            _LOGGER.error("Could not read Home Assistant MQTT config: %s", e)

    if os.path.exists(options_file := f"{EXTERNAL_DIRECTORY}/options.json"):
        with open(options_file, "r") as f:
            config.update(json.load(f))

    return config


# Main Program starts
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Program")
