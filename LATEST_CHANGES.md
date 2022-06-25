# Change Log

All notable changes to this project will be documented in this file.

## [3.1.0] - Not Yet Released

### Changed

- Bumped `pyweatherflowudp` to V1.4.0. Thank you to @natekspencer for keeping this module in good shape.
  - Adjusted logic for `wind_direction` and `wind_direction_cardinal` to report based on the last wind event or observation, whichever is most recent (similar to `wind_speed`)
  - Added properties for `wind_direction_average` and `wind_direction_average_cardinal` to report only on the average wind direction
  - Handle UnicodeDecodeError during message processing
  - Bump Pint to ^0.19

  **Breaking Changes**:

  - The properties `wind_direction` and `wind_direction_cardinal` now report based on the last wind event or observation, whichever is most recent. If you want the wind direction average (previous logic), please use the properties `wind_direction_average` and `wind_direction_average_cardinal`, respectively
  - The default symbol for `rain_rate` is now `mm/h` instead of `mm/hr` due to Pint 0.19 - https://github.com/hgrecco/pint/pull/1454

### Added

- Added new sensor `solar_elevation` which returns Sun Elevation in Degrees with respect to the Horizon. Thanks to @GlennGoddard for creating the formula.
  **NOTE**: If you are not running this module as a HASS Add-On, you must ensure that environment variables `LATITUDE` and `LONGITUDE` are set in the Docker Startup command, as these values are used to calculate this value.
- Added new sensor `solar_insolation` which returns Estimation of Solar Radiation at current sun elevation angle. Thanks to @GlennGoddard for creating the formula.
- Added new sensors `zambretti_number` and `zambretti_text`, which are sensors that uses local data to create Weather Forecast for the near future. In order to optimize the forecast, these values need the *All Time High and Low Sea Level Presurre*. Per default these are set to 960Mb for Low and 1050Mb for High. They can be changed by adding the Environment Variables `ZAMBRETTI_MIN_PRESSURE` and `ZAMBRETTI_MAX_PRESSURE` to the Docker Start command.
