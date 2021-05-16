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

# Sensor ID, Sensor Name, Unit, Device Class
WEATHERFLOW_SENSORS = [
    ["wind_speed", "Wind Speed", "m/s", None, EVENT_RAPID_WIND],
    ["wind_bearing", "Wind Bearing", "˚", None, EVENT_RAPID_WIND],
    ["station_pressure", "Station Pressure", "hPa", DEVICE_CLASS_PRESSURRE, EVENT_AIR_DATA],
    ["sealevel_pressure", "Sea Level Pressure", "hPa", DEVICE_CLASS_PRESSURRE, EVENT_AIR_DATA],
    ["air_temperature", "Temperature", "˚C", DEVICE_CLASS_TEMPERATURE, EVENT_AIR_DATA],
    ["relative_humidity", "Humidity", "%", DEVICE_CLASS_HUMIDITY, EVENT_AIR_DATA],
    ["lightning_strike_count", "Lightning Strike Count", None, None, EVENT_AIR_DATA],
    ["lightning_strike_avg_distance", "Lightning Strike Avg Distance", "Km", None, EVENT_AIR_DATA],
    ["battery_air", "Battery AIR", "V", DEVICE_CLASS_VOLTAGE, EVENT_AIR_DATA],
    ["lightning_strike_distance", "Lightning Strike Distance", "Km", None, EVENT_STRIKE],
    ["lightning_strike_energy", "Lightning Strike Energy", "", None, EVENT_STRIKE],
    ["illuminance", "Illuminance", "lx", DEVICE_CLASS_ILLUMINANCE, EVENT_SKY_DATA],
    ["uv", "UV Index", "UVI", None, EVENT_SKY_DATA],
    ["rain_accumulated", "Rain Accumulated", "mm", None, EVENT_SKY_DATA],
    ["wind_lull", "Wind Lull", "m/s", None, EVENT_SKY_DATA],
    ["wind_speed_avg", "Wind Speed Avg", "m/s", None, EVENT_SKY_DATA],
    ["wind_gust", "Wind Gust", "m/s", None, EVENT_SKY_DATA],
    ["wind_bearing_avg", "Wind Bearing Avg", "˚", None, EVENT_SKY_DATA],
    ["battery_sky", "Battery SKY", "V", DEVICE_CLASS_VOLTAGE, EVENT_SKY_DATA],
    ["solar_radiation", "Solar Radiation", "W/m^2", None, EVENT_SKY_DATA],
    ["local_day_rain_accumulation", "Local Day Rain", "mm", None, EVENT_SKY_DATA],
    ["precipitation_type", "Precipitation Type", None, None, EVENT_SKY_DATA],
    ["rain_start_time", "Rain Start Time", None, DEVICE_CLASS_TIMESTAMP, EVENT_PRECIP_START],
]

SENSOR_ID = 0
SENSOR_NAME = 1
SENSOR_UNIT = 2
SENSOR_CLASS = 3
SENSOR_DEVICE = 4

TEMPEST_SENSORS = [EVENT_TEMPEST_DATA, EVENT_AIR_DATA, EVENT_SKY_DATA]
