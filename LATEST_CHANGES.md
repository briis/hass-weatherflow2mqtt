# Change Log

All notable changes to this project will be documented in this file.

## [3.1.4] - Not Yet Released

### Added

- Added new sensor `fog_probability` which returns the probability for fog based on current conditions. Thanks to @GlennGoddard for creating the formula.
- Added new sensor `snow_probability` which returns the probability of snow based on current conditions. Thanks to @GlennGoddard for creating the formula.

### Changed

- Updated the French Translations. Thank you @MichelJourdain
- Issue #194. Adjusted Tempest minimum battery level to 2.11 V. The specs say that min is 1.8 V but experience show that below 2.11 the Tempest device does not work. So battery percent will now use this new min value.
