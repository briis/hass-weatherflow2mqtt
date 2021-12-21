# Change Log

All notable changes to this project will be documented in this file.

## [3.0.4] - Unreleased

### Changes

- Add a debug log when updating forecast data and set qos=1 to ensure delivery
- Add another debug log to indicate next forecast update
- Docker container is now using the `slim-buster` version of Ubuntu instead of the full version, reducing the size of the Container to one third of the original size.
