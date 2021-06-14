"""Constant file for weatherflow2mqtt."""
import datetime

ATTRIBUTION = "Powered by WeatherFlow2MQTT"
BRAND = "WeatherFlow"

ATTR_ATTRIBUTION = "attribution"
ATTR_BRAND = "brand"
ATTR_FORECAST_CONDITION = "condition"
ATTR_FORECAST_PRECIPITATION = "precipitation"
ATTR_FORECAST_PRECIPITATION_PROBABILITY = "precipitation_probability"
ATTR_FORECAST_PRESSURE = "pressure"
ATTR_FORECAST_TEMP = "temperature"
ATTR_FORECAST_TEMP_LOW = "templow"
ATTR_FORECAST_TIME = "datetime"
ATTR_FORECAST_WIND_BEARING = "wind_bearing"
ATTR_FORECAST_WIND_SPEED = "wind_speed"
ATTR_FORECAST_HUMIDITY = "humidity"

EXTERNAL_DIRECTORY = "/usr/local/config"
STORAGE_FILE = f"{EXTERNAL_DIRECTORY}/.storage.json"
DATABASE = f"{EXTERNAL_DIRECTORY}/weatherflow2mqtt.db"
STORAGE_ID = 1

TABLE_STORAGE = """ CREATE TABLE IF NOT EXISTS storage (
                    id integer PRIMARY KEY,
                    rain_today real,
                    rain_yesterday real,
                    rain_start real,
                    rain_duration_today integer,
                    rain_duration_yesterday integer,
                    lightning_count integer,
                    lightning_count_today integer,
                    last_lightning_time real,
                    last_lightning_distance integer,
                    last_lightning_energy
                );"""

TABLE_PRESSURE = """ CREATE TABLE IF NOT EXISTS pressure (
                    timestamp real PRIMARY KEY,
                    pressure real
                );"""

TABLE_LIGHTNING = """ CREATE TABLE IF NOT EXISTS lightning (
                    timestamp real PRIMARY KEY
                );"""

STORAGE_FIELDS = [
    ["rain_today", 0],
    ["rain_yesterday", 0],
    ["rain_start", datetime.datetime.fromtimestamp(0).isoformat()],
    ["rain_duration_today", 0],
    ["rain_duration_yesterday", 0],
    ["lightning_count", 0],
    ["lightning_count_today", 0],
    ["last_lightning_time", 0],
    ["last_lightning_distance", 0],
    ["last_lightning_energy", 0],
]
STRIKE_STORAGE_FILE = f"{EXTERNAL_DIRECTORY}/.lightning.data"
PRESSURE_STORAGE_FILE = f"{EXTERNAL_DIRECTORY}/.pressure.data"

BASE_URL = "https://swd.weatherflow.com/swd/rest"

DEFAULT_TIMEOUT = 10
DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_ILLUMINANCE = "illuminance"
DEVICE_CLASS_PRESSURRE = "pressure"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_VOLTAGE = "voltage"

DEVICE_STATUS = [
    "Sensors OK",
    "lightning failed",
    "lightning noise",
    "lightning disturber",
    "pressure failed",
    "temperature failed",
    "rh failed",
    "wind failed",
    "precip failed",
    "light/uv failed",
]

DOMAIN = "weatherflow2mqtt"

EVENT_RAPID_WIND = "rapid_wind"
EVENT_HUB_STATUS = "hub_status"
EVENT_DEVICE_STATUS = "device_status"
EVENT_AIR_DATA = "obs_air"
EVENT_SKY_DATA = "obs_sky"
EVENT_TEMPEST_DATA = "obs_st"
EVENT_PRECIP_START = "evt_precip"
EVENT_STRIKE = "evt_strike"
EVENT_FORECAST = "forecast"

FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"
FORECAST_HOURLY_HOURS = 36

STRIKE_COUNT_TIMER = 3 * 60 * 60
PRESSURE_TREND_TIMER = 3 * 60 * 60

UNITS_IMPERIAL = "imperial"

UTC = datetime.timezone.utc

# Sensor ID, Sensor Name, Unit Metric, Unit Imperial, Device Class, Icon, Update Event
WEATHERFLOW_SENSORS = [
    ["wind_speed", "Wind Speed", "m/s", "mph", None, "weather-windy", EVENT_RAPID_WIND],
    ["wind_bearing", "Wind Bearing", "˚", "˚", None, "compass", EVENT_RAPID_WIND],
    [
        "wind_direction",
        "Wind Direction",
        None,
        None,
        None,
        "compass-outline",
        EVENT_RAPID_WIND,
    ],
    [
        "station_pressure",
        "Station Pressure",
        "hPa",
        "inHg",
        DEVICE_CLASS_PRESSURRE,
        None,
        EVENT_AIR_DATA,
    ],
    [
        "sealevel_pressure",
        "Sea Level Pressure",
        "hPa",
        "inHg",
        DEVICE_CLASS_PRESSURRE,
        None,
        EVENT_AIR_DATA,
    ],
    [
        "air_temperature",
        "Temperature",
        "˚C",
        "˚F",
        DEVICE_CLASS_TEMPERATURE,
        None,
        EVENT_AIR_DATA,
    ],
    [
        "relative_humidity",
        "Humidity",
        "%",
        "%",
        DEVICE_CLASS_HUMIDITY,
        None,
        EVENT_AIR_DATA,
    ],
    [
        "lightning_strike_count",
        "Lightning Count (3 hours)",
        None,
        None,
        None,
        "weather-lightning",
        EVENT_AIR_DATA,
    ],
    [
        "lightning_strike_count_today",
        "Lightning Count (Today)",
        None,
        None,
        None,
        "weather-lightning",
        EVENT_AIR_DATA,
    ],
    [
        "battery_air",
        "Battery AIR",
        "V",
        "V",
        DEVICE_CLASS_VOLTAGE,
        None,
        EVENT_AIR_DATA,
    ],
    [
        "lightning_strike_distance",
        "Lightning Distance",
        "km",
        "mi",
        None,
        "flash",
        EVENT_AIR_DATA,
    ],
    [
        "lightning_strike_energy",
        "Lightning Energy",
        None,
        None,
        None,
        "flash",
        EVENT_AIR_DATA,
    ],
    [
        "lightning_strike_time",
        "Last Lightning Strike",
        None,
        None,
        DEVICE_CLASS_TIMESTAMP,
        "clock-outline",
        EVENT_AIR_DATA,
    ],
    [
        "illuminance",
        "Illuminance",
        "lx",
        "lx",
        DEVICE_CLASS_ILLUMINANCE,
        None,
        EVENT_SKY_DATA,
    ],
    ["uv", "UV Index", "UVI", "UVI", None, "weather-sunny-alert", EVENT_SKY_DATA],
    ["rain_today", "Rain Today", "mm", "in", None, "weather-pouring", EVENT_SKY_DATA],
    [
        "rain_yesterday",
        "Rain Yesterday",
        "mm",
        "in",
        None,
        "weather-pouring",
        EVENT_SKY_DATA,
    ],
    ["rain_duration_today", "Rain Duration (Today)", "min", "min", None, "timeline-clock-outline", EVENT_SKY_DATA],
    ["rain_duration_yesterday", "Rain Duration (Yesterday)", "min", "min", None, "timeline-clock-outline", EVENT_SKY_DATA],
    [
        "wind_lull",
        "Wind Lull",
        "m/s",
        "mph",
        None,
        "weather-windy-variant",
        EVENT_SKY_DATA,
    ],
    [
        "wind_speed_avg",
        "Wind Speed Avg",
        "m/s",
        "mph",
        None,
        "weather-windy-variant",
        EVENT_SKY_DATA,
    ],
    ["wind_gust", "Wind Gust", "m/s", "mph", None, "weather-windy", EVENT_SKY_DATA],
    ["wind_bearing_avg", "Wind Bearing Avg", "˚", "˚", None, "compass", EVENT_SKY_DATA],
    [
        "wind_direction_avg",
        "Wind Direction Avg",
        None,
        None,
        None,
        "compass-outline",
        EVENT_SKY_DATA,
    ],
    ["battery", "Battery SKY", "V", "V", DEVICE_CLASS_VOLTAGE, None, EVENT_SKY_DATA],
    [
        "solar_radiation",
        "Solar Radiation",
        "W/m^2",
        "W/m^2",
        None,
        "solar-power",
        EVENT_SKY_DATA,
    ],
    [
        "precipitation_type",
        "Precipitation Type",
        None,
        None,
        None,
        "weather-rainy",
        EVENT_SKY_DATA,
    ],
    [
        "rain_start_time",
        "Last Rain start",
        None,
        None,
        DEVICE_CLASS_TIMESTAMP,
        "clock-outline",
        EVENT_SKY_DATA,
    ],
    [
        "air_density",
        "Air Density",
        "kg/m^3",
        "lb/ft^3",
        None,
        "air-filter",
        EVENT_AIR_DATA,
    ],
    [
        "dewpoint",
        "Dew Point",
        "˚C",
        "˚F",
        DEVICE_CLASS_TEMPERATURE,
        None,
        EVENT_AIR_DATA,
    ],
    ["rain_rate", "Rain Rate", "mm/h", "in/h", None, "weather-pouring", EVENT_SKY_DATA],
    ["uptime", "Uptime", None, None, None, "clock-outline", EVENT_HUB_STATUS],
    [
        "feelslike",
        "Feels Like Temperature",
        "˚C",
        "˚F",
        DEVICE_CLASS_TEMPERATURE,
        None,
        EVENT_AIR_DATA,
    ],
    ["weather", "Weather", None, None, None, "chart-box-outline", EVENT_FORECAST],
]

SENSOR_ID = 0
SENSOR_NAME = 1
SENSOR_UNIT_M = 2
SENSOR_UNIT_I = 3
SENSOR_CLASS = 4
SENSOR_ICON = 5
SENSOR_DEVICE = 6

CONDITION_CLASSES = {
    "clear-night": ["clear-night"],
    "cloudy": ["cloudy"],
    "exceptional": ["cloudy"],
    "fog": ["foggy"],
    "hail": ["hail"],
    "lightning": ["thunderstorm"],
    "lightning-rainy": ["possibly-thunderstorm-day", "possibly-thunderstorm-night"],
    "partlycloudy": [
        "partly-cloudy-day",
        "partly-cloudy-night",
    ],
    "rainy": [
        "rainy",
        "possibly-rainy-day",
        "possibly-rainy-night",
    ],
    "snowy": ["snow", "possibly-snow-day", "possibly-snow-night"],
    "snowy-rainy": ["sleet", "possibly-sleet-day", "possibly-sleet-night"],
    "sunny": ["clear-day"],
    "windy": ["windy"],
}