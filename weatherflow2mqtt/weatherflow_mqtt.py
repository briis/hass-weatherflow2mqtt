"""Program listening to the UDP Broadcast.

from a WeatherFlow Weather Station and publishing sensor data to MQTT.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, OrderedDict

from paho.mqtt.client import Client as MqttClient
from pint.quantity import Quantity
from pyweatherflowudp.client import EVENT_DEVICE_DISCOVERED, WeatherFlowListener
from pyweatherflowudp.device import (
    EVENT_LOAD_COMPLETE,
    EVENT_OBSERVATION,
    EVENT_RAIN_START,
    EVENT_RAPID_WIND,
    EVENT_STATUS_UPDATE,
    EVENT_STRIKE,
    AirSensorType,
    HubDevice,
    SkySensorType,
    TempestDevice,
    WeatherFlowDevice,
    WeatherFlowSensorDevice,
)
from pyweatherflowudp.event import (
    CustomEvent,
    LightningStrikeEvent,
    RainStartEvent,
    WindEvent,
)

from .const import (
    ATTR_ATTRIBUTION,
    ATTRIBUTION,
    DATABASE,
    DOMAIN,
    EVENT_HIGH_LOW,
    EXTERNAL_DIRECTORY,
    FORECAST_ENTITY,
    HIGH_LOW_TIMER,
    LANGUAGE_ENGLISH,
    MANUFACTURER,
    TEMP_CELSIUS,
    UNITS_IMPERIAL,
    UNITS_METRIC,
)
from .forecast import Forecast, ForecastConfig
from .helpers import ConversionFunctions, read_config, truebool
from .sensor_description import (
    DEVICE_SENSORS,
    FORECAST_SENSORS,
    OBSOLETE_SENSORS,
    BaseSensorDescription,
    SensorDescription,
    SqlSensorDescription,
    StorageSensorDescription,
)
from .sqlite import SQLFunctions

_LOGGER = logging.getLogger(__name__)

ATTRIBUTE_MISSING = object()
MQTT_TOPIC_FORMAT = "homeassistant/sensor/{}/{}/{}"
DEVICE_SERIAL_FORMAT = "{}_{}"


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
        elevation: float = 0,
        unit_system: str = UNITS_METRIC,
        rapid_wind_interval: int = 0,
        language: str = LANGUAGE_ENGLISH,
        mqtt_config: MqttConfig = MqttConfig(),
        udp_config: WeatherFlowUdpConfig = WeatherFlowUdpConfig(),
        forecast_config: ForecastConfig = None,
        database_file: str = None,
        filter_sensors: list[str] | None = None,
        invert_filter: bool = False,
    ) -> None:
        """Initialize a WeatherFlow MQTT."""
        self.elevation = elevation
        self.unit_system = unit_system
        self.rapid_wind_interval = rapid_wind_interval

        self.cnv = ConversionFunctions(unit_system, language)

        self.mqtt_config = mqtt_config
        self.udp_config = udp_config

        self.forecast = (
            Forecast.from_config(config=forecast_config, conversions=self.cnv)
            if forecast_config is not None
            else None
        )

        self.mqtt_client: MqttClient = None
        self.listener: WeatherFlowListener | None = None
        self._queue: asyncio.Queue | None = None
        self._queue_task: asyncio.Task | None = None
        self._init_sql_db(database_file=database_file)

        self._filter_sensors = filter_sensors
        self._invert_filter = invert_filter

        # Set timer variables
        self.rapid_last_run = 1621229580.583215  # A time in the past
        self.forecast_last_run: float | None = None
        self.high_low_last_run = 1621229580.583215  # A time in the past
        self.current_day = datetime.today().weekday()
        self.last_midnight = self.cnv.utc_last_midnight()

        # Read stored Values and set variable values
        self.wind_speed = None
        self.solar_radiation = None

    @property
    def is_imperial(self) -> bool:
        """Return `True` if the unit system is imperial, else `False`."""
        return self.unit_system == UNITS_IMPERIAL

    async def connect(self) -> None:
        """Connect to MQTT and UDP."""
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

        self.listener = WeatherFlowListener(self.udp_config.host, self.udp_config.port)
        self.listener.on(
            EVENT_DEVICE_DISCOVERED, lambda device: self._device_discovered(device)
        )
        try:
            await self.listener.start_listening()
            _LOGGER.info("The UDP server is listening on port %s", self.udp_config.port)
        except Exception as e:
            _LOGGER.error(
                "Could not start listening to the UDP Socket. Error is: %s", e
            )
            sys.exit(1)

        self._queue = asyncio.Queue()
        self._queue_task = asyncio.ensure_future(self._mqtt_queue_processor())

    async def run_time_based_updates(self) -> None:
        """Data update loop."""
        # Run New day function if Midnight
        if self.current_day != datetime.today().weekday():
            self.storage["rain_yesterday"] = self.storage["rain_today"]
            self.storage["rain_duration_yesterday"] = self.storage[
                "rain_duration_today"
            ]
            self.storage["rain_today"] = 0
            self.storage["rain_duration_today"] = 0
            self.storage["lightning_count_today"] = 0
            self.last_midnight = self.cnv.utc_last_midnight()
            self.sql.writeStorage(self.storage)
            self.sql.dailyHousekeeping()
            self.current_day = datetime.today().weekday()

        # Update High and Low values if it is time
        now = datetime.now().timestamp()
        if (now - self.high_low_last_run) >= HIGH_LOW_TIMER:
            highlow_topic = MQTT_TOPIC_FORMAT.format(
                DOMAIN, EVENT_HIGH_LOW, "attributes"
            )
            high_low_data = self.sql.readHighLow()
            self._add_to_queue(
                highlow_topic, json.dumps(high_low_data), qos=1, retain=True
            )
            self.high_low_last_run = datetime.now().timestamp()

        await self._update_forecast()

    def _add_to_queue(
        self, topic: str, payload: str | None = None, qos: int = 0, retain: bool = False
    ) -> None:
        """Add an item to the queue."""
        self._queue.put_nowait((topic, payload, qos, retain))

    def _device_discovered(self, device: WeatherFlowDevice) -> None:
        """Handle a discovered device."""

        def _load_complete():
            print(device, "was loaded")
            self._setup_sensors(device)
            device.on(
                EVENT_STATUS_UPDATE,
                lambda event: self._handle_status_update_event(device, event),
            )
            if isinstance(device, WeatherFlowSensorDevice):
                device.on(
                    EVENT_OBSERVATION,
                    lambda event: self._handle_observation_event(device, event),
                )
                if isinstance(device, AirSensorType):
                    device.on(
                        EVENT_STRIKE,
                        lambda event: self._handle_strike_event(device, event),
                    )
                if isinstance(device, SkySensorType):
                    device.on(
                        EVENT_RAPID_WIND,
                        lambda event: self._handle_wind_event(device, event),
                    )
                    device.on(
                        EVENT_RAIN_START,
                        lambda event: self._handle_rain_start_event(device, event),
                    )

        device.on(EVENT_LOAD_COMPLETE, lambda _: _load_complete())

    def _get_sensor_payload(
        self,
        sensor: BaseSensorDescription,
        device: WeatherFlowDevice,
        state_topic: str,
        attr_topic: str,
    ) -> OrderedDict:
        """Construct and return a sensor payload."""
        payload = OrderedDict()

        payload["name"] = f"{device.model} {device.serial_number} {sensor.name}"
        payload["unique_id"] = f"{device.serial_number}-{sensor.id}"
        if (units := sensor.unit_i if self.is_imperial else sensor.unit_m) is not None:
            payload["unit_of_measurement"] = units
        if (device_class := sensor.device_class) is not None:
            payload["device_class"] = device_class
        if (state_class := sensor.state_class) is not None:
            payload["state_class"] = state_class
        if (icon := sensor.icon) is not None:
            payload["icon"] = f"mdi:{icon}"
        payload["state_topic"] = state_topic
        payload["value_template"] = f"{{{{ value_json.{sensor.id} }}}}"
        payload["json_attributes_topic"] = attr_topic
        payload["device"] = {
            "identifiers": [f"{DOMAIN}_{device.serial_number}"],
            "manufacturer": MANUFACTURER,
            "name": f"{device.model} {device.serial_number}",
            "model": device.model,
            "sw_version": device.firmware_revision,
            **(
                {"via_device": f"{DOMAIN}_{device.hub_sn}"}
                if isinstance(device, WeatherFlowSensorDevice)
                else {}
            ),
        }

        return payload

    def _handle_observation_event(
        self, device: WeatherFlowSensorDevice, event: CustomEvent
    ) -> None:
        """Handle an observation event."""
        # Set some class level variables to help with sensors that may not have all data points available:
        if (val := getattr(device, "solar_radiation", None)) is not None:
            self.solar_radiation = val.m
        if (val := getattr(device, "rain_amount_previous_minute", None)) is not None:
            self.storage["rain_today"] += val.m
            if val.m > 0:
                self.storage["rain_duration_today"] += 1
                self.sql.writeStorage(self.storage)

        state_topic = MQTT_TOPIC_FORMAT.format(
            DEVICE_SERIAL_FORMAT.format(DOMAIN, device.serial_number),
            EVENT_OBSERVATION,
            "state",
        )
        data = OrderedDict()

        for sensor in DEVICE_SENSORS:
            # Skip if this device is missing the attribute
            if (
                attr := getattr(device, sensor.device_attr, ATTRIBUTE_MISSING)
            ) is ATTRIBUTE_MISSING or (
                sensor.id == "battery_mode" and not isinstance(device, TempestDevice)
            ):
                continue
            try:
                if isinstance(sensor, SensorDescription):
                    # TODO: Handle unique data points more elegantly...
                    if sensor.id == "pressure_trend":
                        continue

                    # Check for a custom function
                    if (fn := sensor.custom_fn) is not None:
                        # TODO: Handle unique data points more elegantly
                        if sensor.id == "feelslike":
                            attr = fn(self.cnv, device, self.wind_speed)
                        elif sensor.id in ("sealevel_pressure", "visibility"):
                            attr = fn(self.cnv, device, self.elevation)
                        elif sensor.id == "wbgt":
                            attr = fn(self.cnv, device, self.solar_radiation)
                        else:
                            attr = fn(self.cnv, device)

                        # Check if a description is included
                        if sensor.has_description and isinstance(attr, tuple):
                            attr, data[f"{sensor.id}_description"] = attr

                    # Check if the attr is a Quantity object
                    elif isinstance(attr, Quantity):
                        # See if conversion is needed
                        if (
                            unit := sensor.imperial_unit
                            if self.is_imperial
                            else sensor.metric_unit
                        ) is not None:
                            attr = attr.to(unit)

                        # Set the attribute to the Quantity's magnitude
                        attr = attr.m

                    # Check if rounding is needed
                    if (
                        attr is not None
                        and (decimals := sensor.decimals[1 if self.is_imperial else 0])
                        is not None
                    ):
                        attr = round(attr, decimals)

                elif isinstance(sensor, SqlSensorDescription):
                    attr = sensor.sql_fn(self.sql)

                elif isinstance(sensor, StorageSensorDescription):
                    attr = sensor.value(self.storage)

                    if (fn := sensor.cnv_fn) is not None:
                        attr = fn(self.cnv, attr)

                # Set the attribute in the payload
                data[sensor.id] = attr
            except Exception as ex:
                _LOGGER.error("Error setting sensor data for %s: %s", sensor.id, ex)

        # TODO: Handle unique data points more elegantly...
        if data["sealevel_pressure"]:
            (
                data["pressure_trend"],
                data["pressure_trend_value"],
            ) = self.sql.readPressureTrend(
                data["sealevel_pressure"], self.cnv.translations
            )
            self.sql.writePressure(data["sealevel_pressure"])

        data["last_reset_midnight"] = self.last_midnight

        self._add_to_queue(state_topic, json.dumps(data))
        self.sql.updateHighLow(data)
        # self.sql.updateDayData(data)

    def _handle_rain_start_event(
        self, device: SkySensorType, event: RainStartEvent
    ) -> None:
        """Handle a rain start event."""
        self.storage["rain_start"] = event.epoch
        self.sql.writeStorage(self.storage)

    def _handle_status_update_event(
        self, device: HubDevice | WeatherFlowSensorDevice, event: CustomEvent
    ) -> None:
        """Handle a hub status event."""
        device_serial = DEVICE_SERIAL_FORMAT.format(DOMAIN, device.serial_number)

        state_topic = MQTT_TOPIC_FORMAT.format(
            device_serial, EVENT_STATUS_UPDATE, "state"
        )
        state_data = OrderedDict()
        state_data["status"] = device.up_since.isoformat()
        self._add_to_queue(state_topic, json.dumps(state_data))

        attr_topic = MQTT_TOPIC_FORMAT.format(device_serial, "status", "attributes")
        attr_data = OrderedDict()
        attr_data[ATTR_ATTRIBUTION] = ATTRIBUTION
        attr_data["serial_number"] = device.serial_number
        attr_data["rssi"] = device.rssi.m

        if isinstance(device, HubDevice):
            attr_data["reset_flags"] = device.reset_flags
            _LOGGER.debug("HUB Reset Flags: %s", device.reset_flags)
        else:
            attr_data["voltage"] = device._voltage
            attr_data["sensor_status"] = device.sensor_status

            if device.sensor_status:
                _LOGGER.debug(
                    "Device %s has reported a sensor fault. Reason: %s",
                    device.serial_number,
                    device.sensor_status,
                )
            _LOGGER.debug(
                "DEVICE STATUS TRIGGERED AT %s\n -- Device: %s\n -- Firmware Revision: %s\n -- Voltage: %s",
                str(datetime.now()),
                device.serial_number,
                device.firmware_revision,
                device._voltage,
            )

        self._add_to_queue(attr_topic, json.dumps(attr_data))

    def _handle_strike_event(
        self, device: AirSensorType, event: LightningStrikeEvent
    ) -> None:
        """Handle a strike event."""
        self.sql.writeLightning()
        self.storage["lightning_count_today"] += 1
        self.storage["last_lightning_distance"] = self.cnv.distance(event.distance.m)
        self.storage["last_lightning_energy"] = event.energy
        self.storage["last_lightning_time"] = event.epoch
        self.sql.writeStorage(self.storage)

    def _handle_wind_event(self, device: SkySensorType, event: WindEvent) -> None:
        """Handle a wind event."""
        data = OrderedDict()
        state_topic = MQTT_TOPIC_FORMAT.format(
            DEVICE_SERIAL_FORMAT.format(DOMAIN, device.serial_number),
            EVENT_RAPID_WIND,
            "state",
        )
        now = datetime.now().timestamp()
        if (now - self.rapid_last_run) >= self.rapid_wind_interval:
            data["wind_speed"] = self.cnv.speed(event.speed.m)
            data["wind_bearing"] = event.direction.m
            data["wind_direction"] = self.cnv.direction(event.direction.m)
            self.wind_speed = event.speed.m
            self._add_to_queue(state_topic, json.dumps(data))
            self.rapid_last_run = datetime.now().timestamp()

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

    def _setup_mqtt_client(self) -> MqttClient:
        """Initialize MQTT client."""
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

    def _setup_sensors(self, device: WeatherFlowDevice) -> None:
        """Create Sensors in Home Assistant."""
        serial_number = device.serial_number
        domain_serial = DEVICE_SERIAL_FORMAT.format(DOMAIN, serial_number)

        # Create the config for the Sensors
        for sensor in DEVICE_SENSORS:
            sensor_id = sensor.id
            sensor_event = sensor.event

            if (
                getattr(device, sensor.device_attr, ATTRIBUTE_MISSING)
                is ATTRIBUTE_MISSING
            ):
                # Don't add sensors for devices that don't report on that attribute
                continue

            state_topic = MQTT_TOPIC_FORMAT.format(domain_serial, sensor_event, "state")
            attr_topic = MQTT_TOPIC_FORMAT.format(
                domain_serial, sensor_id, "attributes"
            )
            discovery_topic = MQTT_TOPIC_FORMAT.format(
                domain_serial, sensor_id, "config"
            )
            highlow_topic = MQTT_TOPIC_FORMAT.format(
                domain_serial, EVENT_HIGH_LOW, "attributes"
            )

            attribution = OrderedDict()
            payload: OrderedDict | None = None

            if self._filter_sensors is None or (
                (sensor_id in self._filter_sensors) is not self._invert_filter
            ):
                _LOGGER.info("Setting up %s sensor: %s", device.model, sensor.name)

                # Payload
                payload = self._get_sensor_payload(
                    sensor=sensor,
                    device=device,
                    state_topic=state_topic,
                    attr_topic=attr_topic,
                )

                # Attributes
                attribution[ATTR_ATTRIBUTION] = ATTRIBUTION

                # Add description if needed
                if sensor.has_description:
                    payload["json_attributes_topic"] = state_topic
                    template = OrderedDict()
                    template = attribution
                    template[
                        "description"
                    ] = f"{{{{ value_json.{sensor_id}_description }}}}"
                    payload["json_attributes_template"] = json.dumps(template)

                # Add additional attributes to some sensors
                if sensor_id == "pressure_trend":
                    payload["json_attributes_topic"] = state_topic
                    template = OrderedDict()
                    template = attribution
                    template["trend_value"] = "{{ value_json.pressure_trend_value }}"
                    payload["json_attributes_template"] = json.dumps(template)

                # Add extra attributes if needed
                if sensor.extra_att:
                    payload["json_attributes_topic"] = highlow_topic
                    template = OrderedDict()
                    template = attribution
                    template["max_day"] = f"{{{{ value_json.{sensor_id}['max_day'] }}}}"
                    template[
                        "max_day_time"
                    ] = f"{{{{ value_json.{sensor_id}['max_day_time'] }}}}"
                    template[
                        "max_month"
                    ] = f"{{{{ value_json.{sensor_id}['max_month'] }}}}"
                    template[
                        "max_month_time"
                    ] = f"{{{{ value_json.{sensor_id}['max_month_time'] }}}}"
                    template["max_all"] = f"{{{{ value_json.{sensor_id}['max_all'] }}}}"
                    template[
                        "max_all_time"
                    ] = f"{{{{ value_json.{sensor_id}['max_all_time'] }}}}"
                    if sensor.show_min_att:
                        template[
                            "min_day"
                        ] = f"{{{{ value_json.{sensor_id}['min_day'] }}}}"
                        template[
                            "min_day_time"
                        ] = f"{{{{ value_json.{sensor_id}['min_day_time'] }}}}"
                        template[
                            "min_month"
                        ] = f"{{{{ value_json.{sensor_id}['min_month'] }}}}"
                        template[
                            "min_month_time"
                        ] = f"{{{{ value_json.{sensor_id}['min_month_time'] }}}}"
                        template[
                            "min_all"
                        ] = f"{{{{ value_json.{sensor_id}['min_all'] }}}}"
                        template[
                            "min_all_time"
                        ] = f"{{{{ value_json.{sensor_id}['min_all_time'] }}}}"
                    payload["json_attributes_template"] = json.dumps(template)

            self._add_to_queue(
                discovery_topic, json.dumps(payload or {}), qos=1, retain=True
            )
            self._add_to_queue(attr_topic, json.dumps(attribution), qos=1, retain=True)

        if isinstance(device, HubDevice):
            run_forecast = False
            fcst_state_topic = MQTT_TOPIC_FORMAT.format(
                DOMAIN, FORECAST_ENTITY, "state"
            )
            fcst_attr_topic = MQTT_TOPIC_FORMAT.format(
                DOMAIN, FORECAST_ENTITY, "attributes"
            )
            for sensor in FORECAST_SENSORS:
                discovery_topic = MQTT_TOPIC_FORMAT.format(DOMAIN, sensor.id, "config")
                payload: OrderedDict | None = None
                if self.forecast is not None:
                    _LOGGER.info("Setting up %s sensor: %s", device.model, sensor.name)
                    run_forecast = True
                    payload = self._get_sensor_payload(
                        sensor=sensor,
                        device=device,
                        state_topic=fcst_state_topic,
                        attr_topic=fcst_attr_topic,
                    )
                self._add_to_queue(
                    discovery_topic, json.dumps(payload or {}), qos=1, retain=True
                )

            if run_forecast:
                asyncio.ensure_future(self._update_forecast())

        # cleanup obsolete sensors
        for sensor in OBSOLETE_SENSORS:
            self._add_to_queue(
                topic=MQTT_TOPIC_FORMAT.format(domain_serial, sensor, "config")
            )

    async def _mqtt_queue_processor(self) -> None:
        """MQTT queue processor."""
        while True:
            topic, payload, qos, retain = await self._queue.get()
            await self._publish_mqtt(topic, payload, qos, retain)
            self._queue.task_done()

    async def _publish_mqtt(
        self, topic: str, payload: str | None = None, qos: int = 0, retain: bool = False
    ) -> None:
        """Publish a MQTT topic with payload."""
        try:
            self.mqtt_client.publish(topic, payload, qos=qos, retain=retain)
        except Exception as e:
            _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
        await asyncio.sleep(0.01)

    async def _update_forecast(self) -> None:
        """Attempt to update the forecast."""
        # Update the Forecast if it is time and enabled
        if (
            self.forecast is not None
            and (
                (now := datetime.now().timestamp())
                - (0 if self.forecast_last_run is None else self.forecast_last_run)
            )
            >= self.forecast.interval * 60
        ):
            fcst_state_topic = MQTT_TOPIC_FORMAT.format(
                DOMAIN, FORECAST_ENTITY, "state"
            )
            fcst_attr_topic = MQTT_TOPIC_FORMAT.format(
                DOMAIN, FORECAST_ENTITY, "attributes"
            )
            condition_data, fcst_data = await self.forecast.update_forecast()
            if condition_data is not None:
                self._add_to_queue(fcst_state_topic, json.dumps(condition_data))
                self._add_to_queue(fcst_attr_topic, json.dumps(fcst_data))
                self.forecast_last_run = now


async def main():
    """Entry point for program."""
    logging.basicConfig(level=logging.INFO)

    if is_supervisor := truebool(os.getenv("HA_SUPERVISOR")):
        config = await get_supervisor_configuration()
    else:
        config = os.environ

    _LOGGER.info("Timezone is %s", os.environ.get("TZ"))

    # Read the config Settings
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

    if truebool(config.get("DEBUG")):
        logging.getLogger().setLevel(logging.DEBUG)

    if isinstance(filter_sensors := config.get("FILTER_SENSORS"), str):
        filter_sensors = [sensor.strip() for sensor in filter_sensors.split(",")]
    invert_filter = truebool(config.get("INVERT_FILTER"))

    # Read the sensor config
    if filter_sensors is None and not is_supervisor:
        filter_sensors = read_config()

    weatherflowmqtt = WeatherFlowMqtt(
        elevation=elevation,
        unit_system=unit_system,
        rapid_wind_interval=rw_interval,
        language=language,
        mqtt_config=mqtt_config,
        udp_config=udp_config,
        forecast_config=forecast_config,
        database_file=DATABASE,
        filter_sensors=filter_sensors,
        invert_filter=invert_filter,
    )
    await weatherflowmqtt.connect()

    # Watch for message from the UDP socket
    while weatherflowmqtt.listener.is_listening:
        await asyncio.sleep(60)
        await weatherflowmqtt.run_time_based_updates()


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
