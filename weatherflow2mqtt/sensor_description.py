"""Sensor descriptions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pyweatherflowudp.device import (
    EVENT_OBSERVATION,
    EVENT_RAPID_WIND,
    EVENT_STATUS_UPDATE,
    TempestDevice,
    WeatherFlowDevice,
)

from weatherflow2mqtt.helpers import ConversionFunctions
from weatherflow2mqtt.sqlite import SQLFunctions

from .const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_DISTANCE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_IRRADIANCE,
    DEVICE_CLASS_PRECIPITATION,
    DEVICE_CLASS_PRECIPITATION_INTENSITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_WIND_SPEED,
    EVENT_FORECAST,
    FORECAST_ENTITY,
    STATE_CLASS_MEASUREMENT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from .helpers import NO_CONVERSION, no_conversion_to_none

ALTITUDE_FEET = "ft"
ALTITUDE_METERS = "m"
UV_INDEX = "UV index"


@dataclass
class BaseSensorDescription:
    """Base sensor description."""

    id: str
    name: str
    event: str

    attr: str | None = None
    device_class: str | None = None
    extra_att: bool = False
    has_description: bool = False
    icon: str | None = None
    last_reset: bool = False
    show_min_att: bool = False
    state_class: str | None = None
    unit_i: str | None = None
    unit_i_cnv: str | None = None
    unit_m: str | None = None
    unit_m_cnv: str | None = None

    @property
    def device_attr(self) -> str:
        """Return the device attr."""
        return self.id if self.attr is None else self.attr

    @property
    def imperial_unit(self) -> str | None:
        """Return the imperial unit."""
        return (
            self.unit_i
            if self.unit_i_cnv is None
            else no_conversion_to_none(self.unit_i_cnv)
        )

    @property
    def metric_unit(self) -> str | None:
        """Return the metric unit."""
        return (
            self.unit_m
            if self.unit_m_cnv is None
            else no_conversion_to_none(self.unit_m_cnv)
        )


@dataclass
class SensorDescription(BaseSensorDescription):
    """Sensor description."""

    custom_fn: Callable[[ConversionFunctions, WeatherFlowDevice], Any] | Callable[
        [ConversionFunctions, WeatherFlowDevice, Any | None], Any
    ] | None = None
    decimals: tuple[int | None, int | None] = (None, None)
    inputs: tuple[str, ...] = field(default_factory=tuple[str, ...])


@dataclass
class SqlSensorDescription(BaseSensorDescription):
    """Sql-based sensor description."""

    sql_fn: Callable[[SQLFunctions], Any] | None = None


@dataclass
class StorageSensorDescription(BaseSensorDescription):
    """Storage-based sensor description."""

    storage_field: str | None = None

    cnv_fn: Callable[[ConversionFunctions, Any], Any] | None = None

    def value(self, storage: dict[str, Any]) -> Any:
        """Return the field value from the storage."""
        return storage[self.storage_field]


STATUS_SENSOR = SensorDescription(
    id="status",
    name="Status",
    icon="clock-outline",
    event=EVENT_STATUS_UPDATE,
    attr="uptime",
    device_class=DEVICE_CLASS_TIMESTAMP,
)

DEVICE_SENSORS: tuple[BaseSensorDescription, ...] = (
    STATUS_SENSOR,
    SensorDescription(
        id="absolute_humidity",
        name="Absolute Humidity",
        event=EVENT_OBSERVATION,
        unit_m="g/m³",
        unit_i="g/m³",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="water-opacity",
        attr="relative_humidity",
        custom_fn=lambda cnv, device: None
        if None in (device.air_temperature, device.relative_humidity)
        else cnv.absolute_humidity(
            device.air_temperature.m, device.relative_humidity.m
        ),
    ),
    SensorDescription(
        id="air_density",
        name="Air Density",
        event=EVENT_OBSERVATION,
        unit_m="kg/m³",
        unit_i="lb/ft³",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="air-filter",
        decimals=(5, 5),
    ),
    SensorDescription(
        id="air_temperature",
        name="Temperature",
        unit_m=TEMP_CELSIUS,
        unit_i=TEMP_FAHRENHEIT,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        extra_att=True,
        show_min_att=True,
        decimals=(1, 1),
    ),
    SensorDescription(
        id="battery",
        name="Voltage",
        unit_m="V",
        unit_i="V",
        device_class=DEVICE_CLASS_VOLTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        decimals=(2, 2),
    ),
    SensorDescription(
        id="battery_level",
        name="Battery",
        unit_m="%",
        unit_i="%",
        device_class=DEVICE_CLASS_BATTERY,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        attr="battery",
        custom_fn=lambda cnv, device: None
        if device.battery is None
        else cnv.battery_level(device.battery.m, isinstance(device, TempestDevice)),
    ),
    SensorDescription(
        id="battery_mode",
        name="Battery Mode",
        icon="information-outline",
        event=EVENT_OBSERVATION,
        attr="battery",
        has_description=True,
        custom_fn=lambda cnv, device: (None, None)
        if None in (device.battery, device.solar_radiation)
        else cnv.battery_mode(device.battery.m, device.solar_radiation.m),
    ),
    SensorDescription(
        id="beaufort",
        name="Beaufort Scale",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="tailwind",
        event=EVENT_OBSERVATION,
        attr="wind_speed",
        custom_fn=lambda cnv, device: (None, None)
        if device.wind_speed is None
        else cnv.beaufort(device.wind_speed.m),
        has_description=True,
    ),
    SensorDescription(
        id="cloud_base",
        name="Cloud Base Altitude",
        icon="weather-cloudy",
        unit_m=ALTITUDE_METERS,
        unit_i=ALTITUDE_FEET,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        attr="calculate_cloud_base",
        decimals=(0, 0),
        inputs=("altitude",),
    ),
    SensorDescription(
        id="delta_t",
        name="Delta T",
        unit_m=TEMP_CELSIUS,
        unit_m_cnv="delta_degC",
        unit_i=TEMP_FAHRENHEIT,
        unit_i_cnv="delta_degF",
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        decimals=(1, 1),
    ),
    SensorDescription(
        id="dewpoint",
        name="Dew Point",
        unit_m=TEMP_CELSIUS,
        unit_i=TEMP_FAHRENHEIT,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="thermometer-lines",
        event=EVENT_OBSERVATION,
        extra_att=True,
        show_min_att=True,
        attr="dew_point_temperature",
        decimals=(1, 1),
    ),
    SensorDescription(
        id="dewpoint_description",
        name="Dewpoint Comfort Level",
        icon="text-box-outline",
        event=EVENT_OBSERVATION,
        attr="dew_point_temperature",
        custom_fn=lambda cnv, device: None
        if device.dew_point_temperature is None
        else cnv.dewpoint_level(device.dew_point_temperature.m, True),
    ),
    SensorDescription(
        id="feelslike",
        name="Feels Like Temperature",
        unit_m=TEMP_CELSIUS,
        unit_i=TEMP_FAHRENHEIT,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        attr="air_temperature",
        decimals=(1, 1),
        custom_fn=lambda cnv, device, wind_speed: None
        if wind_speed is None
        or None in (device.air_temperature, device.relative_humidity)
        else cnv.feels_like(
            device.air_temperature.m, device.relative_humidity.m, wind_speed
        ),
    ),
    SensorDescription(
        id="freezing_level",
        name="Freezing Level Altitude",
        icon="altimeter",
        unit_m=ALTITUDE_METERS,
        unit_i=ALTITUDE_FEET,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        attr="calculate_freezing_level",
        decimals=(0, 0),
        inputs=("altitude",),
    ),
    SensorDescription(
        id="illuminance",
        name="Illuminance",
        unit_m="lx",
        unit_i="lx",
        device_class=DEVICE_CLASS_ILLUMINANCE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        extra_att=True,
    ),
    SensorDescription(
        id="lightning_strike_count",
        name="Lightning Count",
        icon="weather-lightning",
        event=EVENT_OBSERVATION,
    ),
    SqlSensorDescription(
        id="lightning_strike_count_1hr",
        name="Lightning Count (Last hour)",
        icon="weather-lightning",
        event=EVENT_OBSERVATION,
        attr="lightning_strike_count",
        sql_fn=lambda sql: sql.readLightningCount(1),
    ),
    SqlSensorDescription(
        id="lightning_strike_count_3hr",
        name="Lightning Count (3 hours)",
        icon="weather-lightning",
        event=EVENT_OBSERVATION,
        attr="lightning_strike_count",
        sql_fn=lambda sql: sql.readLightningCount(3),
    ),
    StorageSensorDescription(
        id="lightning_strike_count_today",
        name="Lightning Count (Today)",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-lightning",
        event=EVENT_OBSERVATION,
        extra_att=True,
        last_reset=True,
        attr="lightning_strike_count",
        storage_field="lightning_count_today",
    ),
    StorageSensorDescription(
        id="lightning_strike_distance",
        name="Lightning Distance",
        unit_m="km",
        unit_i="mi",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="flash",
        event=EVENT_OBSERVATION,
        attr="lightning_strike_average_distance",
        storage_field="last_lightning_distance",
    ),
    StorageSensorDescription(
        id="lightning_strike_energy",
        name="Lightning Energy",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="flash",
        event=EVENT_OBSERVATION,
        extra_att=True,
        attr="last_lightning_strike_event",
        storage_field="last_lightning_energy",
    ),
    StorageSensorDescription(
        id="lightning_strike_time",
        name="Last Lightning Strike",
        device_class=DEVICE_CLASS_TIMESTAMP,
        icon="clock-outline",
        event="lightning_strike_time",
        attr="last_lightning_strike_event",
        storage_field="last_lightning_time",
        cnv_fn=lambda cnv, val: cnv.utc_from_timestamp(val),
    ),
    SensorDescription(
        id="precipitation_type",
        name="Precipitation Type",
        icon="weather-rainy",
        event=EVENT_OBSERVATION,
        custom_fn=lambda cnv, device: None
        if device.precipitation_type is None
        else cnv.rain_type(device.precipitation_type.value),
    ),
    SensorDescription(
        id="pressure_trend",
        name="Pressure Trend",
        icon="trending-up",
        event=EVENT_OBSERVATION,
        attr="station_pressure",
    ),
    StorageSensorDescription(
        id="rain_duration_today",
        name="Rain Duration (Today)",
        unit_m="min",
        unit_i="min",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="timeline-clock-outline",
        event=EVENT_OBSERVATION,
        extra_att=True,
        last_reset=True,
        attr="rain_accumulation_previous_minute",
        storage_field="rain_duration_today",
    ),
    StorageSensorDescription(
        id="rain_duration_yesterday",
        name="Rain Duration (Yesterday)",
        unit_m="min",
        unit_i="min",
        icon="timeline-clock-outline",
        event=EVENT_OBSERVATION,
        attr="rain_accumulation_previous_minute",
        storage_field="rain_duration_yesterday",
    ),
    SensorDescription(
        id="rain_intensity",
        name="Rain Intensity",
        icon="text-box-outline",
        event=EVENT_OBSERVATION,
        attr="rain_accumulation_previous_minute",
        custom_fn=lambda cnv, device: None
        if device.rain_rate is None
        else cnv.rain_intensity(device.rain_rate.m),
    ),
    SensorDescription(
        id="rain_rate",
        name="Rain Rate",
        unit_m="mm/h",
        unit_m_cnv="mm/h",
        unit_i="in/h",
        unit_i_cnv="in/h",
        device_class=DEVICE_CLASS_PRECIPITATION_INTENSITY,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-pouring",
        event=EVENT_OBSERVATION,
        extra_att=True,
        decimals=(2, 2),
    ),
    StorageSensorDescription(
        id="rain_start_time",
        name="Last Rain start",
        device_class=DEVICE_CLASS_TIMESTAMP,
        icon="clock-outline",
        event="rain_start_time",
        attr="last_rain_start_event",
        storage_field="rain_start",
        cnv_fn=lambda cnv, val: cnv.utc_from_timestamp(val),
    ),
    StorageSensorDescription(
        id="rain_today",
        name="Rain Today",
        unit_m="mm",
        unit_i="in",
        device_class=DEVICE_CLASS_PRECIPITATION,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-pouring",
        event=EVENT_OBSERVATION,
        last_reset=True,
        attr="rain_accumulation_previous_minute",
        storage_field="rain_today",
        cnv_fn=lambda cnv, val: cnv.rain(val),
    ),
    StorageSensorDescription(
        id="rain_yesterday",
        name="Rain Yesterday",
        unit_m="mm",
        unit_i="in",
        icon="weather-pouring",
        device_class=DEVICE_CLASS_PRECIPITATION,
        event=EVENT_OBSERVATION,
        attr="rain_accumulation_previous_minute",
        storage_field="rain_yesterday",
        cnv_fn=lambda cnv, val: cnv.rain(val),
    ),
    SensorDescription(
        id="relative_humidity",
        name="Humidity",
        unit_m="%",
        unit_m_cnv=NO_CONVERSION,
        unit_i="%",
        unit_i_cnv=NO_CONVERSION,
        device_class=DEVICE_CLASS_HUMIDITY,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        extra_att=True,
        show_min_att=True,
    ),
    SensorDescription(
        id="sealevel_pressure",
        name="Sea Level Pressure",
        unit_m="hPa",
        unit_i="inHg",
        device_class=DEVICE_CLASS_PRESSURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        extra_att=True,
        show_min_att=True,
        attr="calculate_sea_level_pressure",
        decimals=(2, 3),
        inputs=("altitude",),
    ),
    SensorDescription(
        id="solar_radiation",
        name="Solar Radiation",
        unit_m="W/m²",
        unit_i="W/m²",
        device_class=DEVICE_CLASS_IRRADIANCE,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="solar-power",
        event=EVENT_OBSERVATION,
        extra_att=True,
    ),
    SensorDescription(
        id="station_pressure",
        name="Station Pressure",
        unit_m="hPa",
        unit_i="inHg",
        device_class=DEVICE_CLASS_PRESSURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        decimals=(2, 3),
    ),
    SensorDescription(
        id="temperature_description",
        name="Temperature Level",
        icon="text-box-outline",
        event=EVENT_OBSERVATION,
        attr="air_temperature",
        custom_fn=lambda cnv, device: None
        if device.air_temperature is None
        else cnv.temperature_level(device.air_temperature.m),
    ),
    SensorDescription(
        id="uv",
        name="UV Index",
        unit_m=UV_INDEX,
        unit_i=UV_INDEX,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-sunny-alert",
        event=EVENT_OBSERVATION,
        extra_att=True,
    ),
    SensorDescription(
        id="uv_description",
        name="UV Level",
        icon="text-box-outline",
        event=EVENT_OBSERVATION,
        attr="uv",
        custom_fn=lambda cnv, device: cnv.uv_level(device.uv),
    ),
    SensorDescription(
        id="visibility",
        name="Visibility",
        unit_m="km",
        unit_i="nmi",
        device_class=DEVICE_CLASS_DISTANCE,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="eye",
        event=EVENT_OBSERVATION,
        attr="air_temperature",
        custom_fn=lambda cnv, device, elevation: None
        if None in (device.air_temperature, device.relative_humidity)
        else cnv.visibility(
            elevation, device.air_temperature.m, device.relative_humidity.m
        ),
    ),
    SensorDescription(
        id="wbgt",
        name="Wet Bulb Globe Temperature",
        unit_m=TEMP_CELSIUS,
        unit_i=TEMP_FAHRENHEIT,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        attr="wet_bulb_temperature",
        decimals=(1, 1),
        custom_fn=lambda cnv, device, solar_radiation: None
        if None
        in (device.air_temperature, device.relative_humidity, device.station_pressure)
        else cnv.wbgt(
            device.air_temperature.m,
            device.relative_humidity.m,
            device.station_pressure.m,
            solar_radiation,
        ),
    ),
    SensorDescription(
        id="wetbulb",
        name="Wet Bulb Temperature",
        unit_m=TEMP_CELSIUS,
        unit_i=TEMP_FAHRENHEIT,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        event=EVENT_OBSERVATION,
        attr="wet_bulb_temperature",
        decimals=(1, 1),
    ),
    SensorDescription(
        id="wind_bearing",
        name="Wind Bearing",
        unit_m="°",
        unit_i="°",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="compass",
        event=EVENT_RAPID_WIND,
        attr="wind_direction",
    ),
    SensorDescription(
        id="wind_bearing_avg",
        name="Wind Bearing Avg",
        unit_m="°",
        unit_i="°",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="compass",
        event=EVENT_OBSERVATION,
        attr="wind_direction",
    ),
    SensorDescription(
        id="wind_direction",
        name="Wind Direction",
        icon="compass-outline",
        event=EVENT_RAPID_WIND,
    ),
    SensorDescription(
        id="wind_direction_avg",
        name="Wind Direction Avg",
        icon="compass-outline",
        event=EVENT_OBSERVATION,
        attr="wind_direction",
        custom_fn=lambda cnv, device: None
        if device.wind_direction is None
        else cnv.direction(device.wind_direction.m),
    ),
    SensorDescription(
        id="wind_gust",
        name="Wind Gust",
        unit_m="m/s",
        unit_i="mph",
        device_class=DEVICE_CLASS_WIND_SPEED,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-windy",
        event=EVENT_OBSERVATION,
        extra_att=True,
        decimals=(1, 2),
    ),
    SensorDescription(
        id="wind_lull",
        name="Wind Lull",
        unit_m="m/s",
        unit_i="mph",
        device_class=DEVICE_CLASS_WIND_SPEED,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-windy-variant",
        event=EVENT_OBSERVATION,
        extra_att=True,
        decimals=(1, 2),
    ),
    SensorDescription(
        id="wind_speed",
        name="Wind Speed",
        unit_m="m/s",
        unit_i="mph",
        device_class=DEVICE_CLASS_WIND_SPEED,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-windy",
        event=EVENT_RAPID_WIND,
        decimals=(1, 2),
    ),
    SensorDescription(
        id="wind_speed_avg",
        name="Wind Speed Avg",
        unit_m="m/s",
        unit_i="mph",
        device_class=DEVICE_CLASS_WIND_SPEED,
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-windy-variant",
        event=EVENT_OBSERVATION,
        extra_att=True,
        attr="wind_average",
        decimals=(1, 2),
    ),
    SensorDescription(
        id="solar_elevation",
        name="Solar Elevation",
        unit_m="°",
        unit_i="°",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="angle-acute",
        event=EVENT_OBSERVATION,
        attr="solar_radiation",
        custom_fn=lambda cnv, latitude, longitude: None
        if None in (latitude, longitude)
        else cnv.solar_elevation(latitude, longitude)
    ),
    SensorDescription(
        id="solar_insolation",
        name="Solar Insolation",
        unit_m="W/m²",
        unit_i="W/m²",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="solar-power",
        event=EVENT_OBSERVATION,
        attr="solar_radiation",
        custom_fn=lambda cnv, elevation, latitude, longitude: None
        if None in (elevation, latitude, longitude)
        else cnv.solar_insolation(elevation, latitude, longitude)
    ),
    SensorDescription(
        id="zambretti_number",
        name="Zambretti Number",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="vector-bezier",
        event=EVENT_OBSERVATION,
        attr="station_pressure",
        custom_fn=lambda cnv, latitude, wind_direction_avg, p_hi, p_lo, pressure_trend, sealevel_pressure: None
        if None in (latitude, wind_direction_avg, p_hi, p_lo, pressure_trend, sealevel_pressure)
        else cnv.zambretti_value(latitude, wind_direction_avg, p_hi, p_lo, pressure_trend, sealevel_pressure)
    ),
    SensorDescription(
        id="zambretti_text",
        name="Zambretti Text",
        icon="vector-bezier",
        event=EVENT_OBSERVATION,
        attr="station_pressure",
        custom_fn=lambda cnv, zambretti_value: None
        if zambretti_value is None
        else cnv.zambretti_forecast(zambretti_value),
    ),
    SensorDescription(
        id="fog_probability",
        name="Fog Probability",
        unit_m="%",
        unit_i="%",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="weather-fog",
        event=EVENT_OBSERVATION,
        attr="relative_humidity",
        custom_fn=lambda cnv, solar_elevation, wind_speed, humidity, dew_point, air_temperature: 0
        if None in (solar_elevation, wind_speed, humidity, dew_point, air_temperature)
        else cnv.fog_probability(solar_elevation, wind_speed, humidity, dew_point, air_temperature),
    ),
    SensorDescription(
        id="snow_probability",
        name="Snow Probability",
        unit_m="%",
        unit_i="%",
        state_class=STATE_CLASS_MEASUREMENT,
        icon="snowflake",
        event=EVENT_OBSERVATION,
        attr="relative_humidity",
        custom_fn=lambda cnv, device, freezing_level, cloud_base, elevation: None
        if None in (device.air_temperature, device.dew_point_temperature, device.wet_bulb_temperature, freezing_level, cloud_base)
        else cnv.snow_probability(device.air_temperature.m, freezing_level, cloud_base, device.dew_point_temperature.m, device.wet_bulb_temperature.m, elevation)
    ),

    SensorDescription(
        id="current_conditions",
        name="Current Conditions",
        icon="weather-partly-snowy-rainy",
        event=EVENT_OBSERVATION,
        attr="rain_rate",
        custom_fn=lambda cnv, lightning_strike_count_1hr, precipitation_type, rain_rate, wind_speed, solar_elevation, solar_radiation, solar_insolation, snow_probability, fog_probability: "clear-night"
        if None in (lightning_strike_count_1hr, precipitation_type, rain_rate, wind_speed, solar_elevation, solar_radiation, solar_insolation, snow_probability, fog_probability)
        else cnv.current_conditions(lightning_strike_count_1hr, precipitation_type, rain_rate, wind_speed, solar_elevation, solar_radiation, solar_insolation, snow_probability, fog_probability)
    ),
)

HUB_SENSORS: tuple[BaseSensorDescription, ...] = (STATUS_SENSOR,)

FORECAST_SENSORS: tuple[BaseSensorDescription, ...] = (
    SensorDescription(
        id=FORECAST_ENTITY,
        name="Weather",
        icon="chart-box-outline",
        event=EVENT_FORECAST,
    ),
)

OBSOLETE_SENSORS = ["uptime"]
