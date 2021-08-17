# Home Assistant WeatherFlow2MQTT Changelog

## Version 2.0.17

**Release Date**: RELEASED WITH dev TAG

### Changes in release 2.0.17

`NEW`: Battery Percent sensors added. There will 2 new sensors if using AIR & SKY devices and 1 new if using the Tempest device. At the same time, the previous `battery` sensor name is now renamed to `voltage` as this is a more correct description of the value. Thanks to @GlennGoddard for creating the formula to do the conversion.
`NEW`: Wet Bulb Globe Temperature. The WetBulb Globe Temperature (WBGT) is a measure of the heat stress in direct sunlight. Thanks to @GlennGoddard for creating the formula

## Version 2.0.16

**Release Date**: August 9th, 2021

Just back from vacation, I release what was is done now. There are more requests, which will be added in the following days.

### Changes in release 2.0.16

`CHANGE`: Issue #60. Renamed the state for Rain to `heavy` from `heavy rain`.

`FIX`: Visibility calculation not working.

## Version 2.0.15

**Release Date**: August 9th, 2021

Just back from vacation, I release what was is done now. There are more requests, which will be added in the following days.

### Changes in release 2.0.15

`NEW`: **BREAKING CHANGE** 2 new Lightning sensors have been added, `lightning_strike_count_1hr` and `lightning_strike_count_3hr`. They represent the number of lightning strikes within the last hour and the last 3 hours. The 3 hour counter is in reality not new, as this was previously named `lightning_strike_count`, but has now been renamed. The `lightning_strike_count` now shows the number of lightning strikes in the last minute and can be used to give an indication of the severity of the thunderstorm.

`FIX`: Issue #51. Delta_T value was wrong when using `imperial` units. The fix applied in 2.0.14 was not correct, but hopefully this works now.

`NEW`: @crzykidd added a Docker Compose file, so if you are using Docker Compose, find the file `docker-compose.yml` and modify this with your own setup.

`CHANGE`: @GlennGoddard fintuned the visibility calculation, so that sensor is now more accurate, taking more parameters in to account.

## Version 2.0.14

**Release Date**: July 25th, 2021

### Changes in release 2.0.14

`FIX`: Issue #44. A user reported a wrong value for the Forecast Condition icon. It cannot be reproduced, but this version adds better error handling, and logging of the value that causes the error, should it occur again.

`FIX`: Issue #51. Delta_T value was wrong when using `imperial` units. Thanks to @GlennGoddard for spotting the issue, and suggesting the solution.

## Version 2.0.11

**Release Date**: July 23rd, 2021

### Changes in release 2.0.11

`FIX`: Visibility sensor caused a crash after 2.0.10, due to missing vars. This is now fixed.

## Version 2.0.10

**Release Date**: July 20th, 2021

### Changes in release 2.0.10

`CHANGE`: To support multi platform docker containers the new home for the container is on Docker Hub with the name **briis/weatherflow2mqtt**. This is where future upgrades will land. So please change your docker command to use this location. README file is updated with the location.
So please change your docker command to use this location. README file is updated with the location.
With this change, you should no longer have to build the container yourself if you run on a non-Intel HW platform like a Raspberry PI.
I recommend you delete the current container and image, and then re-load it using the new location.

`FIX`: Visibility sensor now takes in to account current weather conditions. Thanks to @GlennGoddard for making this change. Fixing issue #29

## Version 2.0.9

**Release Date**: July 6th, 2021

### Changes in release 2.0.9

`FIX`: Wetbulb Calculation crashed the system if one of the sensors had a NoneType value. Fixing issue #33

`NEW`: Added French Tranlation, thanks to @titilambert.

`FIX`: Issue #37, where the device status check could fail. thanks to @titilambert for fixing this.

## Version 2.0.8

**Release Date**: June 24th, 2021

### Changes in release 2.0.8

`FIX`: Wrong key in the Temperature Level description

## Version 2.0.7

**Release Date**: June 24th, 2021

### Changes in release 2.0.7

`NEW`: There is now multi language support for text states and other strings. Currently the support is limited to Danish (da) and English (en), and the default is English. In order to active another language than English add the following to the Docker Run command: `-e LANGUAGE=da`. If LANGUAGE is omitted, english will be used. So if this is the language you want, you don't have to do anything.  
If you want to help translate in to another language, go to Github and in the translations directory, download the `en.json` file, save it as `yourlanguagecode.json`, translate the strings, and make a pull request on Github.
`FIX`: `sensor.wf_dewpoint_comfort_level` was not showing the correct value when using Imperial Units.
`NEW`: A new sensor called `sensor.wf_beaufort_scale` is added. The Beaufort scale is an empirical measure that relates wind speed to observed conditions at sea or on land and holds a value between 0 and 12, where 0 is Calm and 12 is Hurricane force. The state holds the numeric value and there is an Attribute named `description` that holds the textual representation.

## Version 2.0.6

**Release Date**: June 23rd, 2021

### Changes in release 2.0.6

`FIX`: (Issue #28) The fix on release 2.0.5, was not completely solving the issue. Now a base Base value of Steady will be returned, if we are not able to calculate the Trend due to lack of data.
`NEW`: (Issue #29) Adding new sensor `sensor.wf_dewpoint_comfort_level` which gives a textual representation of the Dewpoint value.
`NEW`: (Issue #29) Adding new sensor `sensor.wf_temperature_level` which gives a textual representation of the Outside Air Temperature value.
`NEW`: (Issue #29) Adding new sensor `sensor.wf_uv_level` which gives a textual representation of the UV Index value.

## Version 2.0.5

**Release Date**: June 22nd, 2021

### Changes in release 2.0.5

`FIX`: (Issue #28) Sometimes the Pressure Trend calculation would get the program to crash due a timing in when data was logged by the system. With this fix, a `None` value will be returned instead.

## Version 2.0.4

**Release Date**: June 21st, 2021

### Changes in release 2.0.4

`NEW`: A new sensor called `wf_wet_bulb_temperature` has been added. This sensor returns the temperature of a parcel of air cooled to saturation (100% relative humidity)
`NEW`: A new sensor called `wf_delta_t` has been added. Delta T, is used in agriculture to indicate acceptable conditions for spraying pesticides and fertilizers. It is simply the difference between the air temperature (aka "dry bulb temperature") and the wet bulb temperature
`NEW`: Added monthly min and max values to selected sensors. **Note** Data will only be updated once a day, so first values will be shown after midnight after the upgrade and new Attributes will require a restart of HA before they appear.
`FIXED`: Daily Max value did not reset for some sensors at midnight.
`FIXED`: When using the WeatherFlow forecast, there could be a mismatch in the condition state.
`CHANGES`: Some *Under the Hood* changes to prepare for future enhancements.

| Attribute Name   | Description   |
| --- | --- |
| `max_month` | Maximum value for the current month. Reset when new month. |
| `max_month_time` | UTC time when the max value was recorded. Reset when new month. |
| `min_month` | Minimum value for the current month. Reset when new month. |
| `min_month_time` | UTC time when the min value was recorded. Reset when new month. |

## Version 2.0.3

**Release Date**: June 18th, 2021

### Changes in release 2.0.3

`NEW`: A new sensor called `wf_visibility`has been added. This sensor shows the distance to the horizon, in either km or nautical miles, depending on the unit_system.

## Version 2.0.2

**Release Date**: June 18th, 2021

### Changes in release 2.0.2

**Please make a backup of `weatherflow2mqtt.db` before upgrading. Just in case anything goes wrong.**

`FIX`: If the forecast data from WeatherFlow is not available, the program will now just skip the update, and wait for the next timely update, instead of crashing the Container.

`CHANGED`: Attributes for each sensors are now moved from the event topics, to each individual sensor, so that we can add sensor specific attributes. This will have no impact on a running system.

`NEW`: Started the work on creating Sensors for High and Low values. A new table is created and daily high/low will be calculated and written to this table. Currently only day high and low plus all-time high and low values are calculated. The values are written as attributes to each individual sensor where I believe it is relevant to have these values. **Note** It takes 10 min before the daily max and min values are shown, and all-time values are first shown the following day after upgrading, or on the first run of this program.

| Attribute Name   | Description   |
| --- | --- |
| `max_day` | Maximum value for the current day. Reset at midnight. |
| `max_day_time` | UTC time when the max value was recorded. Reset at midnight. |
| `min_day` | Minimum value for the current day. Reset at midnight. |
| `min_day_time` | UTC time when the min value was recorded. Reset at midnight. |
| `max_all` | Maximum value ever recorded. Updated at midnight every day. |
| `max_all_time` | UTC time when the all-time max value was recorded. Updated at midnight every day. |
| `min_all` | Minimum value ever recorded. Updated at midnight every day. |
| `min_all_time` | UTC time when the all-time min value was recorded. Updated at midnight every day. |

The following sensors are displaying Max and Min values:

| Sensor ID   | Max Value   | Min Value   |
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

## Version 2.0.1

**Release Date**: June 15th, 2021

### Changes in release 2.0.1

* `FIX`: Fixing the AIR Density value, when using Imperial Metrics

## Version 2.0.0

**Release Date**: June 15th, 2021

### Changes in release 2.0.0

* `NEW`: There is now a new sensor called `pressure_trend`. This sensor monitors the Sea Level pressure changes. The Pressure Trend state is determined by the rate of change over the past 3 hours. It can be one of the following: `Steady`, `Falling` and `Rising`. Please note we will need to gather 3 hours of data, before the returned value will be correct. Until then the value will be `Steady`.
* `NEW`: The simple storage system, that used two flat files, has now been rewritten, to use a SQLite Database instead. This will make future developments easier, and is also the foundation for the new Pressure Trend sensor. If you are already up and running with this program, your old data will automatically be migrated in to the new SQLite Database. And once you are confident that all is running, you can safely delete `.storage.json` and `.lightning.data`.
* `BREAKING CHANGE`: To better seperate the sensors created by this Integration from other Weather related sensors, this version now prefixes all sensor names with `wf_` and all Friendly Names with `WF`. As each sensor has a Unique ID that does not change, the sensors will keep the old Entity Id, and just change the name, and only the Friendly Name will change after this upgrade. But if you delete the Integration, and re-add it, then all the sensors will have the `wf_` as a prefix. The same goes for new sensors that might be added in the future. So if you want to avoid any future issues, I recommend deleting the `WeatherFlow2MQTT` device from the MQTT Integration, and then restart the Docker Container, to get all the sensors added again, with the new naming convention.
