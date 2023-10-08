# Change Log

All notable changes to this project will be documented in this file. 

## [3.2.2] - 2023-10-08

### BREAKING Announcement

As there is now a `Home Assistant Core` integration for WeatherFlow which uses the UDP API, I had to make a [new Integration](https://github.com/briis/weatherflow_forecast) that uses the REST API, with a different name (WeatherFlow Forecast). The new integration is up-to-date with the latest specs for how to create a Weather Forecast, and also gives the option to only add the Forecast, and no additional sensors. 

There is no *Weather Entity* in Home Assistant for MQTT, so after attributes are deprecated in Home Assistant 2024.3, there is no option to add the Forecast to Home Assistant.
As a consequence of that, I have decided to remove the ability for this Add-On to add Forecast data to MQTT and Home Assistant. This Add-On will still be maintained, but just without the option of a Forecast - meaning it will be 100% local.
If you want the forecast in combination with this Add-On, install the new integration mentioned above, just leave the *Add sensors* box unchecked.

There is not an exact date for when this will happen, but it will be before end of February 2024.

### Changes

- Added Slovenian language file. This was unfortunately placed in a wrong directory and as such it was not read by the integration. Fixing issue #236
- Fixed issue #244 with deprecated forecast values. Thank you @mjmeli
- Corrected visibility imperial unit from nautical mile (nmi) to mile (mi)

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

