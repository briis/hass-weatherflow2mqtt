# Change Log
All notable changes to this project will be documented in this file.


## [3.1.6] - 2023-01-08

### Fixed

- Fixed the Tempest battery % calculation to show a more accurate calculation.

## [3.1.4] - 2022-12-29

### Added

- Added new sensor `fog_probability` which returns the probability for fog based on current conditions. Thanks to @GlennGoddard for creating the formula.
- Added new sensor `snow_probability` which returns the probability of snow based on current conditions. Thanks to @GlennGoddard for creating the formula.
- Added new version attribute to the `sensor.hub_SERIAL_NUMBER_status`. This attribute will always hold the current version of the Docker Container.

### Changed

- Updated the French Translations. Thank you @MichelJourdain
- Issue #194. Adjusted Tempest minimum battery level to 2.11 V. The specs say that min is 1.8 V but experience show that below 2.11 the Tempest device does not work. So battery percent will now use this new min value.

## [3.1.3] - 2022-08-20

### Added

- Added support for the Dutch Language. Big thanks to @vdbrink for adding this.

### Changed

- Updated README to clarify how to get Station ID.

## [3.1.1] - 2022-07-12

### Fixed

- Fixed Issue #163 Bumped `pyweatherflowudp` to V1.4.1. Thank you to @natekspencer.
  - Adjusted logic for calculate_sea_level_pressure to match WeatherFlow (https://weatherflow.github.io/Tempest/api/derived-metric-formulas.html#sea-level-pressure)

## [3.1.0] - 2022-07-03

### Changed

- Bumped `pyweatherflowudp` to V1.4.0. Thank you to @natekspencer for keeping this module in good shape.
  - Adjusted logic for `wind_direction` and `wind_direction_cardinal` to report based on the last wind event or observation, whichever is most recent (similar to `wind_speed`)
  - Added properties for `wind_direction_average` and `wind_direction_average_cardinal` to report only on the average wind direction
  - Handle UnicodeDecodeError during message processing
  - Bump Pint to ^0.19
- Bumped Docker image to `python:3.10-slim-buster`, to get on par with Home Assistant.

  **Breaking Changes**:

  - The properties `wind_direction` and `wind_direction_cardinal` now report based on the last wind event or observation, whichever is most recent. If you want the wind direction average (previous logic), please use the properties `wind_direction_average` and `wind_direction_average_cardinal`, respectively
  - The default symbol for `rain_rate` is now `mm/h` instead of `mm/hr` due to Pint 0.19 - https://github.com/hgrecco/pint/pull/1454

### Added

- Added new sensor `solar_elevation` which returns Sun Elevation in Degrees with respect to the Horizon. Thanks to @GlennGoddard for creating the formula.
  **NOTE**: If you are not running this module as a HASS Add-On, you must ensure that environment variables `LATITUDE` and `LONGITUDE` are set in the Docker Startup command, as these values are used to calculate this value.
- Added new sensor `solar_insolation` which returns Estimation of Solar Radiation at current sun elevation angle. Thanks to @GlennGoddard for creating the formula.
- Added new sensors `zambretti_number` and `zambretti_text`, which are sensors that uses local data to create Weather Forecast for the near future. In order to optimize the forecast, these values need the *All Time High and Low Sea Level Presurre*. Per default these are set to 960Mb for Low and 1050Mb for High when using Metric units - 28.35inHg and 31.30inHg when using Imperial units. They can be changed by adding the Environment Variables `ZAMBRETTI_MIN_PRESSURE` and `ZAMBRETTI_MAX_PRESSURE` to the Docker Start command. Thanks to @GlennGoddard for creating the formula and help with all the testing on this.

## [3.0.8] - 2022-06-06

### Fixed

- BUGFIX: Changed spelling error in `en.json` file. Tnanks to @jazzyisj
- BUGFIX: Bump `pyweatherflowudp` to V1.3.1 to handle `up_since` oscillation on devices

### Added

- NEW: Added Latitude and Longitude environment variables. These will be used in later additions for new calculated sensors. If you run the Supervised Add-On, then these will be provided automatically by Home Assistent. If you run a standalone docker container, you must add: `-e LATITUDE=your_latiude e- LONGITUDE=your_longitude` to the Docker startup command.


## [3.0.7] - 2022-01-12

### Fixed

- BUGFIX: Don't add battery mode sensor for Air/Sky devices. If the sensor was already created, you will have to delete it manually in MQTT.
- BUGFIX: In rare occasions the forecast icon is not present in data supplied from WeatherFlow. Will now be set to *Cloudy* as default.

## [3.0.6] - 2021-12-30

### Fixed

- BUGFIX: Handle MQTT qos>0 messages appropriately by calling loop_start() on the MQTT client
  - See https://github.com/eclipse/paho.mqtt.python#client
  - Fixing Issue #46.

## [3.0.5] - 2021-12-24

### Changes

- Add cloud base altitude and freezing level altitude sensors
- Migrate sea level pressure sensor to use the pyweatherflowudp calculation
- Bump pyweatherflowudp to 1.3.0

## [3.0.4] - 2021-12-22

### Changes

- Add a debug log when updating forecast data and set qos=1 to ensure delivery
- Add another debug log to indicate next forecast update
- Docker container is now using the `slim-buster` version of Ubuntu instead of the full version, reducing the size of the Container to one third of the original size.


## [3.0.3] - 2021-12-15

### Changes

- Add discord link to README
- Remove obsolete references to obs[] data points

### Fixed

- Handle timestamps in their own event so they are only updated when a value exists. Fixing #117
- Fix high/low update

## [3.0.2] - 2021-12-11

### Changes

- Uses rain_rate from the pyweatherflowudp package now that it is available. This should solve an issue with Heavy Rain #100 where, when on imperial, rain rate was first converted to in/hr but then passed to rain intensity which is based on a mm/hr rate
- Sends the forecast data to MQTT with a retain=True value so that it can be restored on a Home Assistant restart instead of waiting for the next forecast update
- Reduces the loops for setting up the hub sensor by separating device and hub sensors
- Handles unknown timestamps for last lightning/rain so that it shows up as "Unknown" instead of "52 years ago" when there is no value
- Changes the number of Decimal places for Air Density to 5.


## [3.0.1] - 2021-12-10

### Fixed

- Issue #109. Adding better handling of missing data points when parsing messages which may occure when the firmware revision changes, to ensure the program keeps running.

## [3.0.0] - 2021-12-10

This is the first part of a major re-write of this Add-On. Please note **this version has breaking changes** so ensure to read these release notes carefully. Most of the changes are related to the internal workings of this Add-On, and as a user you will not see a change in the data available in Home Assistant. However the Device structure has changed, to make it possible to support multiple devices.

I want to extend a big THANK YOU to @natekspencer, who has done all the work on these changes.

The UDP communication with the WeatherFlow Hub, has, until this version, been built in to the Add-On. This has now been split out to a separate module, which makes it a lot easier to maintain new data points going forward.
@natekspencer has done a tremendous job in modernizing the [`pyweatherflowudp`](https://github.com/briis/pyweatherflowudp) package. This package does all the UDP communication with the WeatherFlow hub and using this module, we can now remove all that code from this Add-On.

### Breaking Changes

- With the support for multiple devices per Hub, we need to ensure that we know what data comes from what device. All sensors will as minimum get a new name. Previously sensors were named `WF Sensor Name` now they will be named `DEVICE SERIAL_NUMBER Sensor Name`. The entity_id will be `sensor.devicename_serialnumber_SENSORNAME`.
  - For existing installations with templates, automations, scripts or more that reference the previous `sensor.wf_` entities, it may be easier to perform the following steps after updating to this release than finding everywhere they have been used:
    1. Ensure you have advanced mode turned on for your user profile<br/>[![Open your Home Assistant instance and show your Home Assistant user's profile.](https://my.home-assistant.io/badges/profile.svg)](https://my.home-assistant.io/redirect/profile/)
    2. Navigate to integrations<br/>[![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)
    3. Click on "# devices" under your MQTT integration
    4. Click on the "WeatherFlow2MQTT" device (or whatever you renamed it to) and then delete it
    5. Go back to the MQTT devices and click on one of your sensor devices (Air, Sky, Tempest)
    6. Edit the device name and set it to "WF"
    7. Click on "UPDATE"
    8. A popup will ask if you also want to rename the entity IDs (requires advanced mode as stated in step 1). Click on "RENAME" and Home Assistant will rename all the entities to `sensor.wf_`.
       - If any entity IDs clash, you will get an error, but you can handle these individually as you deem necessary
    9. You can then rename the device back to your sensor name. Just click "NO" on the popup asking to change the entity IDs or you will have to repeat the process
    10. Repeat steps 5-9 for each sensor (mostly applicable to air & sky setups).
- Status sensor is now a timestamp (referencing the up_since timestamp of the device) instead of the "humanized" time string since HA takes care of "humanizing" on the front end. This reduces state updates on the sensor since it doesn't have to update every time the uptime seconds change
- `device`\_status (where device is hub, air, sky or tempest) is now just status
- similarly, battery\_`sensor`, battery_level\_`sensor` and voltage\_`sensor` are now just battery, battery_level and voltage, respectively

### Changes

- Multiple devices are now created in mqtt (one for each device)
- Removes the TEMPEST_DEVICE environment variable/config option since we no longer need a user to tell us the type of device
  - You will get a warning in the supervisor logs about the TEMPEST_DEVICE option being set until it is removed from your add-on configuration yaml.

## [2.2.5] - 2021-12-04

### Fixed

- With HA V2021.12 all date and time values need to be in utc time with timezone information. #105

## [2.2.4] - 2021-11-20

### Changed

- @natekspencer did inital work to implement a easier to manage class structure to ease future development.
- **BREAKING CHANGE** If you run the Non-Supervised mode of the program, you must make a change in your docker configuration to ensure you point to the same data directory as before. Change this `-v $(pwd): /usr/local/config` to this `-v $(pwd): /data`

## [2.2.3] - 2021-11-17

### Changed

- @natekspencer optimized the unit conversion code.
- New Logos for the Home Assistant Add-On

## [2.2.2] - 2021-11-15

### Changed

- Issue #93. A user reported that Temperature sensors creates an error when being exported to `homekit`. This is not a consistent error, but might be due to unicoding of the degree symbol. The `unit_of_measurement` value has now been changed so that it reflects the constants from Home Assistant.

## [2.2.1] - 2021-11-13

@natekspencer further enhanced the Home Assistant Add-On experience and made this more compliant with the way the Add-On is setup. Also he added a new option to filter out sensors _you do not want_, plus a few other great things you can read about below. Thank you @natekspencer.

### Changed

- **BREAKING CHANGE** Move mapped volume from /usr/local/config to /data to support supervisor. If you are not running the Home Assistant supervised version, then you will need change this `v $(pwd):/usr/local/config` to this `v $(pwd):/data`.
- Move configuration defaults to code and gracefully handle retrieval
- Cleanup environment variables in Dockerfile since they are now handled in code
- Simplify config loading between environment/supervisor options
- Remove TZ option from HA supervisor configuration since it should be loaded from HA

### Added

- Add options for FILTER_SENSORS and INVERT_FILTER to avoid having to load a config.yaml file in HA
- Add a list of obsolete sensors that can be used to handle cleanup of old sensors when they are deprecated and removed

## [2.2.0] - 2021-11-10

### Changed

- **BREAKING CHANGE** The sensor `sensor.wf_uptime` has been renamed to `sensor.wf_hub_status`. This sensor will now have more attributes on the status of the Hub, like Serial Number, FW Version etc.

### Added

- Thanks to @natekspencer this image can now be installed and managed from the Home Assistant Add-On store. This is not part of the default store yet, but to use it from the Add-On store, just click the button 'ADD REPOSITORY' in the top of the README.md file. **NOTE** Remember to stop/remove the container running outside the Add-On store before attempting to install.
- Depending on what HW you have, there will be 1 or 2 new sensors created, called either `sensor.wf_tempest_status` (If you have a Tempest device) or `sensor.wf_air_status` and `sensor.wf_sky_status`. The state of the sensors will display the Uptime of each device, and then there will attributes giving more details about each HW device.

## 2.1.1

**Release Date**: October 17th, 2021

### Changes in release 2.1.1

* `NEW`: Discussion #83, added new sensor called `sensor.wf_absolute_humidity`, which shows the actual amount of water in volume of air. Thank you to @GlennGoddard for creating the formula.

## Version 2.1.0

**Release Date**: October 11th, 2021

### Changes in release 2.1.0

* `FIX`: Issue #78, wrong Hex code used for decimal symbols.
* `NEW`: Issue #77. Added new sensor called `sensor.wf_battery_mode`. This sensor reports a mode between 0 and 3, and the description for the mode is added as an attribute to the sensor. Basically it shows how the Tempest device operates with the current Voltage. You can read more about this on the [WeatherFlow Website](https://help.weatherflow.com/hc/en-us/articles/360048877194-Solar-Power-Rechargeable-Battery). **This sensor is only available for Tempest devices** <br>Thank you to @GlennGoddard for creating the formula.
* `NEW`: Issue #81. Added `state_class` attributes to all relevant sensors, so that they can be used with [Long Term Statistics](https://www.home-assistant.io/blog/2021/08/04/release-20218/#long-term-statistics). See the README file for a list of supported sensors.
* `NEW`: Discussion #83. Added new sensor `sensor.wf_rain_intensity`. This sensor shows a descriptive text about the current rain rate. See more on the [Weatherflow Community Forum](https://community.weatherflow.com/t/rain-intensity-values/806). The French and German translations are done by me, so they might need some checking to see if they are correct.

## Version 2.0.17

**Release Date**: August 18th, 2021

### Changes in release 2.0.17

`NEW`: Battery Percent sensors added. There will 2 new sensors if using AIR & SKY devices and 1 new if using the Tempest device. At the same time, the previous `battery` sensor name is now renamed to `voltage` as this is a more correct description of the value. Thanks to @GlennGoddard for creating the formula to do the conversion.<br>
**BREAKING** If you already have a running installation, you will have to manually rename two sensors entity_id, to correspond to the new naming: If you have a Tempest device rename `sensor.wf_battery_tempest` to `sensor.wf_voltage_tempest` and `sensor.wf_battery_tempest_2` to `sensor.wf_battery_tempest`. If you have AIR and SKY devices rename `sensor.wf_battery_sky` to `sensor.wf_voltage_sky` and `sensor.wf_battery_sky_2` to `sensor.wf_battery_sky`

`NEW`: Wet Bulb Globe Temperature. The WetBulb Globe Temperature (WBGT) is a measure of the heat stress in direct sunlight. Thanks to @GlennGoddard for creating the formula

`FIX`: Fixing issue #71. Device status was reported wrong. Thank you to @WM for catching this and proposing the fix.

`CHANGE`: Ensure SHOW_DEBUG flag is used everywhere.

`NEW`: Added German Translation. Thank you to @The-Deep-Sea for doing this.

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
