# Change Log

All notable changes to this project will be documented in this file.

## [3.0.1] - 2021-12-10

### Fixed

- Issue #109. Adding better handling of missing data points when parsing messages which may occure when the firmware revision changes, to ensure the program keeps running.


## [3.0.0] - 2021-12-10

This is the first part of a major re-write of this Add-On. Please note **this version has breaking changes** so ensure to read these release notes carefully. Most of the changes are related to the internal workings of this Add-On, and as a user you will not see a change in the data available in Home Assistant. However the Device structure has changed, to make it possible to support multiple devices.

I want to extend a big THANK YOU to @natekspencer, who has done all the work on these changes.

The UDP communication with the WeatherFlow Hub, has, until this version, been built in to the Add-On. This has now been split out to a separate module, which makes it a lot easier to maintain new data points going forward.
@natekspencer has done a tremendous job in modernizing the [`pyweatherflowudp`](https://github.com/briis/pyweatherflowudp) package. This package does all the UDP communication with the WeatherFlow hub and using this module, we can now remove all that code from this Add-On.

### Breaking Changes

- With the support for multiple devices per Hub, we need to ensure that we know what data comes from what device. All sensors will as minimum get a new name. Previously sensors were named `WF Sensor Name` now they will be named `DEVICE SERIAL_NUMBER Sensor Name`. For existing installations the entity_id will not change, it will still be `sensor.wf_SENSOR_NAME`, but for new installations and new sensors it will be `sensor.devicename_serialnumber_SENSORNAME`
- Status sensor is now a timestamp (referencing the up_since timestamp of the device) instead of the "humanized" time string since HA takes care of "humanizing" on the front end. This reduces state updates on the sensor since it doesn't have to update every time the uptime seconds change
- `device`_status (where device is hub, air, sky or tempest) is now just status
- similarly, battery_`sensor`, battery_level_`sensor` and voltage_`sensor` are now just battery, battery_level and voltage, respectively
Other Changes:

### Changes

- Multiple devices are now created in mqtt (one for each device)
- Removes the TEMPEST_DEVICE environment variable/config option since we no longer need a user to tell us the type of device


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

@natekspencer further enhanced the Home Assistant Add-On experience and made this more compliant with the way the Add-On is setup. Also he added a new option to filter out sensors *you do not want*, plus a few other great things you can read about below. Thank you @natekspencer.

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
