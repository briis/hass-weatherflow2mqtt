# WeatherFlow-2-MQTT for Home Assistant

This project monitors the UDP socket (50222) from a WeatherFlow Hub, and publishes the data to a MQTT Server. Data is formatted in a way that, it supports the [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) format for Home Assistant, so a sensor will created for each entity that WeatherFlow sends out, if you have MQTT Discovery enabled.

Everything runs in a pre-build Docker Container, so installation is very simple, you only need Docker installed on a computer and a MQTT Server setup somewhere in your network. If you run the Supervised version of Home Assistant, you will have easy access to both.ß

There is support for both the AIR & SKY devices and the TEMPEST device.

## TODO

This project is still very much in Beta, but the things that are there, work. I am currently working on or considering:

- As I don't have Access to a Tempest Unit, I have not tested this with this device type. If anyone does, please report back here in the Discussions or Issue Area.

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

```bash
docker run -d \
--name=weatherflow2mqtt --restart=unless-stopped \
-v $(pwd):/usr/local/config \
-p 0.0.0.0:50222:50222/udp \
-e TZ=Europe/Copenhagen \
-e TEMPEST_DEVICE=True \
-e UNIT_SYSTEM=metric \
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
ghcr.io/briis/hass-weatherflow2mqtt
```

### Docker Volume

`-v YOUR_STORAGE_AREA:/usr/local/config` Please replace YOUR_STORAGE_AREA with a directory where Docker will have read an write access. It is also in this directory that you must place the *config.yaml* file if you use this. Once the program runs two hidden files called `.storage.yaml` and `.lightning.data` will be created in this directory. These files are used to save some calculated values, and to ensure that you don't start from 0 if you have to restart Home Assistant or the container.

### Docker Environment Variables

A description of the Environment Variables available for this container. All of them have a default value, so you only need to add the onces where you want to change that.

- `TZ`: Set your local Timezone. It is important that you use the right timezone here, or else some of the calculations done by the container will not be correct. Default Timezone is *Europe/Copenhagen*
- `TEMPEST_DEVICE`: If you have a Tempest Weather Station set this to True. If False, the program will assume you have the older AIR and SKY units. Default is *True*
- `UNIT_SYSTEM`: Enter *imperial* or *metric*. This will determine the unit system used when displaying the values. Default is *metric*
- `RAPID_WIND_INTERVAL`: The weather stations delivers wind speed and bearing every 2 seconds. If you don't want to update the HA sensors so often, you can set a number here (in seconds), for how often they are updated. Default is *0*, which means data are updated when received from the station.
- `ELEVATION`: Set the hight above sea level for where the station is placed. This is used when calculating some of the sensor values. The value has to be in meters. Default is *0*
- `WF_HOST`: Unless you have a very special IP setup or the Weatherflow hub is on a different network, you should not change this. Default is *0.0.0.0*
- `WF_PORT`: Weatherflow always broadcasts on port 50222/udp, so don't change this. Default is *50222*
- `MQTT_HOST`: The IP address of your mqtt server. Even though you have the MQTT Server on the same machine as this Container, don't use `127.0.0.1` as this will resolve to an IP Address inside your container. Use the external IP Address. Default value is *127.0.0.1*
- `MQTT_PORT`: The Port for your mqtt server. Default value is *1883*
- `MQTT_USERNAME`: The username used to connect to the mqtt server. Leave blank to use Anonymous connection. Default value is *blank*
- `MQTT_PASSWORD`: The password used to connect to the mqtt server. Leave blank to use Anonymous connection. Default value is *blank*
- `MQTT_DEBUG`: Set this to True, to get some more mqtt debugging messages in the Container log file. Default value is *False*
- `DEBUG`: Set this to True to enable more debug data in the Container Log. Default is *False*
- `ADD_FORECAST`: Set this to True if you want to retrieve Forecast Data from WeatherFlow. If set to True, *STATION_ID* and *STATION_TOKEN* must be filled also. **NOTE** If this is enabled the component will access the Internet to get the Forecast data. Default value is *False*
- `STATION_ID`: Enter your Station ID for your WeatherFlow Station. Default value is *blank*.
- `STATION_TOKEN`: Enter your personal access Token to allow retrieval of data. If you don't have the token [login with your account](https://tempestwx.com/settings/tokens) and create the token. **NOTE** You must own a WeatherFlow station to get this token. Default value is *blank*
- `FORECAST_INTERVAL`: The interval in minutes, between updates of the Forecast data. Default value is *30* minutes.

## Available Sensors

Here is the list of sensors that the program generates. Calculated Sensor means, if No, then data comes directly from the Weather Station, if yes, it is a sensor that is derived from some of the other sensors. For a *copy ready* list se [further below](#sensor-structure)

| Sensor ID   | Name   | Description   | Calculated Sensor   |
| --- | --- | --- | --- |
| air_density | Air Density | The Air density | Yes
| air_temperature | Temperature | Outside Temperature | No
| battery | Battery SKY or TEMPEST | If this is a TEMPEST unit this is where the Voltage is displayed. Else it will be the Voltage of the SKY unit | No
| battery_air | Battery AIR | The voltage on the AIR unit (If present) | No
| dewpoint | Dew Point | Dewpoint in degrees | Yes
| feelslike | Feels Like Temperature | The apparent temperature, a mix of Heat Index and Wind Chill | Yes
| illuminance | Illuminance | How much the incident light illuminates the surface | No
| lightning_strike_count | Lightning Count (3 hours) | Number of lightning strikes the last 3 hours | Yes
| lightning_strike_count_today | Lightning Count (Today) | Number of lightning strikes current day | Yes
| lightning_strike_distance | Lightning Distance | Distance of the last strike | No
| lightning_strike_energy | Lightning Energy | Energy of the last strike | No
| lightning_strike_time | Last Lightning Time | When the last lightning strike occurred | Yes
| precipitation_type | Precipitation Type | Can be one of None, Rain or Hail | No
| rain_rate | Rain Rate | How much is it raining right now | Yes
| rain_start_time | Last Rain | When was the last time it rained | No
| rain_today | Rain Today | Total rain for the current day. (Reset at midnight) | Yes
| rain_yesterday | Rain Yesterday | Total rain for yesterday | Yes
| relative_humidity | Humidity | Relative Humidity | No
| sealevel_pressure | Station Pressure | Preasure measurement at Sea Level | Yes
| solar_radiation | Solar Radiation | Electromagnetic radiation emitted by the sun | No
| station_pressure | Wind Direction | Pressure measurement where the station is located | No
| uptime | Uptime | How long has the HUB been running | No
| uv | UV Index | The UV index | No
| wind_bearing | Wind Bearing | Current measured Wind bearing in degrees | No
| wind_bearing_avg | Wind Bearing Avg | The average wind bearing in degrees | No
| wind_direction | Wind Direction | Current measured Wind bearing as compass symbol | Yes
| wind_direction_avg | Wind Direction Avg | The average wind direction as a compass string | Yes
| wind_gust | Wind Gust | Highest wind speed for the last minute | No
| wind_lull | Wind Lull | Lowest wind for the last minute | No
| wind_speed | Wind Speed | Current measured Wind Speed | No
| wind_speed_avg | Wind Speed Avg | Average wind speed for the last minute | No
| weather | Weather | Only available if Forecast option is enabled. State will be current condition, and forecast data will be in the attributes. | No

### Sensor Structure

```yaml
sensors:
  - air_density
  - air_temperature
  - battery
  - battery_air
  - dewpoint
  - feelslike
  - illuminance
  - lightning_strike_count
  - lightning_strike_count_today
  - lightning_strike_distance
  - lightning_strike_energy
  - lightning_strike_time
  - precipitation_type
  - rain_rate
  - rain_start_time
  - rain_today
  - rain_yesterday
  - relative_humidity
  - sealevel_pressure
  - solar_radiation
  - station_pressure
  - uptime
  - uv
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

## Creating a Weather Entity

If you have enabled the *Forecast* option, then there is a possibility to create a Weather Entity, that can be used in all the different Lovelace Cards there is for *Weather*. We will do this by using the [Weather Template](https://www.home-assistant.io/integrations/weather.template/). The naming of the sensors might vary based on your configuration, so check that if it does not work.

Edit `configuration.yaml` and insert the following:

```yaml
weather:
  - platform: template
    name: My Local Weather
    condition_template: "{{ states('sensor.weather') }}"
    temperature_template: "{{ states('sensor.temperature') | float}}"
    humidity_template: "{{ states('sensor.humidity')| int }}"
    pressure_template: "{{ states('sensor.sea_level_pressure')| float }}"
    wind_speed_template: "{{ states('sensor.wind_speed_avg') | float * 18 / 5 | round(2) }}"
    wind_bearing_template: "{{ states('sensor.wind_bearing_avg')| int }}"
    forecast_template: "{{ states.sensor.weather.attributes.hourly_forecast }}"
```

- The weather entity expects km/h when having metric units, so the above example converts m/s to km/h. If you are unsing *imperial* units, the line should just be `{{ states('sensor.wind_speed_avg') }}`
- For the *forecast_template* you can either use `hourly_forecast` or `daily_forecast` to get Hourly or Day based forecast.
