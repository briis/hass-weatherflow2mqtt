# Change Log

All notable changes to this project will be documented in this file.

## Not Yet Released

### Changes

- BUGFIX: Changed spelling error in `en.json` file. Tnanks to @jazzyisj
- BUGFIX: Bump `pyweatherflowudp` to V1.3.1 to handle `up_since` oscillation on devices
- NEW: Added Latitude and Longitude environment variables. These will be used in later additions for new calculated sensors. If you run the Supervised Add-On, then these will be provided automatically by Home Assistent. If you run a standalone docker container, you must add: `-e LATITUDE=your_latiude e- LONGITUDE=your_longitude` to the Docker startup command.
