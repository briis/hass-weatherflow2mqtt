# WeatherFlow-2-MQTT for Home Assistant

![](https://img.shields.io/docker/v/briis/weatherflow2mqtt/latest?style=flat-square) ![](https://img.shields.io/docker/pulls/briis/weatherflow2mqtt?style=flat-square) [![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=flat-square)](https://community.weatherflow.com/t/weatherflow2mqtt-for-home-assistant/13718) [![](https://img.shields.io/discord/918948431714738257)](https://discord.gg/n5nw8QXM8b)

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fbriis%2Fhass-weatherflow2mqtt)

This project monitors the UDP socket (50222) from a WeatherFlow Hub, and publishes the data to a MQTT Server. Data is formatted in a way that, it supports the [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) format for Home Assistant, so a sensor will created for each entity that WeatherFlow sends out, if you have MQTT Discovery enabled.

Everything runs in a pre-built Docker Container, so installation is very simple. You only need Docker installed on a computer and a MQTT Server setup somewhere in your network. If you run either the Operating System or Supervised installation of Home Assistant, you will have easy access to both.

There is support for both the AIR & SKY devices and the TEMPEST device.

Please review Breaking Changes prior to updating your instance. Breaking changes will be listed in https://github.com/briis/hass-weatherflow2mqtt/blob/main/CHANGELOG.md

## Table of Contents

1. [Installation](#installation)
2. [Docker Setup](#docker-setup)
   1. [Docker Volume](#docker-volume)
   2. [Docker Environment Variables](#docker-environment-variables)
3. [Available Sensors](#available-sensors)
   1. [Sensor Structure](#sensor-structure)
   2. [High and Low Values](#high-and-low-values)
   3. [Long Term Statistics](#Home-Assistant-Long-Term-Statistics)
   4. [Sensors in Developement](#Sensors-in-Developement)
4. [Creating a Home Assistant Weather Entity](#creating-a-home-assistant-weather-entity)
5. [Creating a Developement Environment](#Setup-Dev-environment)

## Installation

### Prerequisites

A MQTT Server must be setup and configured on your local network, before installing this component. If you run a *Supervised* Home Assistant installation, we recommend using the MQTT Add-On available for this, else you must set it up yourself. See more [here](https://www.eclipse.org/paho/) for installing MQTT.

### Home Assistant Supervised

This is the easiest installation method. Just click on the blue **ADD REPOSITORY** button at the top of this README and you will be taken to your Home Assistant instance to add this repository to the _Add-On Store_. From there, scroll down to find "WeatherFlow to MQTT" and then install, configure (optional) and start the add-on.

**NOTE**: Make sure that you already have setup a Working MQTT broker, and easiest way to do that is by using the MQTT broker from the Official Add-On store.

### Outside Home Assistant using Docker

- Ensure Docker is setup and running
- Ensure there is a MQTT Server available
- Open a Terminal on the Machine you want to run the Docker container on.
- Make a new Directory: `mkdir weatherflow2mqtt` (or some other name) and change to that directory.
- If you **don't** want all sensors setup, copy the `config_example_TEMPEST.yaml` or `config_example_AIR_SKY.yaml` file from this repo to that directory, and rename it to `config.yaml`. Then add or remove the sensors you want from the [available sensors list](#sensor-structure). If you don't do this, all sensors from the [Available Sensors](#available-sensors) will be added.
- Now start the Docker Container with the parameters described under [docker-setup](#docker-setup)

If everything is setup correctly with MQTT and Home Assistant, you should now start seeing the sensors show up in HA. **NOTE**, it can take up to 1 min after startup, before all sensors are populated with data.

## Docker Setup

The below command will pull the latest docker image and start WeatherFlow2MQTT for timezone Europe/Copenhagen and save data in the directory you are placed in when you launch the command. Ensure that you have replaced the Environment variables with your specific data. See description below.

If you are using docker-compose you can use the [docker-compose.yml](docker-compose.yml) file and make the modifications for your environment.

```bash
docker run -d \
--name=weatherflow2mqtt --restart=unless-stopped \
-v $(pwd):/data \
-p 0.0.0.0:50222:50222/udp \
-e TZ=Europe/Copenhagen \
-e UNIT_SYSTEM=metric \
-e LANGUAGE=en \
-e RAPID_WIND_INTERVAL=0 \
-e DEBUG=False \
-e ELEVATION=0 \
-e LATITUDE=00.0000 \
-e LONGITUDE=000.0000 \
-e ZAMBRETTI_MIN_PRESSURE=960 \
-e ZAMBRETTI_MAX_PRESSURE=1060 \
-e WF_HOST=0.0.0.0 \
-e WF_PORT=50222 \
-e MQTT_HOST=127.0.0.1 \
-e MQTT_PORT=1883 \
-e MQTT_USERNAME= \
-e MQTT_PASSWORD= \
-e MQTT_DEBUG=False \
-e STATION_ID= \
-e STATION_TOKEN= \
-e FORECAST_INTERVAL=30 \
briis/weatherflow2mqtt:latest
```

The container is build for both Intel and ARM platforms, so it should work on most HW types. Please create an issue, if there is a platform for which it does not work.

### Docker Volume

`-v YOUR_STORAGE_AREA:/data` Please replace _YOUR_STORAGE_AREA_ with a directory where Docker will have read and write access. Once the program runs, a SQLite Database with the name `weatherflow2mqtt.db` will be created in this directory. This database is used to hold some calculated values, store temporary data used for calculations and to ensure that you don't start from 0 if you have to restart Home Assistant or the container. This is also where you can place the `config.yaml` file if you don't want all the sensors (see [Installation](#installation)).

### Docker Environment Variables

A description of the Environment Variables available for this container. All of them have a default value, so you only need to add the onces where you want to change that.

- `TZ`: Set your local Timezone. It is important that you use the right timezone here, or else some of the calculations done by the container will not be correct. Default Timezone is _Europe/Copenhagen_ (**Required**)
- `UNIT_SYSTEM`: Enter _imperial_ or _metric_. This will determine the unit system used when displaying the values. Default is _metric_
- `LANGUAGE`: Use this to set the language for Wind Direction cardinals and other sensors with text strings as state value. These strings will then be displayed in HA in the selected language. See section [Supported Languages](#supported-languages)
- `RAPID_WIND_INTERVAL`: The weather stations delivers wind speed and bearing every 2 seconds. If you don't want to update the HA sensors so often, you can set a number here (in seconds), for how often they are updated. Default is _0_, which means data are updated when received from the station.
- `ELEVATION`: Set the hight above sea level for where the station is placed. This is used when calculating some of the sensor values. Station elevation plus Device height above ground. The value has to be in meters (`meters = feet * 0.3048`). Default is _0_
- `LATITUDE`: Set the Latitude where the Station is located. Default is _0.0000_.
- `LONGITUDE`: Set the Longitude where the Station is located. Default is _0.0000_.
- `ZAMBRETTI_MIN_PRESSURE`: All Time Low Sea Level Pressure. Default is _960_ (Mb for Metric) or Default is _28.35_ (inHG for Imperial)
- `ZAMBRETTI_MAX_PRESSURE`: All Time High Sea Level Pressure. Default is _1060_ (Mb for Metric) or Default is _31.30_ (inHG for Imperial)
- `WF_HOST`: Unless you have a very special IP setup or the Weatherflow hub is on a different network, you should not change this. Default is _0.0.0.0_
- `WF_PORT`: Weatherflow always broadcasts on port 50222/udp, so don't change this. Default is _50222_
- `MQTT_HOST`: The IP address of your mqtt server. Even though you have the MQTT Server on the same machine as this Container, don't use `127.0.0.1` as this will resolve to an IP Address inside your container. Use the external IP Address. Default value is _127.0.0.1_ (**Required**)
- `MQTT_PORT`: The Port for your mqtt server. Default value is _1883_
- `MQTT_USERNAME`: The username used to connect to the mqtt server. Leave blank to use Anonymous connection. Default value is _blank_
- `MQTT_PASSWORD`: The password used to connect to the mqtt server. Leave blank to use Anonymous connection. Default value is _blank_
- `MQTT_DEBUG`: Set this to True, to get some more mqtt debugging messages in the Container log file. Default value is _False_
- `DEBUG`: Set this to True to enable more debug data in the Container Log. Default is _False_
- `STATION_ID`: Enter your Station ID for your WeatherFlow Station. Default value is _blank_.
- `STATION_TOKEN`: Enter your personal access Token to allow retrieval of data. If you don't have the token [login with your account](https://tempestwx.com/settings/tokens) and create the token. **NOTE** You must own a WeatherFlow station to get this token. Default value is _blank_
- `FORECAST_INTERVAL`: The interval in minutes, between updates of the Forecast data. Default value is _30_ minutes.
- `briis/weatherflow2mqtt:<tag>`: _latest_ for the latest stable build, _dev_ for the latest build (may not be stable due to development/testing build). Once dev build is verified latest build and dev will be identical. Latest features will be tested in dev build before released to latest.

### Supported Languages

Currently these languages are supported for Wind Cardinals and other Text state strings:

- `en`: English
- `da`: Danish
- `de`: German
- `fr`: French

If you would like to assist in translating to a new language, do the following:

- From the `translations` directory on this Github Project, download the file `en.json`
- Rename the file to `YourLanguageCode.json` - example for Spanish rename it to `es.json`
- Edit the file and translate the strings
- Make a pull request in Github and attach the file.

## Available Sensors

Here is the list of sensors that the program generates. Calculated Sensor means, if No, then data comes directly from the Weather Station, if yes, it is a sensor that is derived from some of the other sensors. For a _copy ready_ list see [further below](#sensor-structure)

| Sensor ID                    | Name                        | Description                                                                                                                                                                                        | Calculated Sensor | Default Units                                                                                |
| ---------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------- |
| absolute_humidity            | Absolute Humidity           | The amount of water per volume of air                                                                                                                                                              | Yes               | g/m^3                                                                                        |
| air_density                  | Air Density                 | The Air density                                                                                                                                                                                    | Yes               | kg/m^3                                                                                       |
| air_temperature              | Temperature                 | Outside Temperature                                                                                                                                                                                | No                | C°                                                                                           |
| battery                      | Battery                     | The battery level on the sensor (If present)                                                                                                                                                       | Yes               | %                                                                                            |
| battery_mode                 | Battery Mode                | The battery operating mode on the TEMPEST unit (If present)                                                                                                                                        | Yes               | https://help.weatherflow.com/hc/en-us/articles/360048877194-Solar-Power-Rechargeable-Battery |
| beaufort                     | Beaufort Scale              | Beaufort scale is an empirical measure that relates wind speed to observed conditions at sea or on land                                                                                            | Yes               | #                                                                                            |
| cloud_base                   | Cloud Base Altitude         | The estimated altitude above mean sea level (AMSL) to the cloud base                                                                                                                               | Yes               | m                                                                                            |
| delta_t                      | Delta T                     | Difference between Air Temperature and Wet Bulb Temperature                                                                                                                                        | Yes               | C°                                                                                           |
| dewpoint                     | Dew Point                   | Dewpoint in degrees                                                                                                                                                                                | Yes               | C°                                                                                           |
| dewpoint_description         | Dewpoint Comfort Level      | Textual representation of the Dewpoint value                                                                                                                                                       | Yes               |                                                                                              |
| feelslike                    | Feels Like Temperature      | The apparent temperature, a mix of Heat Index and Wind Chill                                                                                                                                       | Yes               | C°                                                                                           |
| freezing_level               | Freezing Level Altitude     | The estimated altitude above mean sea level (AMSL) where the temperature is at the freezing point (0°C/32°F)                                                                                       | Yes               | m                                                                                            |
| illuminance                  | Illuminance                 | How much the incident light illuminates the surface                                                                                                                                                | No                | Lux                                                                                          |
| lightning_strike_count       | Lightning Count             | Number of lightning strikes in the last minute                                                                                                                                                     | Yes               | #                                                                                            |
| lightning_strike_count_1hr   | Lightning Count (Last hour) | Number of lightning strikes during the last hour                                                                                                                                                   | Yes               |                                                                                              |
| lightning_strike_count_3hr   | Lightning Count (3 hours)   | Number of lightning strikes the last 3 hours                                                                                                                                                       | Yes               |                                                                                              |
| lightning_strike_count_today | Lightning Count (Today)     | Number of lightning strikes current day                                                                                                                                                            | Yes               |                                                                                              |
| lightning_strike_distance    | Lightning Distance          | Distance of the last strike                                                                                                                                                                        | No                | km                                                                                           |
| lightning_strike_energy      | Lightning Energy            | Energy of the last strike                                                                                                                                                                          | No                |                                                                                              |
| lightning_strike_time        | Last Lightning Strike       | When the last lightning strike occurred                                                                                                                                                            | Yes               |                                                                                              |
| precipitation_type           | Precipitation Type          | Can be one of None, Rain or Hail                                                                                                                                                                   | No                | 0 = none, 1 = rain, 2 = hail, 3 = rain + hail (heavy rain)                                   |
| pressure_trend               | Pressure Trend              | Returns Steady, Falling or Rising determined by the rate of change over the past 3 hours                                                                                                           | Yes               | trend_text                                                                                   |
| rain_intensity               | Rain Intensity              | A descriptive text of how much is it raining right now                                                                                                                                             | Yes               |                                                                                              |
| rain_rate                    | Rain Rate                   | How much is it raining right now                                                                                                                                                                   | Yes               | mm/h                                                                                         |
| rain_start_time              | Last Rain                   | When was the last time it rained                                                                                                                                                                   | No                | seconds                                                                                      |
| rain_today                   | Rain Today                  | Total rain for the current day. (Reset at midnight)                                                                                                                                                | Yes               | mm                                                                                           |
| rain_yesterday               | Rain Yesterday              | Total rain for yesterday (Reset at midnight)                                                                                                                                                       | Yes               | mm                                                                                           |
| rain_duration_today          | Rain Duration (Today)       | Total rain minutes for the current day. (Reset at midnight)                                                                                                                                        | Yes               | minutes                                                                                      |
| rain_duration_yesterday      | Rain Duration (Yesterday)   | Total rain minutes yesterday                                                                                                                                                                       | Yes               | minutes                                                                                      |
| relative_humidity            | Humidity                    | Relative Humidity                                                                                                                                                                                  | No                | %                                                                                            |
| sealevel_pressure            | Station Pressure            | Preasure measurement at Sea Level                                                                                                                                                                  | Yes               | MB                                                                                           |
| status                       | Status                      | How long has the device been running and other HW details                                                                                                                                          | No                |                                                                                              |
| solar_elevation              | Solar Elevation             | Sun Elevation in Degrees with respect to the Horizon                                                                                                                                                       | Yes                | ° (degree)                                                                                       |
| solar_insolation              | Solar Insolation           | Estimation of Solar Radiation at current sun elevation angle                                                                                                                                                       | Yes                | W/m^2                                                                                       |
| solar_radiation              | Solar Radiation             | Electromagnetic radiation emitted by the sun                                                                                                                                                       | No                | W/m^2                                                                                        |
| station_pressure             | Station Pressure            | Pressure measurement where the station is located                                                                                                                                                  | No                | MB                                                                                           |
| status                       | Status                      | How long has the device been running and other HW details                                                                                                                                          | No                |                                                                                              |
| temperature_description      | Temperature Level           | Textual representation of the Outside Air Temperature value                                                                                                                                        | Yes               | Text                                                                                         |
| uv                           | UV Index                    | The UV index                                                                                                                                                                                       | No                | Index                                                                                        |
| uv_description               | UV Level                    | Textual representation of the UV Index value                                                                                                                                                       | Yes               |                                                                                              |
| visibility                   | Visibility                  | Distance to the horizon                                                                                                                                                                            | Yes               | km                                                                                           |
| voltage                      | Voltage                     | The voltage on the sensor (If present)                                                                                                                                                             | No                | Volts                                                                                        |
| wetbulb                      | Wet Bulb Temperature        | Temperature of a parcel of air cooled to saturation (100% relative humidity)                                                                                                                       | Yes               | C°                                                                                           |
| wet_bulb_globe_temperature   | Wet Bulb Globe Temperature  | The WetBulb Globe Temperature (WBGT) is a measure of the heat stress in direct sunlight, which takes into account: temperature, humidity, wind speed, sun angle and cloud cover (solar radiation). | Yes               | C°                                                                                           |
| wind_bearing                 | Wind Bearing                | Current measured Wind bearing in degrees                                                                                                                                                           | No                | Degrees                                                                                      |
| wind_bearing_avg             | Wind Bearing Avg            | The average wind bearing in degrees                                                                                                                                                                | No                | Degrees                                                                                      |
| wind_direction               | Wind Direction              | Current measured Wind bearing as compass symbol                                                                                                                                                    | Yes               | Cardinal                                                                                     |
| wind_direction_avg           | Wind Direction Avg          | The average wind direction as a compass string                                                                                                                                                     | Yes               | Cardinal                                                                                     |
| wind_gust                    | Wind Gust                   | Highest wind speed for the last minute                                                                                                                                                             | No                | m/s                                                                                          |
| wind_lull                    | Wind Lull                   | Lowest wind for the last minute                                                                                                                                                                    | No                | m/s                                                                                          |
| wind_speed                   | Wind Speed                  | Current measured Wind Speed                                                                                                                                                                        | No                | m/s                                                                                          |
| wind_speed_avg               | Wind Speed Avg              | Average wind speed for the last minute                                                                                                                                                             | No                | m/s                                                                                          |
| weather                      | Weather                     | Only available if STATION_ID and STATION_TOKEN have valid data (See above). State will be current condition, and forecast data will be in the attributes.                                          | No                |                                                                                              |
| zambretti_number             | Zambretti Number            | Local Weather Forecast for the near future utilizing the Beteljuice Zambretti Algorhithm.                                                                                                           | Yes               | (0-25) number corresponds to Zambretti letters A-Z                                            |
| zambretti_text               | Zambretti Text                     | Local Weather Forecast for the near future utilizing the Beteljuice Zambretti Algorhithm.                                                                                                   | Yes               | Weather Forecast Text                                                                        |

### Sensor Structure

See [Available Sensors](#available-sensors) above for a description of each sensor.

```yaml
sensors:
  - absolute_humidity
  - air_density
  - air_temperature
  - battery # voltage
  - battery_mode # support for Tempest devices only
  - beaufort
  - cloud_base
  - delta_t
  - dewpoint
  - dewpoint_description
  - feelslike
  - freezing_level
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
  - rain_intensity
  - rain_rate
  - rain_start_time
  - rain_today
  - rain_yesterday
  - rain_duration_today
  - rain_duration_yesterday
  - relative_humidity
  - sealevel_pressure
  - solar_elevation
  - solar_insolation
  - solar_radiation
  - station_pressure
  - status
  - temperature_description
  - uv
  - uv_description
  - visibility
  - voltage
  - wbgt #Wet Bulb Globe Temperature
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
  - zambretti_number
  - zambretti_text
```

### High and Low Values

For selected sensors high and low values are calculated and published to the attributes of the sensor. Currently daily, monthly and all-time values are calculated, but future values are planned. Only the sensors where it is relevant, will get a low value calculated. See the table further down, for the available sensors and what values to expect.

Here are the current attributes, that will be applied to the selected sensor:

| Attribute Name   | Description                                                                       |
| ---------------- | --------------------------------------------------------------------------------- |
| `max_day`        | Maximum value for the current day. Reset at midnight.                             |
| `max_day_time`   | UTC time when the max value was recorded. Reset at midnight.                      |
| `min_day`        | Minimum value for the current day. Reset at midnight.                             |
| `min_day_time`   | UTC time when the min value was recorded. Reset at midnight.                      |
| `max_month`      | Maximum value for the current month. Reset when new month.                        |
| `max_month_time` | UTC time when the max value was recorded. Reset when new month.                   |
| `min_month`      | Minimum value for the current month. Reset when new month.                        |
| `min_month_time` | UTC time when the min value was recorded. Reset when new month.                   |
| `max_all`        | Maximum value ever recorded. Updated at midnight every day.                       |
| `max_all_time`   | UTC time when the all-time max value was recorded. Updated at midnight every day. |
| `min_all`        | Minimum value ever recorded. Updated at midnight every day.                       |
| `min_all_time`   | UTC time when the all-time min value was recorded. Updated at midnight every day. |

The following sensors are displaying High and Low values:

| Sensor ID                      | High Value | Low Value |
| ------------------------------ | ---------- | --------- |
| `air_temperature`              | Yes        | Yes       |
| `dewpoint`                     | Yes        | Yes       |
| `illuminance`                  | Yes        | No        |
| `lightning_strike_count_today` | Yes        | No        |
| `lightning_strike_energy`      | Yes        | No        |
| `rain_rate`                    | Yes        | No        |
| `rain_duration_today`          | Yes        | No        |
| `relative_humidity`            | Yes        | Yes       |
| `sealevel_pressure`            | Yes        | Yes       |
| `solar_radiation`              | Yes        | No        |
| `uv`                           | Yes        | No        |
| `wind_gust`                    | Yes        | No        |
| `wind_lull`                    | Yes        | No        |
| `wind_speed_avg`               | Yes        | No        |

### Home Assistant Long Term Statistics

These sensors have long term statistics (LTS) enabled in Home Assistant (HA), no action by user is required to have LTS collected by HA this is done with MQTT autodiscovery. To display LTS in HA using the Statistics Graph Card (type: statistics-graph) the 'stat types' that can be used with this integration are Mean, Min, and Max. It is the user's discreation as to how to display the information, but cases such as rain today 'Max' would be a more logical selection without 'Mean' or 'Min'. During testing there has not been a use case for this integration that 'Sum' was of any valid use. Air, Sky, and Tempest sensors are specific to those units.

https://data.home-assistant.io/docs/statistics/

```yaml
air_density
battery
beaufort
delta_t
dewpoint
feelslike
relative_humidity
illuminance
lightning_strike_count_today
lightning_strike_distance
lightning_strike_energy
rain_duration_today
rain_rate
rain_today
sealevel_pressure
solar_elevation
solar_insolation
solar_radiation
station_pressure
air_temperature
uv
visibility
voltage
wet_bulb_globe_temperature
wetbulb
wind_bearing
wind_bearing_avg
wind_gust
wind_lull
wind_speed
wind_speed_avg
```

### Sensors in Developement

```
Local Current Conditions
Probability of Snow
Probability of Fog
```

## Creating a Home Assistant Weather Entity

If you have enabled the _Forecast_ option, then there is a possibility to create a Weather Entity that can be used in all the different Lovelace Cards available for _Weather_. You can do this by using the [Weather Template](https://www.home-assistant.io/integrations/weather.template/).

Edit `configuration.yaml` and insert the following (replacing `hub_hb_00000001` and `tempest_st_00000001` with the appropriate ids of your sensors):

```yaml
weather:
  - platform: template
    name: My Local Weather
    condition_template: "{{ states('sensor.hub_hb_00000001_weather') }}"
    temperature_template: "{{ states('sensor.tempest_st_00000001_temperature') | float}}"
    humidity_template: "{{ states('sensor.tempest_st_00000001_humidity')| int }}"
    pressure_template: "{{ states('sensor.tempest_st_00000001_sea_level_pressure')| float }}"
    wind_speed_template: "{{ ( states('sensor.tempest_st_00000001_wind_speed_avg') | float * 18 / 5 ) | round(2) }}"
    wind_bearing_template: "{{ states('sensor.tempest_st_00000001_wind_bearing_avg')| int }}"
    visibility_template: "{{ states('sensor.tempest_st_00000001_visibility')| float }}"
    forecast_template: "{{ state_attr('sensor.hub_hb_00000001_weather', 'hourly_forecast') }}"
```

- The weather entity expects km/h when using metric units, so the above example converts m/s to km/h. If you are using _imperial_ units, the line should just be `{{ states('sensor.tempest_st_00000001_wind_speed_avg') }}`, again replacing `tempest_st_00000001` with the appropriate id of your sensor
- For the _forecast_template_ you can either use `hourly_forecast` or `daily_forecast` to get Hourly or Day based forecast.

## Setup Dev environment

```bash
virtualenv -p `which python3` env
source env/bin/activate
python setup.py install
```

Then you just need to export the configuration

```
export TZ="America/Toronto"
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
export STATION_ID="..."
export STATION_TOKEN="..."
export FORECAST_INTERVAL="30"
export MQTT_USERNAME="..."
export MQTT_PASSWORD="..."
```

Then you can run the daemon with

```bash
weatherflow2mqtt
```
