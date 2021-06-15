# Home Assistant WeatherFlow2MQTT Changelog

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
