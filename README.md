# WeatherFlow-2-MQTT for Home Assistant

![](https://img.shields.io/github/workflow/status/briis/hass-weatherflow2mqtt/publish?style=flat-square)  [![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=flat-square)](https://community.weatherflow.com/t/weatherflow2mqtt-for-home-assistant/13718)

This project monitors the UDP socket (50222) from a WeatherFlow Hub, and publishes the data to a MQTT Server. Data is formatted in a way that, it supports the [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) format for Home Assistant, so a sensor will created for each entity that WeatherFlow sends out, if you have MQTT Discovery enabled.

Everything runs in a pre-build Docker Container, so installation is very simple, you only need Docker installed on a computer and a MQTT Server setup somewhere in your network. If you run the Supervised version of Home Assistant, you will have easy access to both.ß

There is support for both the AIR & SKY devices and the TEMPEST device.

## Table of Contents

1. [Installation](#installation)
2. [Docker Setup](#docker-setup)
    1. [Docker Volume](#docker-volume)
    2. [Docker Environment Variables](#docker-environment-variables)
3. [Available Sensors](#available-sensors)
    1. [Sensor Structure](#sensor-structure)
    2. [High and Low Values](#high-and-low-values)
4. [Creating a Home Assistant Weather Entity](#creating-a-home-assistant-weather-entity)

## Installation

- Ensure Docker is setup and running
- Ensure there is a MQTT Server available
- Open a Terminal on the Machine you want to run the Docker container on.
- Make a new Directory: `mkdir weatherflow2mqtt` (or some other name) and change to that directory.
- If you **don't** want all sensors setup, copy the `config_example.yaml` file from this repo to that directory, and rename it to `config.yaml`. Then add or remove the sensors you want from the [available sensors list](#sensor-structure). If you don't do this, all sensors from the [Available Sensors](#available-sensors) will be added.
- Now start the Docker Container with the parameters described under [docker-setup](#docker-setup)

If everything is setup correctly with MQTT and Home Assistant, you should now start seeing the sensors show up in HA. **NOTE**, it can take up to 1 min after startup, before all sensors are populated with data.

## Docker Setup

The below command will pull the latest docker image and start WeatherFlow2MQTT for timezone Europe/Copenhagen and save data in the directory you are placed in when you launch the command. Ensure that you have replaced the Environment variables with your specific data. See description below.

If you are using docker-compose you can use the [docker-compose.yml](docker-compose.yml) file and make the modifications for your environment.  

```bash
docker run -d \
--name=weatherflow2mqtt --restart=unless-stopped \
-v $(pwd):/usr/local/config \
-p 0.0.0.0:50222:50222/udp \
-e TZ=Europe/Copenhagen \
-e TEMPEST_DEVICE=True \
-e UNIT_SYSTEM=metric \
-e LANGUAGE=en \
-e RAPID_WIND_INTERVAL=0 \
-e DEBUG=False \
-e ELEVATION=0 \
-e WF_HOST=0.0.0.0 \
-e WF_PORT=50222 \
-e MQTT_HOST=127.0.0.1 \
-e MQTT_PORT=1883 \
-e MQTT_USERNAME= \
-e MQTT_PASSWORD= \
-e MQTT_DEBUG=False \
-e ADD_FORECAST=False \
-e STATION_ID= \
-e STATION_TOKEN= \
-e FORECAST_INTERVAL=30 \
briis/weatherflow2mqtt:latest
```
The container is build for both Intel and ARM platforms, so it should work on most HW types. Please create an issue, if there is a platform for which it does not work.

### Docker Volume

`-v YOUR_STORAGE_AREA:/usr/local/config` Please replace YOUR_STORAGE_AREA with a directory where Docker will have read and write access. It is also in this directory that you must place the *config.yaml* file if you don't want all the sensors (See [Installation](#installation)). Once the program runs, a SQLite Database with the name `weatherflow2mqtt.db` will be created in this directory. This database is used to hold some calculated values, store temporary data used for calculations and to ensure that you don't start from 0 if you have to restart Home Assistant or the container.

### Docker Environment Variables

A description of the Environment Variables available for this container. All of them have a default value, so you only need to add the onces where you want to change that.

- `TZ`: Set your local Timezone. It is important that you use the right timezone here, or else some of the calculations done by the container will not be correct. Default Timezone is *Europe/Copenhagen* (**Required**)
- `TEMPEST_DEVICE`: If you have a Tempest Weather Station set this to True. If False, the program will assume you have the older AIR and SKY units. Default is *True*
- `UNIT_SYSTEM`: Enter *imperial* or *metric*. This will determine the unit system used when displaying the values. Default is *metric*
- `LANGUAGE`: Use this to set the language for Wind Direction cardinals and other sensors with text strings as state value. These strings will then be displayed in HA in the selected language. See section [Supported Languages](#supported-languages)
- `RAPID_WIND_INTERVAL`: The weather stations delivers wind speed and bearing every 2 seconds. If you don't want to update the HA sensors so often, you can set a number here (in seconds), for how often they are updated. Default is *0*, which means data are updated when received from the station.
- `ELEVATION`: Set the hight above sea level for where the station is placed. This is used when calculating some of the sensor values. Station elevation plus Device height above ground. The value has to be in meters (`meters = feet * 0.3048`). Default is *0*
- `WF_HOST`: Unless you have a very special IP setup or the Weatherflow hub is on a different network, you should not change this. Default is *0.0.0.0*
- `WF_PORT`: Weatherflow always broadcasts on port 50222/udp, so don't change this. Default is *50222*
- `MQTT_HOST`: The IP address of your mqtt server. Even though you have the MQTT Server on the same machine as this Container, don't use `127.0.0.1` as this will resolve to an IP Address inside your container. Use the external IP Address. Default value is *127.0.0.1* (**Required**)
- `MQTT_PORT`: The Port for your mqtt server. Default value is *1883*
- `MQTT_USERNAME`: The username used to connect to the mqtt server. Leave blank to use Anonymous connection. Default value is *blank*
- `MQTT_PASSWORD`: The password used to connect to the mqtt server. Leave blank to use Anonymous connection. Default value is *blank*
- `MQTT_DEBUG`: Set this to True, to get some more mqtt debugging messages in the Container log file. Default value is *False*
- `DEBUG`: Set this to True to enable more debug data in the Container Log. Default is *False*
- `ADD_FORECAST`: Set this to True if you want to retrieve Forecast Data from WeatherFlow. If set to True, *STATION_ID* and *STATION_TOKEN* must be filled also. **NOTE** If this is enabled the component will access the Internet to get the Forecast data. Default value is *False*
- `STATION_ID`: Enter your Station ID for your WeatherFlow Station. Default value is *blank*.
- `STATION_TOKEN`: Enter your personal access Token to allow retrieval of data. If you don't have the token [login with your account](https://tempestwx.com/settings/tokens) and create the token. **NOTE** You must own a WeatherFlow station to get this token. Default value is *blank*
- `FORECAST_INTERVAL`: The interval in minutes, between updates of the Forecast data. Default value is *30* minutes.

### Supported Languages

Currently these languages are supported for Wind Cardinals and other Text state strings:

- `en`: English
- `da`: Danish
- `fr`: French

If you would like to assist in translating to a new language, do the following:

- From the `translations` directory on this Github Project, download the file `en.json`
- Rename the file to `YourLanguageCode.json` - example for Spanish rename it to `es.json`
- Edit the file and translate the strings
- Make a pull request in Github and attach the file.

## Available Sensors

Here is the list of sensors that the program generates. Calculated Sensor means, if No, then data comes directly from the Weather Station, if yes, it is a sensor that is derived from some of the other sensors. For a *copy ready* list see [further below](#sensor-structure)

| Sensor ID   | Name   | Description   | Calculated Sensor   | Input (Tempest)  | Input (Air)   | Input (Sky)   | Default Units   
| --- | --- | --- | --- | --- | --- | --- | --- |
| air_density | Air Density | The Air density | Yes | obs[7], obs[6] | obs[2], obs[1] |  | kg/m^3 |
| air_temperature | Temperature | Outside Temperature | No | obs[7] | obs[2] |  | C° |
| battery | Battery SKY or TEMPEST | If this is a TEMPEST unit this is where the Voltage is displayed. Else it will be the Voltage of the SKY unit | No | obs[16] |  | obs[8] | Volts |
| battery_air | Battery AIR | The voltage on the AIR unit (If present) | No |  | obs[6] |  | Volts |
| beaufort | Beaufort Scale | Beaufort scale is an empirical measure that relates wind speed to observed conditions at sea or on land | Yes | obs[2] |  | obs[5] | # |
| delta_t | Delta T | Difference between Air Temperature and Wet Bulb Temperature | Yes | obs[7], obs[8], obs[6] | obs[2], obs[3], obs[1] |  | C° |
| dewpoint | Dew Point | Dewpoint in degrees | Yes | obs[7], obs[8] | obs{2], obs[3] |  | C° |
| dewpoint_description | Dewpoint Comfort Level | Textual representation of the Dewpoint value | Yes | dewpoint | dewpoint |  |  |
| feelslike | Feels Like Temperature | The apparent temperature, a mix of Heat Index and Wind Chill | Yes | obs[7], obs[8], wind_speed | obs[2], obs[3], wind_speed |  | C° |
| illuminance | Illuminance | How much the incident light illuminates the surface | No | obs[9] |  | obs[1] | Lux |
| lightning_strike_count | Lightning Count | Number of lightning strikes in the last minute | Yes | obs[15] | obs[4] |  | # |
| lightning_strike_count_1hr | Lightning Count (Last hour) | Number of lightning strikes during the last hour | Yes |  |  |  |  |
| lightning_strike_count_3hr | Lightning Count (3 hours) | Number of lightning strikes the last 3 hours | Yes |  |  |  |  |
| lightning_strike_count_today | Lightning Count (Today) | Number of lightning strikes current day | Yes |  |  |  |  |
| lightning_strike_distance | Lightning Distance | Distance of the last strike | No |  |  |  | km |
| lightning_strike_energy | Lightning Energy | Energy of the last strike | No |  |  |  |  |
| lightning_strike_time | Last Lightning Strike | When the last lightning strike occurred | Yes |  | seconds |  |  |
| precipitation_type | Precipitation Type | Can be one of None, Rain or Hail | No | obs[13] |  |  | 0 = none, 1 = rain, 2 = hail, 3 = rain + hail (heavy rain) |
| rain_rate | Rain Rate | How much is it raining right now | Yes | obs[12] |  | obs[3] | mm/h |
| rain_start_time | Last Rain | When was the last time it rained | No | rain_start |  | rain_start | seconds |
| rain_today | Rain Today | Total rain for the current day. (Reset at midnight) | Yes | rain_today |  | rain_today | mm |
| rain_yesterday | Rain Yesterday | Total rain for yesterday (Reset at midnight) | Yes | rain_yesterday |  | rain_yesterday | mm |
| rain_duration_today | Rain Duration (Today) | Total rain minutes for the current day. (Reset at midnight) | Yes | rain_duration_today |  | rain_duration_today | minutes |
| rain_duration_yesterday | Rain Duration (Yesterday) | Total rain minutes yesterday | Yes | rain_duration_yesterday |  | rain_duration_yesterday | minutes |
| relative_humidity | Humidity | Relative Humidity | No | obs[8] |  | obs[3] | % |
| sealevel_pressure | Station Pressure | Preasure measurement at Sea Level | Yes | obs[6], elevation | obs[1], elevation |  | MB |
| pressure_trend | Pressure Trend | Returns Steady, Falling or Rising determined by the rate of change over the past 3 hours| trend_text | trend_text |  |  | Yes |
| solar_radiation | Solar Radiation | Electromagnetic radiation emitted by the sun | No | obs[11] |  | obs[10] | W/m^2 |
| station_pressure | Station Pressure | Pressure measurement where the station is located | No | obs[6] | obs[1] |  | MB |
| temperature_description | Temperature Level | Textual representation of the Outside Air Temperature value | Yes | obs[7] | obs[2] |  | Text |
| uptime | Uptime | How long has the HUB been running | No | hub_status/uptime |  |  |  |
| uv | UV Index | The UV index | No | obs[10] |  | obs[2] | Index |
| uv_description | UV Level | Textual representation of the UV Index value | Yes | obs[10] |  |  | obs[2] |
| visibility | Visibility | Distance to the horizon | Yes | elevation, obs[7], obs[8] | elevation, obs[2], obs[3] |  | km |
| wetbulb | Wet Bulb Temperature | Temperature of a parcel of air cooled to saturation (100% relative humidity) | Yes | obs[7], obs[8], obs[6] | obs[2], obs[3], obs[1] |  | C° |
| wind_bearing | Wind Bearing | Current measured Wind bearing in degrees | No |  |  |  | Degrees |
| wind_bearing_avg | Wind Bearing Avg | The average wind bearing in degrees | No | obs[4] |  | obs[7] | Degrees |
| wind_direction | Wind Direction | Current measured Wind bearing as compass symbol | Yes |  |  |  | Cardinal |
| wind_direction_avg | Wind Direction Avg | The average wind direction as a compass string | Yes | obs[4] |  | obs[7] | Cardinal |
| wind_gust | Wind Gust | Highest wind speed for the last minute | No | obs[3] |  | obs[6] | m/s |
| wind_lull | Wind Lull | Lowest wind for the last minute | No | obs[1] |  | obs[4] | m/s |
| wind_speed | Wind Speed | Current measured Wind Speed | No |  |  |  | m/s |
| wind_speed_avg | Wind Speed Avg | Average wind speed for the last minute | No | obs[2] |  | obs[5] | m/s |
| weather | Weather | Only available if Forecast option is enabled. State will be current condition, and forecast data will be in the attributes. | No |  |  |  |  |

### Sensor Structure

```yaml
sensors:
  - air_density
  - air_temperature
  - battery
  - battery_air
  - beaufort
  - dewpoint
  - dewpoint_description
  - delta_t
  - feelslike
  - illuminance
  - lightning_strike_count
  - lightning_strike_count_1hr
  - lightning_strike_count_3hr
  - lightning_strike_count_today
  - lightning_strike_distance
  - lightning_strike_energy
  - lightning_strike_time
  - precipitation_type
  - pressure_trend
  - rain_rate
  - rain_start_time
  - rain_today
  - rain_yesterday
  - rain_duration_today
  - rain_duration_yesterday
  - relative_humidity
  - sealevel_pressure
  - solar_radiation
  - station_pressure
  - temperature_description
  - uptime
  - uv
  - uv_description
  - visibility
  - wetbulb
  - wind_bearing
  - wind_bearing_avg
  - wind_direction
  - wind_direction_avg
  - wind_gust
  - wind_lull
  - wind_speed
  - wind_speed_avg
  - weather
```

### High and Low Values

For selected sensors high and low values are calculated and published to the attributes of the sensor. Currently daily, monthly and all-time values are calculated, but future values are planned. Only the sensors where it is relevant, will get a low value calculated. See the table further down, for the available sensors and what values to expect.

Here are the current attributes, that will be applied to the selected sensor:

| Attribute Name   | Description   |
| --- | --- |
| `max_day` | Maximum value for the current day. Reset at midnight. |
| `max_day_time` | UTC time when the max value was recorded. Reset at midnight. |
| `min_day` | Minimum value for the current day. Reset at midnight. |
| `min_day_time` | UTC time when the min value was recorded. Reset at midnight. |
| `max_month` | Maximum value for the current month. Reset when new month. |
| `max_month_time` | UTC time when the max value was recorded. Reset when new month. |
| `min_month` | Minimum value for the current month. Reset when new month. |
| `min_month_time` | UTC time when the min value was recorded. Reset when new month. |
| `max_all` | Maximum value ever recorded. Updated at midnight every day. |
| `max_all_time` | UTC time when the all-time max value was recorded. Updated at midnight every day. |
| `min_all` | Minimum value ever recorded. Updated at midnight every day. |
| `min_all_time` | UTC time when the all-time min value was recorded. Updated at midnight every day. |

The following sensors are displaying High and Low values:

| Sensor ID   | High Value   | Low Value   |
| --- | --- | --- |
| `air_temperature` | Yes | Yes |
| `dewpoint` | Yes | Yes |
| `illuminance` | Yes | No |
| `lightning_strike_count_today` | Yes | No |
| `lightning_strike_energy` | Yes | No |
| `rain_rate` | Yes | No |
| `rain_duration_today` | Yes | No |
| `relative_humidity` | Yes | Yes |
| `sealevel_pressure` | Yes | Yes |
| `solar_radiation` | Yes | No |
| `uv` | Yes | No |
| `wind_gust` | Yes | No |
| `wind_lull` | Yes | No |
| `wind_speed_avg` | Yes | No |

## Creating a Home Assistant Weather Entity

If you have enabled the *Forecast* option, then there is a possibility to create a Weather Entity, that can be used in all the different Lovelace Cards there is for *Weather*. We will do this by using the [Weather Template](https://www.home-assistant.io/integrations/weather.template/). The naming of the sensors might vary based on your configuration, so check that if it does not work.

Edit `configuration.yaml` and insert the following:

```yaml
weather:
  - platform: template
    name: My Local Weather
    condition_template: "{{ states('sensor.wf_weather') }}"
    temperature_template: "{{ states('sensor.wf_temperature') | float}}"
    humidity_template: "{{ states('sensor.wf_humidity')| int }}"
    pressure_template: "{{ states('sensor.wf_sea_level_pressure')| float }}"
    wind_speed_template: "{{ ( states('sensor.wf_wind_speed_avg') | float * 18 / 5 ) | round(2) }}"
    wind_bearing_template: "{{ states('sensor.wf_wind_bearing_avg')| int }}"
    visibility_template: "{{ states('sensor.wf_visibility')| float }}"
    forecast_template: "{{ state_attr('sensor.wf_weather', 'hourly_forecast') }}"
```

- The weather entity expects km/h when having metric units, so the above example converts m/s to km/h. If you are using *imperial* units, the line should just be `{{ states('sensor.wf_wind_speed_avg') }}`
- For the *forecast_template* you can either use `hourly_forecast` or `daily_forecast` to get Hourly or Day based forecast.


## Setup Dev environment

```bash
virtualenv -p `which python3` env
source env/bin/activate
python setup.py install
```

Then you just need to export the configuration
```
export TZ="America/Toronto"
export TEMPEST_DEVICE="True"
export UNIT_SYSTEM="metric"
export LANGUAGE="en"
export RAPID_WIND_INTERVAL="0"
export DEBUG="True"
export EXTERNAL_DIRECTORY="."
export ELEVATION="30"
export WF_HOST="0.0.0.0"
export WF_PORT="50222"
export MQTT_HOST="..."
export MQTT_PORT="1883"
export MQTT_DEBUG="False"
export ADD_FORECAST="True"
export STATION_ID="..."
export STATION_TOKEN="..."
export FORECAST_INTERVAL="30"
export MQTT_USERNAME="..."
export MQTT_PASSWORD="..."
```

Then you can run the daemon with
```
weatherflow2mqt
```
