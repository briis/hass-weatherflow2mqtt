"""Constant file for weatherflow2mqtt."""
import datetime
import os

ATTRIBUTION = "Powered by WeatherFlow2MQTT"
DOMAIN = "weatherflow2mqtt"
MANUFACTURER = "WeatherFlow"

ATTR_ATTRIBUTION = "attribution"
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

EXTERNAL_DIRECTORY = os.environ.get("EXTERNAL_DIRECTORY", "/data")
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
COL_PRESSURE = "sealevel_pressure"
COL_UV = "uv"
COL_SOLARRAD = "solar_radiation"

BASE_URL = "https://swd.weatherflow.com/swd/rest"

BATTERY_MODE_DESCRIPTION = [
    "All sensors enabled and operating at full performance. Wind sampling interval every 3 seconds",
    "Wind sampling interval set to 6 seconds",
    "Wind sampling interval set to one minute",
    "Wind sampling interval set to 5 minutes. All other sensors sampling interval set to 5 minutes. Haptic Rain sensor disabled from active listening",
]

DEFAULT_TIMEOUT = 10

DEVICE_CLASS_BATTERY = "battery"
DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_ILLUMINANCE = "illuminance"
DEVICE_CLASS_PRESSURE = "pressure"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_VOLTAGE = "voltage"

STATE_CLASS_MEASUREMENT = "measurement"
STATE_CLASS_INCREASING = "total_increasing"

EVENT_FORECAST = "weather"
EVENT_HIGH_LOW = "high_low"

FORECAST_TYPE_DAILY = "daily"
FORECAST_TYPE_HOURLY = "hourly"
FORECAST_ENTITY = "weather"
FORECAST_HOURLY_HOURS = 36

STRIKE_COUNT_TIMER = 3 * 60 * 60
PRESSURE_TREND_TIMER = 3 * 60 * 60
HIGH_LOW_TIMER = 10 * 60

LANGUAGE_ENGLISH = "en"
LANGUAGE_DANISH = "da"
LANGUAGE_GERMAN = "de"
LANGUAGE_FRENCH = "fr"
SUPPORTED_LANGUAGES = [
    LANGUAGE_ENGLISH,
    LANGUAGE_DANISH,
    LANGUAGE_GERMAN,
    LANGUAGE_FRENCH,
]

TEMP_CELSIUS = "°C"
TEMP_FAHRENHEIT = "°F"
UNITS_IMPERIAL = "imperial"
UNITS_METRIC = "metric"

UTC = datetime.timezone.utc


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
