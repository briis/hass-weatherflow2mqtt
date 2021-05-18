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
- Create the docker container. Replace TZ (Timezone) with your Time Zone. `docker create --name weatherflow2mqtt -e TZ=Europe/Copenhagen -v $(pwd):/config -p 0.0.0.0:50222:50222/udp ghcr.io/briis/hass-weatherflow2mqtt` You might not need the 0.0.0.0 in front of port 50222, but if you run into IPv6 errors you can add this.
- Then finally start the Container with `docker start weatherflow2mqtt`

If everything is setup correctly with MQTT and Home Assistant, you should now start seeing the sensors show up in HA.

## Configuration

The `config.yaml` looks like the below:

```yaml
unit_system: "metric" #Use metric or imperial
rapid_wind_interval: 0
debug: "off"
weatherflow:
  host: "0.0.0.0"
  port: "50222"
mqtt:
  host: "YOUR_MQTT_IP_HERE"
  port: 1883
  username: "YOUR_MQTT_USERNAME"
  password: "YOUR_MQTT_PASSWORD"
  debug: "off" # on or off to enable mqtt debug
station:
  elevation: 50 # Station Elevation above sea level
```

Normally you would only have to change the MQTT settings to supply the address and credentials for your MQTT Server. But here is the complete walkthrough of the configuration settings:

- `unit_system`: Enter *imperial* or *metric* to decide what unit the data is delivered in
- `rapid_wind_interval`: The weather stations delivers wind speed and bearing every 2 seconds. If you don't want to update the HA sensors so often, you can set a number here (in seconds), for how often they are updated. Default is zero, which means the two sensors are updated everytime WeatherFlow sends new data
- `debug`: Set this to on, to get some more debugging messages in the Container log file
- `weatherflow host`: Unless you have a very special IP setup or the Weatherflow hub is on a different network, you should not change this
- `weatherflow port`: Weatherflow always broadcasts on port 50222/udp, so don't change this
- `mqtt host`: The IP address of your mqtt server
- `mqtt port`: The Port for your mqtt server - Standard is 1883
- `mqtt username`: The username used to connect to the mqtt server. Currently this does not support anonymous connections
- `mqtt password`: The password used to connect to the mqtt server
- `mqtt debug`: Set this to on, to get some more mqtt debugging messages in the Container log file
- `station elevation`: The elevation above sea level (in meters) four your weather station. Is used by the program for some of the derived sensors.

