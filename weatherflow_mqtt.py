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
from datetime import datetime

from aioudp import open_local_endpoint
from helpers import ConversionFunctions
from const import (
    DOMAIN,
    DOMAIN_SHORT,
    EVENT_AIR_DATA,
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

    # Read the config file
    # filepath = "config.yaml"
    filepath = "/config/config.yaml"
    with open(filepath) as json_file:
        data = yaml.load(json_file, Loader=yaml.FullLoader)
        weatherflow_ip = data["weatherflow"]["host"]
        weatherflow_port = data["weatherflow"]["port"]
        mqtt_host = data["mqtt"]["host"]
        mqtt_port = data["mqtt"]["port"]
        mqtt_username = data["mqtt"]["username"]
        mqtt_password = data["mqtt"]["password"]
        elevation = data["station"]["elevation"]
        unit_system = data["unit_system"]
        rw_interval = data["rapid_wind_interval"]

    cnv = ConversionFunctions(unit_system)

    #Setup and connect to MQTT Broker
    client =mqtt.Client("WFMQTT")
    client.username_pw_set(username=mqtt_username,password=mqtt_password)
    client.connect(mqtt_host, port=mqtt_port)

    #Setup and start listening to WeatherFlow UDP Socket
    endpoint = await open_local_endpoint(host=weatherflow_ip, port=weatherflow_port)
    _LOGGER.debug("The UDP server is running on port %s...", endpoint.address[1])

    # Configure Sensors in MQTT
    await setup_sensors(endpoint, client, unit_system)

    # Set timer variables (A time in the past)
    rapid_last_run = 1621229580.583215

    # Publish Initial Data for Lightning Event
    data = OrderedDict()
    state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, EVENT_STRIKE)
    data['lightning_strike_distance'] = 0
    data['lightning_strike_energy'] = 0
    client.publish(state_topic, json.dumps(data))

    # Publish Initial Data for Precipitation Start Event
    data = OrderedDict()
    state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, EVENT_PRECIP_START)
    data['rain_start_time'] = "Not Recorded"
    client.publish(state_topic, json.dumps(data))

    # Watch for message from the UDP socket
    while True:
        data, (host, port) = await endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")

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
                    client.publish(state_topic, json.dumps(data))
                    rapid_last_run = datetime.now().timestamp()
            if msg_type in EVENT_PRECIP_START:
                obs = json_response["evt"]
                data['rain_start_time'] = datetime.fromtimestamp(obs[0])
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_STRIKE:
                obs = json_response["evt"]
                data['lightning_strike_distance'] = await cnv.distance(obs[1])
                data['lightning_strike_energy'] = obs[2]
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_AIR_DATA:
                obs = json_response["obs"][0]
                data['station_pressure'] = await cnv.pressure(obs[1])
                data['air_temperature'] = await cnv.temperature(obs[2])
                data['relative_humidity'] = obs[3]
                data['lightning_strike_count'] = obs[4]
                data['lightning_strike_avg_distance'] = await cnv.distance(obs[5])
                data['battery_air'] = obs[6]
                data['sealevel_pressure'] = await cnv.pressure(obs[1] + (elevation / 9.2))
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_SKY_DATA:
                obs = json_response["obs"][0]
                data['illuminance'] = obs[1]
                data['uv'] = obs[2]
                data['rain_accumulated'] = await cnv.rain(obs[3])
                data['wind_lull'] = await cnv.speed(obs[4])
                data['wind_speed_avg'] = await cnv.speed(obs[5])
                data['wind_gust'] = await cnv.speed(obs[6])
                data['wind_bearing_avg'] = obs[7]
                data['wind_direction_avg'] = await cnv.direction(obs[7])
                data['battery_sky'] = obs[8]
                data['solar_radiation'] = obs[10]
                data['precipitation_type'] = await cnv.rain_type(obs[12])
                client.publish(state_topic, json.dumps(data))
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
                data['rain_accumulated'] = await cnv.rain(obs[12])
                data['precipitation_type'] = await cnv.rain_type(obs[13])
                data['battery_sky'] = obs[16]
                client.publish(state_topic, json.dumps(data))
                state_topic = 'homeassistant/sensor/{}/obs_air/state'.format(DOMAIN)
                data = OrderedDict()
                data['station_pressure'] = await cnv.pressure(obs[6])
                data['air_temperature'] = await cnv.temperature(obs[7])
                data['relative_humidity'] = obs[8]
                data['lightning_strike_count'] = obs[15]
                data['lightning_strike_avg_distance'] = await cnv.distance(obs[14])
                data['sealevel_pressure'] = await cnv.pressure(obs[6] + (elevation / 9.2), 2)
                client.publish(state_topic, json.dumps(data))


async def setup_sensors(endpoint, mqtt_client, unit_system):
    """Setup the Sensors in Home Assistant."""

    # Get Hub Information
    while True:
        data, (host, port) = await endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")
        if msg_type == EVENT_HUB_STATUS:
            serial_number = json_response.get("serial_number")
            firmware = json_response.get("firmware_revision")
            uptime = json_response.get("uptime")
            break

    # Create the config for the Sensors
    units = SENSOR_UNIT_I if unit_system == UNITS_IMPERIAL else SENSOR_UNIT_M
    for sensor in WEATHERFLOW_SENSORS:
        _LOGGER.debug("SETTING UP %s SENSOR", sensor[SENSOR_NAME])
        state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, sensor[SENSOR_DEVICE])
        discovery_topic = 'homeassistant/sensor/{}/{}/config'.format(DOMAIN, sensor[SENSOR_ID])
        payload = OrderedDict()
        payload['name'] = "{} {}".format(DOMAIN_SHORT, sensor[SENSOR_NAME])
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
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)

#Main Program starts
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Program")