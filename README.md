# WeatherFlow to MQTT for Home Assistant

This project monitors the UDP socket (50222) from a WeatherFlow Hub, and publishes the data to a MQTT Server. Data is formatted in a way that, it supports the [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) format for Home Assistant, so a sensor will created for each entity that WeatherFlow sends out, if you have MQTT Discovery enabled.

Everything runs in a pre-build Docker Container, so installation is very simple, you only need Docker installed on a computer and a MQTT Server setup somewhere in your network. If you run the Supervised version of Home Assistant, MQTT is very easy to setup.

## Installation

- Ensure Docker is setup and running
- Ensure there is a MQTT Server available
- Open a Terminal on the Machine you want to run the Docker container on.
- Make a new Directory: `mkdir weatherflow2mqtt` (or some other name) and change to that directory.
- Copy the `config_example.yaml` file from this repo to that directory, and rename it to `config.yaml`.
- Edit `config.yaml` as described below in the Configuration section.
- Pull the docker image with this command: `docker pull ghcr.io/briis/hass-weatherflow2mqtt`
- Create the docker container. Replace TZ (Timezone) with your Time Zone. `docker create --name weatherflow2mqtt -e TZ=Europe/Copenhagen -v $(pwd):/usr/local/config -p 0.0.0.0:50222:50222/udp ghcr.io/briis/hass-weatherflow2mqtt` You might not need the 0.0.0.0 in front of port 50222, but if you run into IPv6 errors you can add this.
- Then finally start the Container with `docker start weatherflow2mqtt`

If everything is setup correctly with MQTT and Home Assistant, you should now start seeing the sensors show up in HA. Please note, it can take up to 1 min after startup, before all sensors are populated with data.

## Configuration

The `config.yaml` looks like the below:

```yaml
unit_system: "metric" #Use metric or imperial
rapid_wind_interval: 0
debug: "off"
station:
  elevation: 50
  host: "0.0.0.0"
  port: "50222"
mqtt:
  host: "YOUR_MQTT_IP_HERE"
  port: 1883
  username: "YOUR_MQTT_USERNAME"
  password: "YOUR_MQTT_PASSWORD"
  debug: "off" # on or off to enable mqtt debug
sensors:
```

Normally you would only have to change the MQTT settings to supply the address and credentials for your MQTT Server. But here is the complete walkthrough of the configuration settings:

- `unit_system`: Enter *imperial* or *metric* to decide what unit the data is delivered in
- `rapid_wind_interval`: The weather stations delivers wind speed and bearing every 2 seconds. If you don't want to update the HA sensors so often, you can set a number here (in seconds), for how often they are updated. Default is zero, which means the two sensors are updated everytime WeatherFlow sends new data
- `debug`: Set this to on, to get some more debugging messages in the Container log file
- `station elevation`: The elevation above sea level (in meters) four your weather station. Is used by the program for some of the derived sensors.
- `station host`: Unless you have a very special IP setup or the Weatherflow hub is on a different network, you should not change this
- `station port`: Weatherflow always broadcasts on port 50222/udp, so don't change this
- `mqtt host`: The IP address of your mqtt server
- `mqtt port`: The Port for your mqtt server - Standard is 1883
- `mqtt username`: The username used to connect to the mqtt server. Leave blank to use Anonymous connection
- `mqtt password`: The password used to connect to the mqtt server. Leave blank to use Anonymous connection
- `mqtt debug`: Set this to on, to get some more mqtt debugging messages in the Container log file
- `sensors`: Leave blank to setup All available sensors, or enter a list of sensor ID's to setup. See *Available Sensors* for a list of sensors.

## Available Sensors

Here is the list of sensors that the program generates

| Sensor ID   | Name   | Description   |
| --- | --- | --- |
| wind_speed | Wind Speed | Current measured Wind Speed
| wind_bearing | Wind Bearing | Current measured Wind bearing in degrees
| wind_direction | Wind Direction | Current measured Wind bearing as compass symbol
| station_pressure | Wind Direction |
| sealevel_pressure | Station Pressure |
| air_temperature | Temperature |
| relative_humidity | Humidity |
| lightning_strike_count | Lightning Strike Count |
| lightning_strike_avg_distance | Lightning Strike Avg Distance |
| battery_air | Battery AIR |
| lightning_strike_distance | Lightning Strike Distance |
| lightning_strike_energy | Lightning Strike Energy |
| illuminance | Illuminance |
| uv | UV Index |
| rain_accumulated | Rain Accumulated |
| wind_lull | Wind Lull |
| wind_speed_avg | Wind Speed Avg |
| wind_gust | Wind Gust |
| wind_bearing_avg | Wind Bearing Avg |
| wind_direction_avg | Wind Direction Avg |
| battery_sky | Battery SKY |
| solar_radiation | Solar Radiation |
| precipitation_type | Precipitation Type |
| rain_start_time | Rain Start Time |
| air_density | Air Density |
| dewpoint | Dew Point |
| rain_rate | Rain Rate |
| uptime | Uptime |
| feelslike | Feels Like Temperature |
