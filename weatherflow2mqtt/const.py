"""Constant file for weatherflow2mqtt."""
import datetime
import os

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

EXTERNAL_DIRECTORY = os.environ.get("EXTERNAL_DIRECTORY", "/usr/local/config")
INTERNAL_DIRECTORY = "/app"
STORAGE_FILE = f"{EXTERNAL_DIRECTORY}/.storage.json"
DATABASE = f"{EXTERNAL_DIRECTORY}/weatherflow2mqtt.db"
DATABASE_VERSION = 2
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

TABLE_HIGH_LOW = """
                    CREATE TABLE IF NOT EXISTS high_low (
                        sensorid TEXT PRIMARY KEY,
                        latest REAL,
                        max_day REAL,
                        max_day_time REAL,
                        min_day REAL,
                        min_day_time REAL,
                        max_yday REAL,
                        max_yday_time REAL,
                        min_yday REAL,
                        min_yday_time REAL,
                        max_week REAL,
                        max_week_time REAL,
                        min_week REAL,
                        min_week_time REAL,
                        max_month REAL,
                        max_month_time REAL,
                        min_month REAL,
                        min_month_time REAL,
                        max_year REAL,
                        max_year_time REAL,
                        min_year REAL,
                        min_year_time REAL,
                        max_all REAL,
                        max_all_time REAL,
                        min_all REAL,
                        min_all_time REAL
                    );
                  """

TABLE_DAY_DATA = """ CREATE TABLE IF NOT EXISTS day_data (
                    timestamp REAL PRIMARY KEY,
                    air_temperature REAL,
                    relative_humidity REAL,
                    dewpoint REAL,
                    illuminance REAL,
                    rain_duration_today REAL,
                    rain_rate REAL,
                    wind_gust REAL,
                    wind_lull REAL,
                    wind_speed_avg REAL,
                    lightning_strike_energy REAL,
                    lightning_strike_count_today REAL,
                    sealevel_pressure REAL,
                    uv REAL,
                    solar_radiation REAL
                );"""

COL_TEMPERATURE = "air_temperature"
COL_HUMIDITY = "relative_humidity"
COL_DEWPOINT = "dewpoint"
COL_ILLUMINANCE = "illuminance"
COL_RAINDURATION = "rain_duration_today"
COL_RAINRATE = "rain_rate"
COL_WINDGUST = "wind_gust"
COL_WINDLULL = "wind_lull"
COL_WINDSPEED = "wind_speed_avg"
COL_STRIKEENERGY = "lightning_strike_energy"
COL_STRIKECOUNT = "lightning_strike_count_today"
COL_PRESSURE= "sealevel_pressure"
COL_UV = "uv"
COL_SOLARRAD = "solar_radiation"

BASE_URL = "https://swd.weatherflow.com/swd/rest"

BATTERY_MODE_DESCRIPTION = [
    "All sensors enabled and operating at full performance. Wind sampling interval every 3 seconds",
    "Wind sampling interval set to 6 seconds",
    "Wind sampling interval set to one minute",
    "Wind sampling interval set to 5 minutes. All other sensors sampling interval set to 5 minutes. Haptic Rain sensor disabled from active listening"
]

DEFAULT_TIMEOUT = 10
DEVICE_CLASS_BATTERY = "battery"
DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_ILLUMINANCE = "illuminance"
DEVICE_CLASS_PRESSURRE = "pressure"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_VOLTAGE = "voltage"

STATE_CLASS_MEASUREMENT = "measurement"

DEVICE_STATUS_MASKS = {
        0b000000001: 'Lightning',
        0b000000010: 'Lightning Noise',
        0b000000100: 'Lightning Disturber',
        0b000001000: 'Pressure',
        0b000010000: 'Temperature',
        0b000100000: 'Humidity',
        0b001000000: 'Wind',
        0b010000000: 'Precipitation',
        0b100000000: 'Light/UV',
        0x00008000: 'Power Booster Depleted',
        0b00010000: 'Power Booster Shore Power'
}

DOMAIN = "weatherflow2mqtt"

EVENT_RAPID_WIND = "rapid_wind"
EVENT_HUB_STATUS = "hub_status"
EVENT_DEVICE_STATUS = "device_status"
EVENT_AIR_DATA = "obs_air"
EVENT_SKY_DATA = "obs_sky"
EVENT_TEMPEST_DATA = "obs_st"
EVENT_PRECIP_START = "evt_precip"
EVENT_STRIKE = "evt_strike"
EVENT_FORECAST = "weather"
EVENT_HIGH_LOW = "high_low"

FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"
FORECAST_ENTITY = "weather"
FORECAST_HOURLY_HOURS = 36

STRIKE_COUNT_TIMER = 3 * 60 * 60
PRESSURE_TREND_TIMER = 3 * 60 * 60
HIGH_LOW_TIMER = 10 * 60

SUPPORTED_LANGUAGES = [
    "en",
    "da",
    "de",
    "fr"
]

UNITS_IMPERIAL = "imperial"

UTC = datetime.timezone.utc

# Sensor ID, Sensor Name, Unit Metric, Unit Imperial, Device Class, State Class, Icon, Update Event, Extra Attributes, Show Min Values, Show Last Reset
WEATHERFLOW_SENSORS = [
    ["wind_speed", "Wind Speed", "m/s", "mph", None, None, "weather-windy", EVENT_RAPID_WIND, False, False, False],
    ["wind_bearing", "Wind Bearing", "˚", "˚", None, None, "compass", EVENT_RAPID_WIND, False, False, False],
    [
        "wind_direction",
        "Wind Direction",
        None,
        None,
        None,
        None,
        "compass-outline",
        EVENT_RAPID_WIND,
        False,
        False,
        False
    ],
    [
        "station_pressure",
        "Station Pressure",
        "hPa",
        "inHg",
        DEVICE_CLASS_PRESSURRE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "sealevel_pressure",
        "Sea Level Pressure",
        "hPa",
        "inHg",
        DEVICE_CLASS_PRESSURRE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        True,
        True,
        False
    ],
    [
        "pressure_trend",
        "Pressure Trend",
        None,
        None,
        None,
        None,
        "trending-up",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "air_temperature",
        "Temperature",
        "°C",
        "°F",
        DEVICE_CLASS_TEMPERATURE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        True,
        True,
        False
    ],
    [
        "relative_humidity",
        "Humidity",
        "%",
        "%",
        DEVICE_CLASS_HUMIDITY,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        True,
        True,
        False
    ],
    [
        "lightning_strike_count",
        "Lightning Count",
        None,
        None,
        None,
        None,
        "weather-lightning",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "lightning_strike_count_1hr",
        "Lightning Count (Last hour)",
        None,
        None,
        None,
        None,
        "weather-lightning",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "lightning_strike_count_3hr",
        "Lightning Count (3 hours)",
        None,
        None,
        None,
        None,
        "weather-lightning",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "lightning_strike_count_today",
        "Lightning Count (Today)",
        None,
        None,
        None,
        STATE_CLASS_MEASUREMENT,
        "weather-lightning",
        EVENT_AIR_DATA,
        True,
        False,
        True
    ],
    [
        "battery_air",
        "Voltage AIR",
        "V",
        "V",
        DEVICE_CLASS_VOLTAGE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "battery_level_air",
        "Battery AIR",
        "%",
        "%",
        DEVICE_CLASS_BATTERY,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "battery_level_sky",
        "Battery SKY",
        "%",
        "%",
        DEVICE_CLASS_BATTERY,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_SKY_DATA,
        False,
        False
    ],
    [
        "battery_level_tempest",
        "Battery TEMPEST",
        "%",
        "%",
        DEVICE_CLASS_BATTERY,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    [
        "battery_mode",
        "Battery Mode",
        "",
        "",
        None,
        None,
        "information-outline",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    [
        "lightning_strike_distance",
        "Lightning Distance",
        "km",
        "mi",
        None,
        None,
        "flash",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "lightning_strike_energy",
        "Lightning Energy",
        None,
        None,
        None,
        None,
        "flash",
        EVENT_AIR_DATA,
        True,
        False,
        False
    ],
    [
        "lightning_strike_time",
        "Last Lightning Strike",
        None,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        "clock-outline",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "illuminance",
        "Illuminance",
        "lx",
        "lx",
        DEVICE_CLASS_ILLUMINANCE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_SKY_DATA,
        True,
        False,
        False
    ],
    ["uv", "UV Index", "UVI", "UVI", None, None, "weather-sunny-alert", EVENT_SKY_DATA, True, False, False],
    ["rain_today", "Rain Today", "mm", "in", None, STATE_CLASS_MEASUREMENT, "weather-pouring", EVENT_SKY_DATA, False, False, True],
    [
        "rain_yesterday",
        "Rain Yesterday",
        "mm",
        "in",
        None,
        None,
        "weather-pouring",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    ["rain_duration_today", "Rain Duration (Today)", "min", "min", None, STATE_CLASS_MEASUREMENT, "timeline-clock-outline", EVENT_SKY_DATA, True, False, True],
    ["rain_duration_yesterday", "Rain Duration (Yesterday)", "min", "min", None, None, "timeline-clock-outline", EVENT_SKY_DATA, False, False, False],
    [
        "wind_lull",
        "Wind Lull",
        "m/s",
        "mph",
        None,
        None,
        "weather-windy-variant",
        EVENT_SKY_DATA,
        True,
        False,
        False
    ],
    [
        "wind_speed_avg",
        "Wind Speed Avg",
        "m/s",
        "mph",
        None,
        None,
        "weather-windy-variant",
        EVENT_SKY_DATA,
        True,
        False,
        False
    ],
    ["wind_gust", "Wind Gust", "m/s", "mph", None, None, "weather-windy", EVENT_SKY_DATA, True, False, False],
    ["wind_bearing_avg", "Wind Bearing Avg", "˚", "˚", None, None, "compass", EVENT_SKY_DATA, False, False, False],
    [
        "wind_direction_avg",
        "Wind Direction Avg",
        None,
        None,
        None,
        None,
        None,
        "compass-outline",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    ["battery", "Voltage SKY", "V", "V", DEVICE_CLASS_VOLTAGE, STATE_CLASS_MEASUREMENT, None, EVENT_SKY_DATA, False, False, False],
    [
        "solar_radiation",
        "Solar Radiation",
        "W/m^2",
        "W/m^2",
        None,
        None,
        "solar-power",
        EVENT_SKY_DATA,
        True,
        False,
        False
    ],
    [
        "precipitation_type",
        "Precipitation Type",
        None,
        None,
        None,
        None,
        "weather-rainy",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    [
        "rain_start_time",
        "Last Rain start",
        None,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        "clock-outline",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    [
        "air_density",
        "Air Density",
        "kg/m^3",
        "lb/ft^3",
        None,
        None,
        "air-filter",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "dewpoint",
        "Dew Point",
        "°C",
        "°F",
        DEVICE_CLASS_TEMPERATURE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        True,
        True,
        False
    ],
    ["rain_rate", "Rain Rate", "mm/h", "in/h", None, None, "weather-pouring", EVENT_SKY_DATA, True, False, False],
    ["uptime", "Uptime", None, None, None, None, "clock-outline", EVENT_HUB_STATUS, False, False, False],
    [
        "feelslike",
        "Feels Like Temperature",
        "°C",
        "°F",
        DEVICE_CLASS_TEMPERATURE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    ["visibility", "Visibility", "km", "nmi", None, None, "eye", EVENT_AIR_DATA, False, False, False],
    [
        "wetbulb",
        "Wet Bulb Temperature",
        "°C",
        "°F",
        DEVICE_CLASS_TEMPERATURE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "wbgt",
        "Wet Bulb Globe Temperature",
        "°C",
        "°F",
        DEVICE_CLASS_TEMPERATURE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "delta_t",
        "Delta T",
        "°C",
        "°F",
        DEVICE_CLASS_TEMPERATURE,
        STATE_CLASS_MEASUREMENT,
        None,
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "dewpoint_description",
        "Dewpoint Comfort Level",
        None,
        None,
        None,
        None,
        "text-box-outline",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "temperature_description",
        "Temperature Level",
        None,
        None,
        None,
        None,
        "text-box-outline",
        EVENT_AIR_DATA,
        False,
        False,
        False
    ],
    [
        "uv_description",
        "UV Level",
        None,
        None,
        None,
        None,
        "text-box-outline",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    [
        "beaufort",
        "Beaufort Scale",
        None,
        None,
        None,
        None,
        "tailwind",
        EVENT_SKY_DATA,
        False,
        False,
        False
    ],
    [FORECAST_ENTITY, "Weather", None, None, None, None, "chart-box-outline", EVENT_FORECAST, False, False, False],
]

SENSOR_ID = 0
SENSOR_NAME = 1
SENSOR_UNIT_M = 2
SENSOR_UNIT_I = 3
SENSOR_CLASS = 4
SENSOR_STATE_CLASS = 5
SENSOR_ICON = 6
SENSOR_DEVICE = 7
SENSOR_EXTRA_ATT = 8
SENSOR_SHOW_MIN_ATT = 9
SENSOR_LAST_RESET = 10

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
