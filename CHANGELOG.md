# Change Log

All notable changes to this project will be documented in this file.

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
- Added new sensors `zambretti_number` and `zambretti_text`, which are sensors that uses local data to create Weather Forecast for the near future. In order to optimize the forecast, these values need the *All Time High and Low Sea Level Presurre*. Per default these are set to 960Mb for Low and 1050Mb for High when using Metric units - 28.35inHg and 31.30inHg when using Imperial units. They can be changed by adding the Environment Variables `ZAMBRETTI_MIN_PRESSURE` and `ZAMBRETTI_MAX_PRESSURE` to the Docker Start command.

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
