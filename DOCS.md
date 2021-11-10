# Home Assistant Community Add-on: WeatherFlow2MQTT

This add-on allows you to get data from a WeatherFlow weather station using UDP. There is support for both the new Tempest station and the older AIR & SKY station.

**Important**: this add-on uses the same timezone as your Home Assistant instance, so make sure it has been properly set.

## Installation

To install the add-on, first follow the installation steps from the [README on GitHub](https://github.com/briis/hass-weatherflow2mqtt/blob/main/README.md).

## Configuration

### Option: `TEMPEST_DEVICE`: (default: True)

If you have a Tempest Weather Station set this to True. If False, the program will assume you have the older AIR and SKY units. Default is *True*
### Option: `FILTER_SENSORS`: (default: None)

A comma-separated list of sensors to include instead of loading all sensors. Default is _None_, which disables filtering such that all sensors are loaded.

### Option: `INVERT_FILTER`: (default: False)

If set to True, `FILTER_SENSORS` will be treated as an exclusion list such that the specified sensors are ignored. Default is _False_.

### Option: `UNIT_SYSTEM`: (default: Same as Home Assistant)

Select *imperial* or *metric*. This will determine the unit system used when displaying the values. Default is *metric*

### Option: `LANGUAGE`: (default: en)

Use this to set the language for Wind Direction cardinals and other sensors with text strings as state value. These strings will then be displayed in HA in the selected language.

### Option: `RAPID_WIND_INTERVAL`: (default: 0)

The weather stations delivers wind speed and bearing every 2 seconds. If you don't want to update the HA sensors so often, you can set a number here (in seconds), for how often they are updated. Default is *0*, which means data are updated when received from the station.

### Option: `ELEVATION`: (default: 0)

Set the hight above sea level for where the station is placed. This is used when calculating some of the sensor values. Station elevation plus Device height above ground. The value has to be in meters (`meters = feet * 0.3048`). Default is *0*

### Option: `WF_HOST`: (default: 0.0.0.0)

Unless you have a very special IP setup or the Weatherflow hub is on a different network, you should not change this. Default is *0.0.0.0*

### Option: `WF_PORT`: (default: 50222)

Weatherflow always broadcasts on port 50222/udp, so don't change this. Default is *50222*

### Option: `MQTT_HOST`: (default: Installed MQTT Add-On IP)

The IP address of your mqtt server. Even though you have the MQTT Server on the same machine as this Container, don't use `127.0.0.1` as this will resolve to an IP Address inside your container. Use the external IP Address.

### Option: `MQTT_PORT`: (default: 1883)

The Port for your mqtt server. Default value is *1883*

### Option: `MQTT_USERNAME`: (default: Installed MQTT Add-On username)

The username used to connect to the mqtt server. Leave blank to use Anonymous connection.

### Option: `MQTT_PASSWORD`: (default: Installed MQTT Add-On password)

The password used to connect to the mqtt server. Leave blank to use Anonymous connection.

### Option: `MQTT_DEBUG`: (default: False)

Set this to True, to get some more mqtt debugging messages in the Container log file.

### Option: `DEBUG`: (default: False)

Set this to True to enable more debug data in the Container Log.

### Option: `ADD_FORECAST`: (default: False)

Set this to True if you want to retrieve Forecast Data from WeatherFlow. If set to True, *STATION_ID* and *STATION_TOKEN* must be filled also. **NOTE** If this is enabled the component will access the Internet to get the Forecast data.

### Option: `STATION_ID`: (default: None)

Enter your Station ID for your WeatherFlow Station.

### Option: `STATION_TOKEN`: (default: None)

Enter your personal access Token to allow retrieval of data. If you don't have the token [login with your account](https://tempestwx.com/settings/tokens) and create the token. **NOTE** You must own a WeatherFlow station to get this token.

### Option: `FORECAST_INTERVAL`: (default: 30)

The interval in minutes, between updates of the Forecast data.

## Authors & contributors

The original setup of this repository is by [Bjarne Riis](https://github.com/briis).

For a full list of all authors and contributors, check the [contributor's page](https://github.com/briis/hass-weatherflow2mqtt/graphs/contributors).
