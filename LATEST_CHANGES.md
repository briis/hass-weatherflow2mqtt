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