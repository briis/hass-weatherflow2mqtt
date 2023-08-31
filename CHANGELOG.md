# Change Log

All notable changes to this project will be documented in this file. 

## [3.2.1] - 2023-08-31

### Changes

- Some stations do not get the Sea Level Pressure and/or the UV value in the Hourly Forecast. It is not clear why this happens, but the issue is with WeatherFlow. The change implemented here, ensures that the system does not break because of that. If not present a 0 value is returned.
  This fixes Issue #234, #238 and maybe also #239

## [3.2.0] - 2023-08-29

### Changes

- Fixed wrong type string in the `rain_type` function, so that it should now also get a string for Heavy Rain. Thanks to @GlennGoddard for spotting this. Closing #205
- Changing units using ^ to conform with HA standards
- Adding new device classes to selected sensors. (Wind Speed, Distance, Irradiation, Precipiation etc.)
- Closing #198 and #215, by trying to ensure that correct timezone and unit system is always set
- Added swedish translation. Thank you to @Bo1jo
- Bumped docker image to `python:3.11-slim-buster` and @pcfens optimized the `Dockerfile`` to create a faster and smaller image.
- Bumped all dependency modules to latest available version
- Thanks @quentinmit the following improvements have been made, that makes it easier to run the program without Docker in a more traditional `setuptools` way.
    - Translations are installed and loaded as package data
    - The no-longer-supported asyncio PyPI package is removed from requirements.txt
    - Pint 0.20 and 0.21 are supported (also requires the pyweatherflowudp patch I sent separately)
- @prigorus  added the Slovenian translation

