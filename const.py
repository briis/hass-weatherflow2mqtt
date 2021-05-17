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

# Sensor ID, Sensor Name, Unit Metric, Unit Imperial, Device Class, Icon, Update Event
WEATHERFLOW_SENSORS = [
    ["wind_speed", "Wind Speed", "m/s", "mph", None, "weather-windy", EVENT_RAPID_WIND],
    ["wind_bearing", "Wind Bearing", "˚", "˚", None, "compass", EVENT_RAPID_WIND],
    ["wind_direction", "Wind Direction", None, None, None, "compass-outline", EVENT_RAPID_WIND],
    ["station_pressure", "Station Pressure", "hPa", "inHg", DEVICE_CLASS_PRESSURRE, None, EVENT_AIR_DATA],
    ["sealevel_pressure", "Sea Level Pressure", "hPa", "inHg", DEVICE_CLASS_PRESSURRE, None, EVENT_AIR_DATA],
    ["air_temperature", "Temperature", "˚C", "˚F", DEVICE_CLASS_TEMPERATURE, None, EVENT_AIR_DATA],
    ["relative_humidity", "Humidity", "%", "%", DEVICE_CLASS_HUMIDITY, None, EVENT_AIR_DATA],
    ["lightning_strike_count", "Lightning Strike Count", None, None, None, "weather-lightning", EVENT_AIR_DATA],
    ["lightning_strike_avg_distance", "Lightning Strike Avg Distance", "Km", None, None, "flash", EVENT_AIR_DATA],
    ["battery_air", "Battery AIR", "V", "V", DEVICE_CLASS_VOLTAGE, None, EVENT_AIR_DATA],
    ["lightning_strike_distance", "Lightning Strike Distance", "Km", "mi", None, "flash", EVENT_STRIKE],
    ["lightning_strike_energy", "Lightning Strike Energy", None, None, None, "flash", EVENT_STRIKE],
    ["illuminance", "Illuminance", "lx", "lx", DEVICE_CLASS_ILLUMINANCE, None, EVENT_SKY_DATA],
    ["uv", "UV Index", "UVI", "UVI", None, "weather-sunny-alert", EVENT_SKY_DATA],
    ["rain_accumulated", "Rain Accumulated", "mm", "in", None, "weather-pouring", EVENT_SKY_DATA],
    ["wind_lull", "Wind Lull", "m/s", "mph", None, "weather-windy-variant", EVENT_SKY_DATA],
    ["wind_speed_avg", "Wind Speed Avg", "m/s", "mph", None, "weather-windy-variant", EVENT_SKY_DATA],
    ["wind_gust", "Wind Gust", "m/s", "mph", None, "weather-windy", EVENT_SKY_DATA],
    ["wind_bearing_avg", "Wind Bearing Avg", "˚", "˚", None, "compass", EVENT_SKY_DATA],
    ["wind_direction_avg", "Wind Direction Avg", None, None, None, "compass-outline", EVENT_SKY_DATA],
    ["battery_sky", "Battery SKY", "V", "V", DEVICE_CLASS_VOLTAGE, None, EVENT_SKY_DATA],
    ["solar_radiation", "Solar Radiation", "W/m^2", "W/m^2", None, "solar-power", EVENT_SKY_DATA],
    ["precipitation_type", "Precipitation Type", None, None, None, "weather-rainy", EVENT_SKY_DATA],
    ["rain_start_time", "Rain Start Time", None, None, DEVICE_CLASS_TIMESTAMP, "clock-outline", EVENT_PRECIP_START],
    ["air_density", "Air Density", "kg/m^3", "lb/ft^3", None, "air-filter", EVENT_AIR_DATA],
    ["dewpoint", "Dew Point", "˚C", "˚F", DEVICE_CLASS_TEMPERATURE, None, EVENT_AIR_DATA],
    ["rain_rate", "Rain Rate", "mm/h", "in/h", None, "weather-pouring", EVENT_SKY_DATA],
]

SENSOR_ID = 0
SENSOR_NAME = 1
SENSOR_UNIT_M = 2
SENSOR_UNIT_I = 3
SENSOR_CLASS = 4
SENSOR_ICON = 5
SENSOR_DEVICE = 6

TEMPEST_SENSORS = [EVENT_TEMPEST_DATA, EVENT_AIR_DATA, EVENT_SKY_DATA]
