# WeatherFlow to MQTT for Home Assistant

This project monitors the UDP socket (50222) from a WeatherFlow Hub, and publishes the data to a MQTT Server. Data is formatted in a way that, it supports the [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) format for Home Assistant, so a sensor will created for each entity that WeatherFlow sends out, if you have MQTT Discovery enabled.

Everything runs in a pre-build Docker Container, so installation is very simple, you only need Docker installed on a computer and a MQTT Server setup somewhere in your network. If you run the Supervised version of Home Assistant, MQTT is very easy to setup.

## TODO

This project is still very much in Beta, but the things that are there, work. I am currently working on or considering:

- Still need some work on the persistent storage, in order to ensure data is correct on restart, and also to have the possibility to do som calculation based sensors. Som is already working, some I am not too sure about yet.
- As I don't have Access to a Tempest Unit, I have not tested this with this device type. If anyone does, please report back here in the Discussions or Issue Area.
- I consider to also integrate the AI based Forecast from WeatherFlow. This will require some calls to their REST API, and as such this program will not be *Local Data* only. But if I do it, I will make it optional.

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

The `config.yaml` structure must look like the below:

```yaml
tempest_device: True
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

Normally you would only have to change the Unit System and MQTT settings to supply the address and credentials for your MQTT Server. But here is the complete walkthrough of the configuration settings:

- `tempest_device`: If you have the older devices AIR and SKY, set this setting to `False`.
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

Here is the list of sensors that the program generates. Calculated Sensor means, if No, then data comes directly from the Weather Station, if yes, it is a sensor that is derived from some of the other sensors.

| Sensor ID   | Name   | Description   | Calculated Sensor   |
| --- | --- | --- | --- |
| wind_speed | Wind Speed | Current measured Wind Speed | No
| wind_bearing | Wind Bearing | Current measured Wind bearing in degrees | No
| wind_direction | Wind Direction | Current measured Wind bearing as compass symbol | Yes
| station_pressure | Wind Direction | Pressure measurement where the station is located | No
| sealevel_pressure | Station Pressure | Preasure measurement at Sea Level | Yes
| air_temperature | Temperature | Outside Temperature | No
| relative_humidity | Humidity | Relative Humidity | No
| lightning_strike_count | Lightning Count (3 hours) | Number of lightning strikes the last 3 hours | Yes
| battery_air | Battery AIR | The voltage on the AIR unit (If present) | No
| lightning_strike_distance | Lightning Distance | Distance of the last strike | No
| lightning_strike_energy | Lightning Energy | Energy of the last strike | No
| lightning_strike_time | Last Lightning Time | When the last lightning strike occurred | Yes
| illuminance | Illuminance | How much the incident light illuminates the surface | No
| uv | UV Index | The UV index | No
| rain_accumulated | Rain Accumulated | Total rain for the current day. (Reset at midnight) | Yes
| wind_lull | Wind Lull | Lowest wind | No
| wind_speed_avg | Wind Speed Avg | Average wind speed for the last minute | No
| wind_gust | Wind Gust | Highest wind speed for the last minute | No
| wind_bearing_avg | Wind Bearing Avg | The average wind bearing in degrees | No
| wind_direction_avg | Wind Direction Avg | The average wind direction as a compass string | Yes
| battery | Battery SKY or TEMPEST | If this is a TEMPEST unit this where the Voltage is displayed. Else it will be the Voltage of the SKY unit | No
| solar_radiation | Solar Radiation | Electromagnetic radiation emitted by the sun | No
| precipitation_type | Precipitation Type | Can be one of None, Rain or Hail | No
| rain_start_time | Last Rain | When was the last time it rained | Yes
| air_density | Air Density | The Air density | Yes
| dewpoint | Dew Point | Dewpoint in degrees | Yes
| rain_rate | Rain Rate | How much is it raining right now | Yes
| uptime | Uptime | How long has the HUB been running | No
| feelslike | Feels Like Temperature | The experienced temperature, a mix of Heat Index and Wind Chill | Yes

```yaml
sensors:
  - wind_speed
  - wind_bearing
  - wind_direction
  - station_pressure
  - sealevel_pressure
  - air_temperature
  - relative_humidity
  - lightning_strike_count
  - battery_air
  - lightning_strike_distance
  - lightning_strike_energy
  - lightning_strike_time
  - illuminance
  - uv
  - rain_accumulated
  - wind_lull
  - wind_speed_avg
  - wind_gust
  - wind_bearing_avg
  - wind_direction_avg
  - battery
  - solar_radiation
  - precipitation_type
  - rain_start_time
  - air_density
  - dewpoint
  - rain_rate
  - uptime
  - feelslike
```
