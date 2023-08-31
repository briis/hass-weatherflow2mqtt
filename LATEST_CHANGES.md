# Change Log

All notable changes to this project will be documented in this file.

## [3.2.1] - Not Yet Released

### Changes

- Some stations do not get the Sea Level Pressure in the Hourly Forecast. It is not clear why this happens, but the issue is with WeatherFlow. The change implemented here, ensures that the system does not break because of that. If not present a 0 value is returned.