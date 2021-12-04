# Change Log

All notable changes to this project will be documented in this file.

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
