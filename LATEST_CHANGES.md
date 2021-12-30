# Change Log

All notable changes to this project will be documented in this file.

## Not Yet Released

### Changes

- BUGFIX: Handle MQTT qos>0 messages appropriately by calling loop_start() on the MQTT client
  - See https://github.com/eclipse/paho.mqtt.python#client
  - Fixing Issue #46.