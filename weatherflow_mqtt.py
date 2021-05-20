"""Program listening to the UDP Broadcast from
   a WeatherFlow Weather Station and publishing
   sensor data to MQTT.
"""

import json
from typing import OrderedDict
import paho.mqtt.client as mqtt
import asyncio
import logging
import yaml
import time
from datetime import datetime, date
import sys

from aioudp import open_local_endpoint
from helpers import ConversionFunctions, DataStorage
from const import (
    DOMAIN,
    EVENT_AIR_DATA,
    EVENT_DEVICE_STATUS,
    EVENT_RAPID_WIND,
    EVENT_HUB_STATUS,
    EVENT_PRECIP_START,
    EVENT_SKY_DATA,
    EVENT_STRIKE,
    EVENT_TEMPEST_DATA,
    EXTERNAL_DIRECTORY,
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

    
    # Read the config file
    filepath = f"{EXTERNAL_DIRECTORY}/config.yaml"
    with open(filepath) as json_file:
        data = yaml.load(json_file, Loader=yaml.FullLoader)
        weatherflow_ip = data["station"]["host"]
        weatherflow_port = data["station"]["port"]
        elevation = data["station"]["elevation"]
        mqtt_host = data["mqtt"]["host"]
        mqtt_port = data["mqtt"]["port"]
        mqtt_username = data["mqtt"]["username"]
        mqtt_password = data["mqtt"]["password"]
        mqtt_debug = data["mqtt"]["debug"]
        unit_system = data["unit_system"]
        rw_interval = data["rapid_wind_interval"]
        show_debug = data["debug"]
        sensors = data.get("sensors")

    mqtt_anonymous = False
    if not mqtt_username or not mqtt_password:
        mqtt_anonymous = True

    cnv = ConversionFunctions(unit_system)
    data_store = DataStorage()

    # Setup and connect to MQTT Broker
    try:
        client =mqtt.Client()
        client.max_inflight_messages_set(40)
        if not mqtt_anonymous:
            client.username_pw_set(username=mqtt_username,password=mqtt_password)
        if mqtt_debug == "on":
            client.enable_logger()
        client.connect(mqtt_host, port=mqtt_port)
        _LOGGER.info("Connected to the MQTT server on address %s and port %s...", mqtt_host, mqtt_port)
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
    await setup_sensors(endpoint, client, unit_system, sensors)

    # Set timer variables
    rapid_last_run = 1621229580.583215 # A time in the past
    current_day = datetime.today().weekday()

    # Read stored Values and set variable values
    storage = await data_store.read_storage()
    rain_today = storage["rain_today"]
    strike_count = storage["lightning_count"]

    # Publish Initial Data
    data = OrderedDict()
    state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, EVENT_STRIKE)
    data['lightning_strike_distance'] = storage['last_lightning_distance']
    data['lightning_strike_energy'] = storage['last_lightning_energy']
    client.publish(state_topic, json.dumps(data))

    # Publish Initial Data for Precipitation Start Event
    data = OrderedDict()
    state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, EVENT_PRECIP_START)
    data['rain_start_time'] = storage['rain_start']
    client.publish(state_topic, json.dumps(data))

    # Setup variables for x-device calculations
    wind_speed = None

    # Watch for message from the UDP socket
    while True:
        data, (host, port) = await endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")

        # Run New day function if it is time
        if current_day != datetime.today().weekday():
            rain_today = 0
            storage["rain_today"] = 0
            current_day = datetime.today().weekday()

        # Clear Ligtning Data if data older than 3 hours
        if time.time() - storage['last_lightning_time'] > 10800:
            strike_count = 0

        #Process the data
        if msg_type is not None:
            data = OrderedDict()
            state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, msg_type)
            if msg_type in EVENT_RAPID_WIND:
                now = datetime.now().timestamp()
                if (now - rapid_last_run) >= rw_interval:
                    obs = json_response["ob"]
                    data['wind_speed'] = await cnv.speed(obs[1])
                    data['wind_bearing'] = obs[2]
                    data['wind_direction'] = await cnv.direction(obs[2])
                    wind_speed = obs[1]
                    client.publish(state_topic, json.dumps(data))
                    rapid_last_run = datetime.now().timestamp()
            if msg_type in EVENT_HUB_STATUS:
                data['uptime'] = await cnv.humanize_time(json_response.get("uptime"))
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_PRECIP_START:
                obs = json_response["evt"]
                data['rain_start_time'] = datetime.fromtimestamp(obs[0]).isoformat()
                client.publish(state_topic, json.dumps(data))
                storage['rain_start'] = datetime.fromtimestamp(obs[0]).isoformat()
                await data_store.write_storage(storage)
            if msg_type in EVENT_STRIKE:
                obs = json_response["evt"]
                data['lightning_strike_distance'] = await cnv.distance(obs[1])
                data['lightning_strike_energy'] = obs[2]
                client.publish(state_topic, json.dumps(data))
                strike_count += 1
                storage['last_lightning_distance'] = await cnv.distance(obs[1])
                storage['last_lightning_energy'] = obs[2]
                storage['last_lightning_time'] = time.time()
                storage['lightning_count'] = strike_count
                await data_store.write_storage(storage)
            if msg_type in EVENT_AIR_DATA:
                obs = json_response["obs"][0]
                data['station_pressure'] = await cnv.pressure(obs[1])
                data['air_temperature'] = await cnv.temperature(obs[2])
                data['relative_humidity'] = obs[3]
                data['lightning_strike_count'] = strike_count
                data['battery_air'] = obs[6]
                data['sealevel_pressure'] = await cnv.pressure(obs[1] + (elevation / 9.2))
                data['air_density'] = await cnv.air_density(obs[2], obs[1])
                data['dewpoint'] = await cnv.dewpoint(obs[2], obs[3])
                data['feelslike'] = await cnv.feels_like(obs[2], obs[3], wind_speed)
                client.publish(state_topic, json.dumps(data))
                if obs[4] > 0:
                    storage['lightning_count'] = storage['lightning_count'] + obs[4]
                    await data_store.write_storage(storage)
            if msg_type in EVENT_SKY_DATA:
                obs = json_response["obs"][0]
                data['illuminance'] = obs[1]
                data['uv'] = obs[2]
                rain_today = rain_today + obs[3]
                data['rain_accumulated'] = await cnv.rain(rain_today)
                data['wind_lull'] = await cnv.speed(obs[4])
                data['wind_speed_avg'] = await cnv.speed(obs[5])
                data['wind_gust'] = await cnv.speed(obs[6])
                data['wind_bearing_avg'] = obs[7]
                data['wind_direction_avg'] = await cnv.direction(obs[7])
                data['battery_sky'] = obs[8]
                data['solar_radiation'] = obs[10]
                data['precipitation_type'] = await cnv.rain_type(obs[12])
                data['rain_rate'] = await cnv.rain_rate(obs[3])
                client.publish(state_topic, json.dumps(data))
                if obs[3] > 0:
                    storage['rain_today'] = rain_today
                    await data_store.write_storage(storage)
            if msg_type in EVENT_TEMPEST_DATA:
                obs = json_response["obs"][0]

                state_topic = 'homeassistant/sensor/{}/obs_sky/state'.format(DOMAIN)
                data['wind_lull'] = await cnv.speed(obs[1])
                data['wind_speed_avg'] = await cnv.speed(obs[2])
                data['wind_gust'] = await cnv.speed(obs[3])
                data['wind_bearing_avg'] = obs[4]
                data['wind_direction_avg'] = await cnv.direction(obs[4])
                data['illuminance'] = obs[9]
                data['uv'] = obs[10]
                data['solar_radiation'] = obs[11]
                rain_today = rain_today + obs[12]
                data['rain_accumulated'] = await cnv.rain(rain_today)
                data['precipitation_type'] = await cnv.rain_type(obs[13])
                data['battery_sky'] = obs[16]
                data['rain_rate'] = await cnv.rain_rate(obs[12])
                client.publish(state_topic, json.dumps(data))

                state_topic = 'homeassistant/sensor/{}/obs_air/state'.format(DOMAIN)
                data = OrderedDict()
                data['station_pressure'] = await cnv.pressure(obs[6])
                data['air_temperature'] = await cnv.temperature(obs[7])
                data['relative_humidity'] = obs[8]
                data['lightning_strike_count'] = storage['lightning_count'] + obs[15]
                data['sealevel_pressure'] = await cnv.pressure(obs[6] + (elevation / 9.2), 2)
                data['air_density'] = await cnv.air_density(obs[7], obs[6])
                data['dewpoint'] = await cnv.dewpoint(obs[7], obs[8])
                data['feelslike'] = await cnv.feels_like(obs[7], obs[8], wind_speed)
                client.publish(state_topic, json.dumps(data))

                if obs[15] > 0 or obs[12] > 0:
                    storage['rain_today'] = rain_today
                    storage['lightning_count'] = storage['lightning_count'] + obs[15]
                    await data_store.write_storage(storage)

            if msg_type in EVENT_DEVICE_STATUS:
                if show_debug == "on":
                    now = datetime.now()
                    serial_number = json_response.get("serial_number")
                    firmware_revision = json_response.get("firmware_revision")
                    voltage = json_response.get("voltage")
                    _LOGGER.debug("DEVICE STATUS TRIGGERED AT %s\n  -- Device: %s\n -- Firmware Revision: %s\n -- Voltage: %s", str(now), serial_number, firmware_revision, voltage)


async def setup_sensors(endpoint, mqtt_client, unit_system, sensors):
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
        state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, sensor[SENSOR_DEVICE])
        discovery_topic = 'homeassistant/sensor/{}/{}/config'.format(DOMAIN, sensor[SENSOR_ID])
        payload = OrderedDict()
        if sensors is None or sensor[SENSOR_ID] in sensors:
            _LOGGER.info("SETTING UP %s SENSOR", sensor[SENSOR_NAME])
            payload['name'] = "{}".format(sensor[SENSOR_NAME])
            payload['unique_id'] = "{}-{}".format(serial_number, sensor[SENSOR_ID])
            if sensor[units] is not None:
                payload['unit_of_measurement'] = sensor[units]
            if sensor[SENSOR_CLASS] is not None:
                payload['device_class'] = sensor[SENSOR_CLASS]
            if sensor[SENSOR_ICON] is not None:
                payload['icon'] = f"mdi:{sensor[SENSOR_ICON]}"
            payload['state_topic'] = state_topic
            payload['value_template'] = "{{{{ value_json.{} }}}}".format(sensor[SENSOR_ID])
            payload['device'] = {
                    'identifiers' : ["WeatherFlow_{}".format(serial_number)],
                    'connections' : [["mac", serial_number]],
                    'manufacturer' : 'WeatherFlow',
                    'name' : 'WeatherFlow2MQTT',
                    'model' : 'WeatherFlow Weather Station',
                    'sw_version': firmware
            }
            
        try:
            mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)
            await asyncio.sleep(0.2)
        except Exception as e:
            _LOGGER.error("Could not connect to MQTT Server. Error is: %s", e)
            break

#Main Program starts
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Program")
