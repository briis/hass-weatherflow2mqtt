"""Program listening to the UDP Broadcast from
   a WeatherFlow Weather Station and publishing
   sensor data to MQTT.
"""

import json
from typing import OrderedDict
import paho.mqtt.client as mqtt
import asyncio
import logging
import time
from datetime import datetime
import sys
import os

from aioudp import open_local_endpoint
from helpers import ConversionFunctions, DataStorage
from forecast import Forecast
from const import (
    ATTRIBUTION,
    ATTR_ATTRIBUTION,
    ATTR_BRAND,
    BRAND,
    DOMAIN,
    EVENT_AIR_DATA,
    EVENT_DEVICE_STATUS,
    EVENT_FORECAST,
    EVENT_RAPID_WIND,
    EVENT_HUB_STATUS,
    EVENT_PRECIP_START,
    EVENT_SKY_DATA,
    EVENT_STRIKE,
    EVENT_TEMPEST_DATA,
    SENSOR_CLASS,
    SENSOR_DEVICE,
    SENSOR_ICON,
    SENSOR_ID,
    SENSOR_NAME,
    SENSOR_UNIT_I,
    SENSOR_UNIT_M,
    UNITS_IMPERIAL,
    WEATHERFLOW_SENSORS,
)

_LOGGER = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.DEBUG)

    # Read the config Settings
    _LOGGER.info("Timezone is %s", os.environ["TZ"])
    is_tempest = eval(os.environ["TEMPEST_DEVICE"])
    weatherflow_ip = os.environ["WF_HOST"]
    weatherflow_port = int(os.environ["WF_PORT"])
    elevation = float(os.environ["ELEVATION"])
    mqtt_host = os.environ["MQTT_HOST"]
    mqtt_port = int(os.environ["MQTT_PORT"])
    mqtt_username = os.environ["MQTT_USERNAME"]
    mqtt_password = os.environ["MQTT_PASSWORD"]
    mqtt_debug = eval(os.environ["MQTT_DEBUG"])
    unit_system = os.environ["UNIT_SYSTEM"]
    rw_interval = int(os.environ["RAPID_WIND_INTERVAL"])
    show_debug = eval(os.environ["DEBUG"])
    add_forecast = eval(os.environ["ADD_FORECAST"])
    station_id = os.environ["STATION_ID"]
    station_token = os.environ["STATION_TOKEN"]
    forecast_interval = int(os.environ["FORECAST_INTERVAL"])


    cnv = ConversionFunctions(unit_system)
    data_store = DataStorage()
    if add_forecast:
        forecast = Forecast(station_id, unit_system, station_token)
        forecast_interval = forecast_interval * 60
    # Read the sensor config
    sensors = await data_store.read_config()

    mqtt_anonymous = False
    if not mqtt_username or not mqtt_password:
        _LOGGER.debug("MQTT Credentials not needed")
        mqtt_anonymous = True

    # Setup and connect to MQTT Broker
    try:
        client = mqtt.Client(client_id="weatherflow2mqtt")
        client.max_inflight_messages_set(40)
        if not mqtt_anonymous:
            client.username_pw_set(username=mqtt_username, password=mqtt_password)
        if mqtt_debug:
            client.enable_logger()
            _LOGGER.debug("MQTT Credentials: %s - %s", mqtt_username, mqtt_password)
        client.connect(mqtt_host, port=mqtt_port)
        _LOGGER.info(
            "Connected to the MQTT server on address %s and port %s...",
            mqtt_host,
            mqtt_port,
        )
    except Exception as e:
        _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
        sys.exit(1)

    # Setup and start listening to WeatherFlow UDP Socket
    try:
        endpoint = await open_local_endpoint(host=weatherflow_ip, port=weatherflow_port)
        _LOGGER.info("The UDP server is running on port %s...", endpoint.address[1])
    except Exception as e:
        _LOGGER.error("Could not start listening to the UDP Socket. Error is: %s", e)
        sys.exit(1)

    # Configure Sensors in MQTT
    await setup_sensors(endpoint, client, unit_system, sensors, is_tempest, add_forecast)

    # Set timer variables
    rapid_last_run = 1621229580.583215  # A time in the past
    forecast_last_run = 1621229580.583215  # A time in the past
    current_day = datetime.today().weekday()

    # Read stored Values and set variable values
    storage = await data_store.read_storage()
    wind_speed = None

    # Watch for message from the UDP socket
    while True:
        data, (host, port) = await endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")

        # Run New day function if Midnight
        if current_day != datetime.today().weekday():
            storage["rain_yesterday"] = storage["rain_today"]
            storage["rain_today"] = 0
            storage["lightning_count_today"] = 0
            await data_store.write_storage(storage)
            await data_store.housekeeping_strike()
            current_day = datetime.today().weekday()

        # Update the Forecast if it is time and enabled
        if add_forecast:
            now = datetime.now().timestamp()
            fcst_state_topic = "homeassistant/sensor/{}/{}/state".format(DOMAIN, EVENT_FORECAST)
            fcst_attr_topic = "homeassistant/sensor/{}/{}/attributes".format(DOMAIN, EVENT_FORECAST)
            if (now - forecast_last_run) >= forecast_interval:
                condition_data, fcst_data  = await forecast.update_forecast()
                client.publish(fcst_state_topic, json.dumps(condition_data))
                client.publish(fcst_attr_topic, json.dumps(fcst_data))
                forecast_last_run = now

        # Process the data
        if msg_type is not None:
            data = OrderedDict()
            state_topic = "homeassistant/sensor/{}/{}/state".format(DOMAIN, msg_type)
            if msg_type in EVENT_RAPID_WIND:
                now = datetime.now().timestamp()
                if (now - rapid_last_run) >= rw_interval:
                    obs = json_response["ob"]
                    data["wind_speed"] = await cnv.speed(obs[1])
                    data["wind_bearing"] = obs[2]
                    data["wind_direction"] = await cnv.direction(obs[2])
                    wind_speed = obs[1]
                    client.publish(state_topic, json.dumps(data))
                    rapid_last_run = datetime.now().timestamp()
            if msg_type in EVENT_HUB_STATUS:
                data["uptime"] = await cnv.humanize_time(json_response.get("uptime"))
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_PRECIP_START:
                obs = json_response["evt"]
                storage["rain_start"] = datetime.fromtimestamp(obs[0]).isoformat()
                await data_store.write_storage(storage)
            if msg_type in EVENT_STRIKE:
                obs = json_response["evt"]
                await data_store.write_strike_storage()
                storage["lightning_count_today"] += 1
                storage["last_lightning_distance"] = await cnv.distance(obs[1])
                storage["last_lightning_energy"] = obs[2]
                storage["last_lightning_time"] = time.time()
                await data_store.write_storage(storage)
            if msg_type in EVENT_AIR_DATA:
                obs = json_response["obs"][0]
                data["station_pressure"] = await cnv.pressure(obs[1])
                data["air_temperature"] = await cnv.temperature(obs[2])
                data["relative_humidity"] = obs[3]
                data["lightning_strike_count"] = await data_store.read_strike_storage()
                data["lightning_strike_count_today"] = storage["lightning_count_today"]
                data["lightning_strike_distance"] = storage["last_lightning_distance"]
                data["lightning_strike_energy"] = storage["last_lightning_energy"]
                data["lightning_strike_time"] = datetime.fromtimestamp(
                    storage["last_lightning_time"]
                ).isoformat()
                data["battery_air"] = round(obs[6], 2)
                data["sealevel_pressure"] = await cnv.sea_level_pressure(obs[2], obs[1], elevation)
                data["air_density"] = await cnv.air_density(obs[2], obs[1])
                data["dewpoint"] = await cnv.dewpoint(obs[2], obs[3])
                data["feelslike"] = await cnv.feels_like(obs[2], obs[3], wind_speed)
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_SKY_DATA:
                obs = json_response["obs"][0]
                data["illuminance"] = obs[1]
                data["uv"] = obs[2]
                storage["rain_today"] += obs[3]
                data["rain_today"] = await cnv.rain(storage["rain_today"])
                data["rain_yesterday"] = await cnv.rain(storage["rain_yesterday"])
                data["rain_start_time"] = storage["rain_start"]
                data["wind_lull"] = await cnv.speed(obs[4])
                data["wind_speed_avg"] = await cnv.speed(obs[5])
                data["wind_gust"] = await cnv.speed(obs[6])
                data["wind_bearing_avg"] = obs[7]
                data["wind_direction_avg"] = await cnv.direction(obs[7])
                data["battery"] = round(obs[8], 2)
                data["solar_radiation"] = obs[10]
                data["precipitation_type"] = await cnv.rain_type(obs[12])
                data["rain_rate"] = await cnv.rain_rate(obs[3])
                client.publish(state_topic, json.dumps(data))
                if obs[3] > 0:
                    await data_store.write_storage(storage)
            if msg_type in EVENT_TEMPEST_DATA:
                obs = json_response["obs"][0]

                state_topic = "homeassistant/sensor/{}/{}/state".format(
                    DOMAIN, EVENT_SKY_DATA
                )
                data["wind_lull"] = await cnv.speed(obs[1])
                data["wind_speed_avg"] = await cnv.speed(obs[2])
                data["wind_gust"] = await cnv.speed(obs[3])
                data["wind_bearing_avg"] = obs[4]
                data["wind_direction_avg"] = await cnv.direction(obs[4])
                data["illuminance"] = obs[9]
                data["uv"] = obs[10]
                data["solar_radiation"] = obs[11]
                storage["rain_today"] += obs[12]
                data["rain_today"] = await cnv.rain(storage["rain_today"])
                data["rain_yesterday"] = await cnv.rain(storage["rain_yesterday"])
                data["rain_start_time"] = storage["rain_start"]
                data["precipitation_type"] = await cnv.rain_type(obs[13])
                data["battery"] = round(obs[16], 2)
                data["rain_rate"] = await cnv.rain_rate(obs[12])
                client.publish(state_topic, json.dumps(data))

                state_topic = "homeassistant/sensor/{}/{}/state".format(
                    DOMAIN, EVENT_AIR_DATA
                )
                data = OrderedDict()
                data["station_pressure"] = await cnv.pressure(obs[6])
                data["air_temperature"] = await cnv.temperature(obs[7])
                data["relative_humidity"] = obs[8]
                data["lightning_strike_count"] = await data_store.read_strike_storage()
                data["lightning_strike_count_today"] = storage["lightning_count_today"]
                data["lightning_strike_distance"] = storage["last_lightning_distance"]
                data["lightning_strike_energy"] = storage["last_lightning_energy"]
                data["lightning_strike_time"] = datetime.fromtimestamp(
                    storage["last_lightning_time"]
                ).isoformat()
                data["sealevel_pressure"] = await cnv.sea_level_pressure(obs[7], obs[6], elevation)
                data["air_density"] = await cnv.air_density(obs[7], obs[6])
                data["dewpoint"] = await cnv.dewpoint(obs[7], obs[8])
                data["feelslike"] = await cnv.feels_like(obs[7], obs[8], wind_speed)
                client.publish(state_topic, json.dumps(data))

                if obs[12] > 0:
                    await data_store.write_storage(storage)

            if msg_type in EVENT_DEVICE_STATUS:
                if show_debug:
                    now = datetime.now()
                    serial_number = json_response.get("serial_number")
                    firmware_revision = json_response.get("firmware_revision")
                    voltage = json_response.get("voltage")
                    _LOGGER.debug(
                        "DEVICE STATUS TRIGGERED AT %s\n  -- Device: %s\n -- Firmware Revision: %s\n -- Voltage: %s",
                        str(now),
                        serial_number,
                        firmware_revision,
                        voltage,
                    )
            if msg_type != EVENT_RAPID_WIND and msg_type != EVENT_HUB_STATUS:
                # Update the Forecast State (Ensure there is data if HA restarts)
                if add_forecast:
                    client.publish(fcst_state_topic, json.dumps(condition_data))
                    client.publish(fcst_attr_topic, json.dumps(fcst_data))

            if show_debug:
                _LOGGER.debug(
                    "Event type %s has been processed, with payload: %s",
                    msg_type,
                    json.dumps(data),
                )


async def setup_sensors(endpoint, mqtt_client, unit_system, sensors, is_tempest, add_forecast):
    """Setup the Sensors in Home Assistant."""

    # Get Hub Information
    while True:
        data, (host, port) = await endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")
        if msg_type == EVENT_HUB_STATUS:
            serial_number = json_response.get("serial_number")
            firmware = json_response.get("firmware_revision")
            break

    # Create the config for the Sensors
    units = SENSOR_UNIT_I if unit_system == UNITS_IMPERIAL else SENSOR_UNIT_M
    for sensor in WEATHERFLOW_SENSORS:
        sensor_name = sensor[SENSOR_NAME]
        # Don't add the Weather Sensor if forecast disabled
        if not add_forecast and sensor[SENSOR_DEVICE] == EVENT_FORECAST:
            _LOGGER.debug("Skipping Forecast sensor %s %s", add_forecast, sensor[SENSOR_DEVICE])
            continue
        # Don't add the AIR Unit Battery if this is a Tempest Device
        if is_tempest and sensor[SENSOR_ID] == "battery_air":
            continue
        # Modify name of Battery Device if Tempest Unit
        if is_tempest and sensor[SENSOR_ID] == "battery":
            sensor_name = "Battery TEMPEST"
        state_topic = "homeassistant/sensor/{}/{}/state".format(
            DOMAIN, sensor[SENSOR_DEVICE]
        )
        attr_topic = "homeassistant/sensor/{}/{}/attributes".format(
            DOMAIN, sensor[SENSOR_DEVICE]
        )
        discovery_topic = "homeassistant/sensor/{}/{}/config".format(
            DOMAIN, sensor[SENSOR_ID]
        )

        attribution = OrderedDict()
        attribution[ATTR_ATTRIBUTION] = ATTRIBUTION
        attribution[ATTR_BRAND] = BRAND

        payload = OrderedDict()
        if sensors is None or sensor[SENSOR_ID] in sensors:
            _LOGGER.info("SETTING UP %s SENSOR", sensor_name)
            payload["name"] = "{}".format(sensor_name)
            payload["unique_id"] = "{}-{}".format(serial_number, sensor[SENSOR_ID])
            if sensor[units] is not None:
                payload["unit_of_measurement"] = sensor[units]
            if sensor[SENSOR_CLASS] is not None:
                payload["device_class"] = sensor[SENSOR_CLASS]
            if sensor[SENSOR_ICON] is not None:
                payload["icon"] = f"mdi:{sensor[SENSOR_ICON]}"
            payload["state_topic"] = state_topic
            payload["value_template"] = "{{{{ value_json.{} }}}}".format(
                sensor[SENSOR_ID]
            )
            payload["json_attributes_topic"] = attr_topic
            payload["device"] = {
                "identifiers": ["WeatherFlow_{}".format(serial_number)],
                "connections": [["mac", serial_number]],
                "manufacturer": "WeatherFlow",
                "name": "WeatherFlow2MQTT",
                "model": "WeatherFlow Weather Station",
                "sw_version": firmware,
            }

        try:
            mqtt_client.publish(
                discovery_topic, json.dumps(payload), qos=1, retain=True
            )
            await asyncio.sleep(0.05)
            mqtt_client.publish(attr_topic, json.dumps(attribution), qos=1, retain=True)
            await asyncio.sleep(0.2)
        except Exception as e:
            _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
            break


# Main Program starts
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Program")
