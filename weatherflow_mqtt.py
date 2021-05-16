"""Program listening to the UDP Broadcast from
   a WeatherFlow Weather Station and publishing
   sensor data to MQTT.
"""

import json
from typing import OrderedDict
import paho.mqtt.client as mqtt
import asyncio
import logging
from datetime import datetime

from aioudp import open_local_endpoint
from const import (
    DOMAIN,
    DOMAIN_SHORT,
    EVENT_AIR_DATA,
    EVENT_DEVICE_STATUS,
    EVENT_RAPID_WIND,
    EVENT_HUB_STATUS,
    EVENT_PRECIP_START,
    EVENT_SKY_DATA,
    EVENT_STRIKE,
    EVENT_TEMPEST_DATA,
    SENSOR_CLASS,
    SENSOR_DEVICE,
    SENSOR_ID,
    SENSOR_NAME,
    SENSOR_UNIT,
    WEATHERFLOW_SENSORS,
)

_LOGGER = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.DEBUG)
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    #Read the settings.json file
    filepath = "/config/settings.json"
    # filepath = "settings.json"
    with open(filepath) as json_file:
        data = json.load(json_file)
        weatherflow_ip = data["weatherflow"]["host"]
        weatherflow_port = data["weatherflow"]["port"]
        mqtt_host = data["mqtt"]["host"]
        mqtt_port = data["mqtt"]["port"]
        mqtt_username = data["mqtt"]["username"]
        mqtt_password = data["mqtt"]["password"]
        mqtt_topic = data["mqtt"]["topic"]
        elevation = data["station"]["elevation"]

    #Setup and connect to MQTT Broker
    client =mqtt.Client("WFMQTT")
    client.username_pw_set(username=mqtt_username,password=mqtt_password)
    client.connect(mqtt_host, port=mqtt_port)
    client.publish(f"{mqtt_topic}/log",f"WE ARE CONNECTED TO MQTT at {current_time}")

    #Setup and start listening to WeatherFlow UDP Socket
    endpoint = await open_local_endpoint(host=weatherflow_ip, port=weatherflow_port)
    _LOGGER.debug("The UDP server is running on port %s...", endpoint.address[1])

    # Configure Sensors in MQTT
    await setup_sensors(endpoint, client)


    while True:
        data, (host, port) = await endpoint.receive()
        json_response = json.loads(data.decode("utf-8"))
        msg_type = json_response.get("type")

        #Process the data
        if msg_type is not None:
            data = OrderedDict()
            state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, msg_type)
            if msg_type in EVENT_RAPID_WIND:
                obs = json_response["ob"]
                data['wind_speed'] = obs[1]
                data['wind_bearing'] = obs[2]
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_STRIKE:
                obs = json_response["evt"]
                data['lightning_strike_distance'] = obs[1]
                data['lightning_strike_energy'] = obs[2]
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_AIR_DATA:
                obs = json_response["obs"][0]
                data['station_pressure'] = obs[1]
                data['air_temperature'] = obs[2]
                data['relative_humidity'] = obs[3]
                data['lightning_strike_count'] = obs[4]
                data['lightning_strike_avg_distance'] = obs[5]
                data['battery_air'] = obs[6]
                data['sealevel_pressure'] = round(obs[1] + (elevation / 9.2), 2)
                client.publish(state_topic, json.dumps(data))
            if msg_type in EVENT_SKY_DATA:
                obs = json_response["obs"][0]
                data['illuminance'] = obs[1]
                data['uv'] = obs[2]
                data['rain_accumulated'] = obs[3]
                data['wind_lull'] = obs[4]
                data['wind_speed_avg'] = obs[5]
                data['wind_gust'] = obs[6]
                data['wind_bearing_avg'] = obs[7]
                data['battery_sky'] = obs[8]
                data['solar_radiation'] = obs[10]
                data['local_day_rain_accumulation'] = obs[11]
                data['precipitation_type'] = obs[12]
                client.publish(state_topic, json.dumps(data))


async def setup_sensors(endpoint, mqtt_client):
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

    for sensor in WEATHERFLOW_SENSORS:
        _LOGGER.debug("SETTING UP %s SENSOR", sensor[SENSOR_NAME])
        state_topic = 'homeassistant/sensor/{}/{}/state'.format(DOMAIN, sensor[SENSOR_DEVICE])
        discovery_topic = 'homeassistant/sensor/{}/{}/config'.format(DOMAIN, sensor[SENSOR_ID])
        payload = OrderedDict()
        payload['name'] = "{} {}".format(DOMAIN_SHORT, sensor[SENSOR_NAME])
        payload['unique_id'] = "{}-{}".format(serial_number, sensor[SENSOR_ID])
        payload['unit_of_measurement'] = sensor[SENSOR_UNIT]
        if sensor[SENSOR_CLASS] is not None:
            payload['device_class'] = sensor[SENSOR_CLASS]
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
        mqtt_client.publish(discovery_topic, json.dumps(payload), 1, True)

#Main Program starts
if __name__ == "__main__":
    asyncio.run(main())
