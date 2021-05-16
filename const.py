"""Constant file for weatherflow2mqtt."""

DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_ILLUMINANCE = "illuminance"
DEVICE_CLASS_PRESSURRE = "pressure"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_VOLTAGE = "voltage"

DOMAIN = "weatherflow2mqtt"
DOMAIN_SHORT = "WF2MQTT"

EVENT_RAPID_WIND = "rapid_wind"
EVENT_HUB_STATUS = "hub_status"
EVENT_DEVICE_STATUS = "device_status"
EVENT_AIR_DATA = "obs_air"
EVENT_SKY_DATA = "obs_sky"
EVENT_TEMPEST_DATA = "obs_st"
EVENT_PRECIP_START = "evt_precip"
EVENT_STRIKE = "evt_strike"

UNITS_IMPERIAL = "imperial"

# Sensor ID, Sensor Name, Unit Metric, Unit Imperial, Device Class
WEATHERFLOW_SENSORS = [
    ["wind_speed", "Wind Speed", "m/s", "mph", None, EVENT_RAPID_WIND],
    ["wind_bearing", "Wind Bearing", "˚", "˚", None, EVENT_RAPID_WIND],
    ["wind_direction", "Wind Direction", None, None, None, EVENT_RAPID_WIND],
    ["station_pressure", "Station Pressure", "hPa", "inHg", DEVICE_CLASS_PRESSURRE, EVENT_AIR_DATA],
    ["sealevel_pressure", "Sea Level Pressure", "hPa", "inHg", DEVICE_CLASS_PRESSURRE, EVENT_AIR_DATA],
    ["air_temperature", "Temperature", "˚C", "˚F", DEVICE_CLASS_TEMPERATURE, EVENT_AIR_DATA],
    ["relative_humidity", "Humidity", "%", "%", DEVICE_CLASS_HUMIDITY, EVENT_AIR_DATA],
    ["lightning_strike_count", "Lightning Strike Count", None, None, None, EVENT_AIR_DATA],
    ["lightning_strike_avg_distance", "Lightning Strike Avg Distance", "Km", None, None, EVENT_AIR_DATA],
    ["battery_air", "Battery AIR", "V", "V", DEVICE_CLASS_VOLTAGE, EVENT_AIR_DATA],
    ["lightning_strike_distance", "Lightning Strike Distance", "Km", "mi", None, EVENT_STRIKE],
    ["lightning_strike_energy", "Lightning Strike Energy", None, None, None, EVENT_STRIKE],
    ["illuminance", "Illuminance", "lx", "lx", DEVICE_CLASS_ILLUMINANCE, EVENT_SKY_DATA],
    ["uv", "UV Index", "UVI", "UVI", None, EVENT_SKY_DATA],
    ["rain_accumulated", "Rain Accumulated", "mm", "in", None, EVENT_SKY_DATA],
    ["wind_lull", "Wind Lull", "m/s", "mph", None, EVENT_SKY_DATA],
    ["wind_speed_avg", "Wind Speed Avg", "m/s", "mph", None, EVENT_SKY_DATA],
    ["wind_gust", "Wind Gust", "m/s", "mph", None, EVENT_SKY_DATA],
    ["wind_bearing_avg", "Wind Bearing Avg", "˚", "˚", None, EVENT_SKY_DATA],
    ["wind_direction_avg", "Wind Direction Avg", None, None, None, EVENT_SKY_DATA],
    ["battery_sky", "Battery SKY", "V", "V", DEVICE_CLASS_VOLTAGE, EVENT_SKY_DATA],
    ["solar_radiation", "Solar Radiation", "W/m^2", "W/m^2", None, EVENT_SKY_DATA],
    ["precipitation_type", "Precipitation Type", None, None, None, EVENT_SKY_DATA],
    ["rain_start_time", "Rain Start Time", None, None, DEVICE_CLASS_TIMESTAMP, EVENT_PRECIP_START],
]

SENSOR_ID = 0
SENSOR_NAME = 1
SENSOR_UNIT_M = 2
SENSOR_UNIT_I = 3
SENSOR_CLASS = 4
SENSOR_DEVICE = 5

TEMPEST_SENSORS = [EVENT_TEMPEST_DATA, EVENT_AIR_DATA, EVENT_SKY_DATA]
