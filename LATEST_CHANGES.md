# Change Log

All notable changes to this project will be documented in this file.

## [3.1.7] - Not Yet Released

### Fixed

- Fixed wrong type string in the `rain_type` function, so that it should now also get a string for Heavy Rain. Thanks to @GlennGoddard for spotting this. Closing #205
- Changing units using ^ to conform with HA standards
- Adding new device classes to selected sensors. (Wind Speed, Distance, Irradiation, Precipiation etc.)
- Closing #198 and #215, by trying to ensure that correct timezone and unit system is always set
