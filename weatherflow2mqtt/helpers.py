"""Several Helper Functions."""
from __future__ import annotations

import datetime as dt
import time
import json
import logging
import math
from typing import Any

import yaml

from .const import (
    BATTERY_MODE_DESCRIPTION,
    EXTERNAL_DIRECTORY,
    SUPPORTED_LANGUAGES,
    UNITS_IMPERIAL,
)

_LOGGER = logging.getLogger(__name__)

UTC = dt.timezone.utc
NO_CONVERSION = object()


def no_conversion_to_none(val: Any) -> Any | None:
    return None if val is NO_CONVERSION else val


def truebool(val: Any | None) -> bool:
    """Return `True` if the value passed in matches a "True" value, otherwise `False`.

    "True" values are: 'true', 't', 'yes', 'y', 'on' or '1'.
    """
    return val is not None and str(val).lower() in ("true", "t", "yes", "y", "on", "1")


def read_config() -> list[str] | None:
    """Read the config file to look for sensors."""
    try:
        filepath = f"{EXTERNAL_DIRECTORY}/config.yaml"
        with open(filepath, "r") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            sensors = data.get("sensors")

            return sensors

    except FileNotFoundError:
        return None
    except Exception as e:
        _LOGGER.error("Could not read config.yaml file. Error message: %s", e)
        return None


class ConversionFunctions:
    """Class to help with converting from different units."""

    def __init__(self, unit_system: str, language: str) -> None:
        """Initialize Conversion Function."""
        self.unit_system = unit_system
        self.translations = self.get_language_file(language)

    def get_language_file(self, language: str) -> dict[str, dict[str, str]] | None:
        """Return the language file json array."""
        filename = (
            f"translations/{language if language in SUPPORTED_LANGUAGES else 'en'}.json"
        )

        try:
            with open(filename, "r") as json_file:
                return json.load(json_file)
        except FileNotFoundError as e:
            _LOGGER.error("Could not read language file. Error message: %s", e)
            return None
        except Exception as e:
            _LOGGER.error("Could not read language file. Error message: %s", e)
            return None

    def temperature(self, value) -> float:
        """Convert Temperature Value."""
        if value is not None:
            if self.unit_system == UNITS_IMPERIAL:
                return round((value * 9 / 5) + 32, 1)
            return round(value, 1)

        _LOGGER.error(
            "FUNC: temperature ERROR: Temperature value was reported as NoneType. Check the sensor"
        )

    def pressure(self, value) -> float:
        """Convert Pressure Value."""
        if value is not None:
            if self.unit_system == UNITS_IMPERIAL:
                return round(value * 0.02953, 3)
            return round(value, 2)

        _LOGGER.error(
            "FUNC: pressure ERROR: Pressure value was reported as NoneType. Check the sensor"
        )

    def speed(self, value, kmh=False) -> float:
        """Convert Wind Speed."""
        if value is not None:
            if self.unit_system == UNITS_IMPERIAL:
                return round(value * 2.2369362920544, 2)
            if kmh:
                return round((value * 18 / 5), 1)
            return round(value, 1)

        _LOGGER.error(
            "FUNC: speed ERROR: Wind value was reported as NoneType. Check the sensor"
        )

    def distance(self, value) -> float:
        """Convert distance."""
        if value is not None:
            if self.unit_system == UNITS_IMPERIAL:
                return round(value / 1.609344, 2)
            return value

        _LOGGER.error(
            "FUNC: distance ERROR: Lightning Distance value was reported as NoneType. Check the sensor"
        )

    def rain(self, value) -> float:
        """Convert rain."""
        if value is not None:
            if self.unit_system == UNITS_IMPERIAL:
                return round(value * 0.0393700787, 2)
            return round(value, 2)

        _LOGGER.error(
            "FUNC: rain ERROR: Rain value was reported as NoneType. Check the sensor"
        )

    def rain_type(self, value) -> str:
        """Convert rain type."""
        type_array = ["none", "rain", "hail", "heavy"]
        try:
            precip_type = type_array[int(value)]
            return self.translations["precip_type"][precip_type]
        except IndexError:
            _LOGGER.warning("VALUE is: %s", value)
            return f"Unknown - {value}"

    def direction(self, value) -> str:
        """Return directional Wind Direction string."""
        if value is None:
            return "N"

        direction_array = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
            "N",
        ]
        direction_str = direction_array[int((value + 11.25) / 22.5)]
        return self.translations["wind_dir"][direction_str]

    def dewpoint(self, temperature, humidity, no_conversion=False):
        """Return Dewpoint."""
        if temperature is not None and humidity is not None:
            dewpoint_c = round(
                243.04
                * (
                    math.log(humidity / 100)
                    + ((17.625 * temperature) / (243.04 + temperature))
                )
                / (
                    17.625
                    - math.log(humidity / 100)
                    - ((17.625 * temperature) / (243.04 + temperature))
                ),
                1,
            )
            if no_conversion:
                return dewpoint_c
            return self.temperature(dewpoint_c)

        _LOGGER.error(
            "FUNC: dewpoint ERROR: Temperature and/or Humidity value was reported as NoneType. Check the sensor"
        )

    def absolute_humidity(self, temp, humidity):
        """Return Absolute Humidity.

        Grams of water per cubic meter of air (g/m^3)
        Input:
            Temperature in Celcius
            Relative Humidity in percent
        AH = (1320.65/TK)*RH*(10**((7.4475*(TK-273.14))/(TK-39.44))
            where:
              AH is Absolute Humidity g/m^3
              RH is Relative Humidity in range of 0.0 - 1.0.  i.e. 25% RH is 0.25
              TK is Temperature in Kelvin
        """
        if temp is None or humidity is None:
            return None

        # Convert Celcius to Kelvin for temperature
        TK = temp + 273.16
        # Format Relative Humidity
        RH = humidity / 100
        # Absolute Humidity Estimation is fairly acurate between (5C - 20C) (41F - 122F)
        AH = (1320.65 / TK) * RH * (10 ** ((7.4475 * (TK - 273.14)) / (TK - 39.44)))

        """
        # lf/ft^3 is too small a value for that unit, will pass metric units
        # just like Solar Radiation
        # Leaving conversion here for future reference
        if self._unit_system == UNITS_IMPERIAL:
            # (g/m^3 * 0.000062) converts to lb/ft^3
            return round(AH * 0.000062, 6)
        """
        return round(AH, 2)

    def rain_intensity(self, rain_rate) -> str:
        """Return a descriptive value of the rain rate.

        VERY LIGHT: < 0.25 mm/hour
        LIGHT: ≥ 0.25, < 1.0 mm/hour
        MODERATE: ≥ 1.0, < 4.0 mm/hour
        HEAVY: ≥ 4.0, < 16.0 mm/hour
        VERY HEAVY: ≥ 16.0, < 50 mm/hour
        EXTREME: > 50.0 mm/hour
        """
        if rain_rate == 0:
            intensity = "NONE"
        elif rain_rate < 0.25:
            intensity = "VERYLIGHT"
        elif rain_rate < 1:
            intensity = "LIGHT"
        elif rain_rate < 4:
            intensity = "MODERATE"
        elif rain_rate < 16:
            intensity = "HEAVY"
        elif rain_rate < 50:
            intensity = "VERYHEAVY"
        else:
            intensity = "EXTREME"

        return self.translations["rain_intensity"][intensity]

    def feels_like(self, temperature, humidity, windspeed):
        """Calculate feel like temperature."""
        if temperature is None or humidity is None or windspeed is None:
            return 0

        e_value = (
            humidity * 0.06105 * math.exp((17.27 * temperature) / (237.7 + temperature))
        )
        feelslike_c = temperature + 0.348 * e_value - 0.7 * windspeed - 4.25
        return self.temperature(feelslike_c)

    def visibility(self, elevation, temp, humidity):
        """Return the visibility.

        Input:
            Elevation in Meters
            Temperature in Celcius
            Humidity in percent
        """
        if temp is None or elevation is None or humidity is None:
            return None

        dewpoint_c = self.dewpoint(temp, humidity, True)
        # Set minimum elevation for cases of stations below sea level
        if elevation > 2:
            elv_min = float(elevation)
        else:
            elv_min = float(2)

        # Max possible visibility to horizon (units km)
        mv = float(3.56972 * math.sqrt(elv_min))

        # Percent reduction based on quatity of water in air (no units)
        # 76 percent of visibility variation can be accounted for by humidity accourding to US-NOAA.
        pr_a = float((1.13 * abs(temp - dewpoint_c) - 1.15) / 10)
        if pr_a > 1:
            # Prevent visibility exceeding maximum distance
            pr = float(1)
        elif pr_a < 0.025:
            # Prevent visibility below minimum distance
            pr = float(0.025)
        else:
            pr = pr_a

        # Visibility in km to horizon
        vis = float(mv * pr)

        if self.unit_system == UNITS_IMPERIAL:
            # Originally was in nautical miles;
            # HA displays miles as imperial, therfore converted to miles
            return round(vis / 1.609344, 1)
        return round(vis, 1)

    def wetbulb(self, temp, humidity, pressure, no_conversion=False):
        """Return Wet Bulb Temperature.

        Converted from a JS formula made by Gary W Funk
        Input:
            Temperature in Celcius
            Humdity in Percent
            Station Pressure in MB
        """
        if temp is None or humidity is None or pressure is None:
            return None

        t = float(temp)
        rh = float(humidity)
        p = float(pressure)

        # Variables
        edifference = 1
        twguess = 0
        previoussign = 1
        incr = 10
        es = 6.112 * math.exp(17.67 * t / (t + 243.5))
        e2 = es * (rh / 100)

        while abs(edifference) > 0.005:
            ewguess = 6.112 * math.exp((17.67 * twguess) / (twguess + 243.5))
            eguess = ewguess - p * (t - twguess) * 0.00066 * (1 + (0.00115 * twguess))
            edifference = e2 - eguess
            if edifference == 0:
                break

            if edifference < 0:
                cursign = -1
                if cursign != previoussign:
                    previoussign = cursign
                    incr = incr / 10
                else:
                    incr = incr
            else:
                cursign = 1
                if cursign != previoussign:
                    previoussign = cursign
                    incr = incr / 10
                else:
                    incr = incr

            twguess = twguess + incr * previoussign

        if no_conversion:
            return twguess
        return self.temperature(twguess)

    def wbgt(self, temp, humidity, pressure, solar_radiation):
        """Return Wet Bulb Globe Temperature.

        This is a way to show heat stress on the human body.
        Input:
            Temperature in Celcius
            Humdity in Percent
            Station Pressure in MB
            Solar Radiation in Wm^2
        WBGT = 0.7Twb + 0.2Tg + 0.1Ta
          where:
            WBGT is Wet Bulb Globe Temperature in C
            Twb is Wet Bulb Temperature in C
            Tg is Black Globe Temperature in C (estimation)
            Ta is Air Temperature (dry bulb)
        Tg = 0.01498SR + 1.184Ta - 0.0789Rh - 2.739
          where:
            Tg is Black Globe Temperature in C (estimation)
            SR is Solar Radiation in Wm^2
            Ta is Air Temperature in C
            Rh is Relative Humidity in %
        WBGT = 0.7Twb + 0.002996SR + 0.3368Ta -0.01578Rh - 0.5478
        """
        if (
            temp is None
            or humidity is None
            or pressure is None
            or solar_radiation is None
        ):
            return None

        ta = float(temp)
        twb = self.wetbulb(temp, humidity, pressure, True)
        rh = float(humidity)
        # p = float(pressure)
        sr = float(solar_radiation)

        wbgt = round(0.7 * twb + 0.002996 * sr + 0.3368 * ta - 0.01578 * rh - 0.5478, 1)

        if self.unit_system == UNITS_IMPERIAL:
            return self.temperature(wbgt)
        return wbgt

    def battery_level(self, battery, is_tempest):
        """Return battery percentage.

        Input:
            Voltage in Volts DC (depends on the weather station type, see below)
            is_tempest in Boolean
        Tempest:
            Battery voltage range is 1.8 to 2.85 Vdc
                > 2.80 is capped at 100%
                < 1.8 is capped at 0%
        Air:
            4 AA batteries (2 in series, then parallel for 2 sets)
            Battery voltage range is 1.2(x2) => 2.4 to 1.8(x2) => 3.6 Vdc
            (lowered to 3.5 based on observation)
                > 3.5 is capped at 100%
                < 2.4 is capped at 0%
        Sky:
            8 AA batteries (2 in series, then parallel for 4 sets)
            Battery voltage range is 1.2(x2) => 2.4 to 1.8(x2) => 3.6 Vdc
            (lowered to 3.5 based on observation)
                > 3.5 is capped at 100%
                < 2.4 is capped at 0%
        """
        if battery is None:
            return None

        if is_tempest:
            if battery > 2.80:
                # Cap max at 100%
                pb = int(100)
            elif battery < 1.8:
                # Min voltage is 1.8
                pb = int(0)
            else:
                # pb = battery - 1.8
                # Multiply by 100 to get in percentage
                pb = int((battery - 1.8) * 100)
        else:
            if battery > 3.50:
                # Cap max at 100%
                pb = int(100)
            elif battery < 2.4:
                # Min voltage is 2.4
                pb = int(0)
            else:
                # pb = (battery - 2.4)/1.1
                # Multiply by 100 to get in percentage
                pb = int(((battery - 2.4) / 1.1) * 100)

        return pb

    def battery_mode(self, voltage, solar_radiation):
        """Return battery operating mode.

        Input:
            Voltage in Volts DC (depends on the weather station type, see below)
            is_tempest in Boolean
            solar_radiation in W/M^2 (used to determine if battery is in a charging state)
        Tempest:
            # https://help.weatherflow.com/hc/en-us/articles/360048877194-Solar-Power-Rechargeable-Battery
        AIR & SKY:
            The battery mode does not apply to AIR & SKY Units
        """
        if voltage is None or solar_radiation is None:
            return None

        if voltage >= 2.455:
            # Mode 0 (independent of charging or discharging at this voltage)
            batt_mode = int(0)
        elif voltage <= 2.355:
            # Mode 3 (independent of charging or discharging at this voltage)
            batt_mode = int(3)
        elif solar_radiation > 100:
            # Assume charging and voltage is raising
            if voltage >= 2.41:
                # Mode 1
                batt_mode = int(1)
            elif voltage > 2.375:
                # Mode 2
                batt_mode = int(2)
            else:
                # Mode 3
                batt_mode = int(3)
        else:
            # Assume discharging and voltage is lowering
            if voltage > 2.415:
                # Mode 0
                batt_mode = int(0)
            elif voltage > 2.39:
                # Mode 1
                batt_mode = int(1)
            elif voltage > 2.355:
                # Mode 2
                batt_mode = int(2)
            else:
                # Mode 3
                batt_mode = int(3)

        mode_description = BATTERY_MODE_DESCRIPTION[batt_mode]
        return batt_mode, mode_description

    def beaufort(self, wind_speed):
        """Return Beaufort Scale value based on Wind Speed."""
        if wind_speed is None:
            return 0, self.translations["beaufort"][str(0)]

        if wind_speed > 32.7:
            bft_value = 12
        elif wind_speed >= 28.5:
            bft_value = 11
        elif wind_speed >= 24.5:
            bft_value = 10
        elif wind_speed >= 20.8:
            bft_value = 9
        elif wind_speed >= 17.2:
            bft_value = 8
        elif wind_speed >= 13.9:
            bft_value = 7
        elif wind_speed >= 10.8:
            bft_value = 6
        elif wind_speed >= 8.0:
            bft_value = 5
        elif wind_speed >= 5.5:
            bft_value = 4
        elif wind_speed >= 3.4:
            bft_value = 3
        elif wind_speed >= 1.6:
            bft_value = 2
        elif wind_speed >= 0.3:
            bft_value = 1
        else:
            bft_value = 0

        bft_text = self.translations["beaufort"][str(bft_value)]

        return bft_value, bft_text

    def dewpoint_level(self, dewpoint: float, is_metric: bool = None) -> str:
        """Return text based comfort level, based on dewpoint F value."""
        if dewpoint is None:
            return "no-data"
        if is_metric is None:
            is_metric = self.unit_system != UNITS_IMPERIAL

        if is_metric:
            dewpoint = (dewpoint * 9 / 5) + 32

        if dewpoint >= 80:
            return self.translations["dewpoint"]["severely-high"]
        if dewpoint >= 75:
            return self.translations["dewpoint"]["miserable"]
        if dewpoint >= 70:
            return self.translations["dewpoint"]["oppressive"]
        if dewpoint >= 65:
            return self.translations["dewpoint"]["uncomfortable"]
        if dewpoint >= 60:
            return self.translations["dewpoint"]["ok-for-most"]
        if dewpoint >= 55:
            return self.translations["dewpoint"]["comfortable"]
        if dewpoint >= 50:
            return self.translations["dewpoint"]["very-comfortable"]
        if dewpoint >= 30:
            return self.translations["dewpoint"]["somewhat-dry"]
        if dewpoint >= 0.5:
            return self.translations["dewpoint"]["dry"]
        if dewpoint >= 0:
            return self.translations["dewpoint"]["very-dry"]

        return self.translations["dewpoint"]["undefined"]

    def temperature_level(self, temperature_c):
        """Return text based comfort level, based on Air Temperature value."""
        if temperature_c is None:
            return "no-data"

        temperature = (temperature_c * 9 / 5) + 32

        if temperature >= 104:
            return self.translations["temperature"]["inferno"]
        if temperature >= 95:
            return self.translations["temperature"]["very-hot"]
        if temperature >= 86:
            return self.translations["temperature"]["hot"]
        if temperature >= 77:
            return self.translations["temperature"]["warm"]
        if temperature >= 68:
            return self.translations["temperature"]["nice"]
        if temperature >= 59:
            return self.translations["temperature"]["cool"]
        if temperature >= 41:
            return self.translations["temperature"]["chilly"]
        if temperature >= 32:
            return self.translations["temperature"]["cold"]
        if temperature >= 20:
            return self.translations["temperature"]["freezing"]
        if temperature <= 20:
            return self.translations["temperature"]["fridged"]

        return self.translations["temperature"]["undefined"]

    def uv_level(self, uvi):
        """Return text based UV Description."""
        if uvi is None:
            return "no-data"

        if uvi >= 10.5:
            return self.translations["uv"]["extreme"]
        if uvi >= 7.5:
            return self.translations["uv"]["very-high"]
        if uvi >= 5.5:
            return self.translations["uv"]["high"]
        if uvi >= 2.5:
            return self.translations["uv"]["moderate"]
        if uvi > 0:
            return self.translations["uv"]["low"]

        return self.translations["uv"]["none"]

    def utc_from_timestamp(self, timestamp: int) -> str:
        """Return a UTC time from a timestamp."""
        if not timestamp:
            return None

        # Convert to String as MQTT does not like data objects
        dt_obj = dt.datetime.utcfromtimestamp(timestamp).replace(tzinfo=UTC)
        utc_offset = dt_obj.strftime("%z")
        utc_string = f"{utc_offset[:3]}:{utc_offset[3:]}"
        dt_str = dt_obj.strftime("%Y-%m-%dT%H:%M:%S")

        return f"{dt_str}{utc_string}"

    def utc_last_midnight(self) -> str:
        """Return UTC Time for last midnight."""
        midnight = dt.datetime.combine(dt.datetime.today(), dt.time.min)
        midnight_ts = dt.datetime.timestamp(midnight)
        midnight_dt = self.utc_from_timestamp(midnight_ts)
        return midnight_dt

    def solar_elevation(self, latitude, longitude):
        """ Return Sun Elevation in Degrees with respect to the Horizon.

        Input:
            Latitude in Degrees and fractional degrees (no docker variable yet)
            Longitude in Degrees and fractional degrees (no docker variable yet)
            Local Time
            UTC Time
        Where:
            jd is Julian Date (Day of Year only), then Julian Date + Fractional True
            lt is Local Time (####) 24 hour time, no colon
            tz is Time Zone Offset (ie -7 from UTC)
            beta is Beta for EOT
            lstm is Local Standard Time Meridian
            eot is Equation of Time
            tc is Time Correction Factor
            lst is Local Solar Time
            h is Hour Angle
            dec is Declination
            se is Solar Elevation
            ** All Trigonometry Fuctions need Degrees converted to Radians **
            ** The assumption is made that correct local time is established **
        """
        if latitude is None or longitude is None:
            return None

        cos = math.cos
        sin = math.sin
        asin = math.asin
        radians = math.radians
        degrees = math.degrees
        jd = time.localtime(time.time()).tm_yday
        hr = time.localtime(time.time()).tm_hour
        min = time.localtime(time.time()).tm_min
        lt = hr + min/60
        tz = time.localtime(time.time()).tm_gmtoff/3600
        jd = jd + lt/24
        beta = (360/365) * (jd - 81)
        lstm = 15 * tz
        eot = (9.87*(sin(radians(beta*2)))) - (7.53*(cos(radians(beta)))) - (1.5*(sin(radians(beta))))
        tc = (4 * (longitude - lstm)) + eot
        lst = lt + tc/60
        h = 15 * (lst - 12)
        dec = cos(radians(((jd) + 10) * (360/365))) * (-23.44)
        se = degrees(asin(sin(radians(latitude)) * sin(radians(dec)) + cos(radians(latitude)) * cos(radians(dec)) * cos(radians(h))))
        se = round(se)

        return se

    def solar_insolation(self, elevation, latitude, longitude):
        """ Return Estimation of Solar Radiation at current sun elevation angle.

        Input:
            Elevation in Meters
            Latitude
            Longitude
        Where:
            sz is Solar Zenith in Degrees
            ah is (Station Elevation Compensation) Constant ah_a = 0.14, ah_h = Station elevation in km
            am is Air Mass of atmoshere between Station and Sun
            1353 W/M^2 is considered Solar Radiation at edge of atmoshere
            ** All Trigonometry Fuctions need Degrees converted to Radians **
        """
        if elevation is None or latitude is None or longitude is None:
            return None

        # Calculate Solar Elevation
        solar_elevation = self.solar_elevation(latitude, longitude)

        cos = math.cos
        sin = math.sin
        asin = math.asin
        radians = math.radians
        degrees = math.degrees
        se = solar_elevation
        sz = 90 - se
        ah_a = 0.14
        ah_h = elevation / 1000
        ah = ah_a * ah_h
        if se >= 0:
            am = 1/(cos(radians(sz)) + 0.50572*pow((96.07995 - sz),(-1.6364)))
            si = (1353 * ((1-ah)*pow(.7, pow(am, 0.678))+ah))*(sin(radians(se)))
        else:
            am = 1
            si = 0
        si = round(si)

        return si

    def zambretti_value(self, latitude, wind_dir, p_hi, p_lo, trend, press):
        """ Return local forecast number based on Zambretti Forecaster.
        Input:
            Sea Level Pressure in mB
            Pressure Trend 0 for Steady, >0 for Rising and <0 for Falling
            Latitude in Degrees
            All Time Sea Level Pressure High in mB
            All Time Sea Level Pressure Low in mB
            Wind Direction in Degrees - Converted to Cardinal further down)
        Where:
        """
        if (
            latitude is None
            or wind_dir is None
            or p_hi is None
            or p_lo is None
            or trend is None
            or press is None
        ):
            return None

        # Based off Beteljuice's Zambretti work; http://www.beteljuice.co.uk/zambretti/forecast.html
        # Northern = 1 or Southern = 2 hemisphere
        if latitude >= 0:
            z_where = 1
        else:
            z_where = 2
        # upper limits of your local 'weather window' Pulled from All Time Max
        # var z_baro_top = 1050; # upper limits of your local 'weather window' (1050.0 hPa for UK)
        z_baro_top = p_hi
        # lower limits of your local 'weather window' Pulled from All Time Min
        # var z_baro_bottom = 950;	// lower limits of your local 'weather window' (950.0 hPa for UK)
        z_baro_bottom = p_lo
        # range of pressure
        z_range = z_baro_top - z_baro_bottom
        # z_hpa is Sea Level Adjusted (Relative) barometer in hPa or mB
        z_hpa = press
        # z_month is current month as a number between 1 to 12
        z_month = dt.datetime.now()
        z_month = int(z_month.strftime("%m"))
        # True (1) for summer, False (0) for Winter (Northern Hemishere)
        z_season = (z_month >= 4 and  z_month <= 9)
        # z_wind is English windrose cardinal eg. N, NNW, NW etc.
        # NB. if calm a 'nonsense' value should be sent as z_wind (direction) eg. 1 or calm !
        z_wind = self.direction(wind_dir)
        # z_trend is barometer trend: 0 = no change, 1 = rise, 2 = fall
        # z_trend_threshold = 0.047248 if self.unit_system == UNITS_IMPERIAL else 1.6
        if float(trend) < 0:
            z_trend = 2
        elif float(trend) > 0:
            z_trend = 1
        else:
            z_trend = 0
        # A constant for the current location, will vary since range will adjust as the min and max pressure will update overtime
        z_constant = (z_range / 22)
        # Equivalents of Zambretti 'dial window' letters A - Z: 0=A
        rise_options  = [25,25,25,24,24,19,16,12,11,9,8,6,5,2,1,1,0,0,0,0,0,0]
        steady_options  = [25,25,25,25,25,25,23,23,22,18,15,13,10,4,1,1,0,0,0,0,0,0]
        fall_options =  [25,25,25,25,25,25,25,25,23,23,21,20,17,14,7,3,1,1,1,0,0,0]

        if z_where == 1:
            # North hemisphere
            if z_wind == "N":
                z_hpa += 6 / 100 * z_range
            elif z_wind == "NNE":
                z_hpa += 5 / 100 * z_range
            elif z_wind == "NE":
                z_hpa += 5 / 100 * z_range
            elif z_wind == "ENE":
                z_hpa += 2 / 100 * z_range
            elif z_wind == "E":
                z_hpa -= 0.5 / 100 * z_range
            elif z_wind == "ESE":
                z_hpa -= 2 / 100 * z_range
            elif z_wind == "SE":
                z_hpa -= 5 / 100 * z_range
            elif z_wind == "SSE":
                z_hpa -= 8.5 / 100 * z_range
            elif z_wind == "S":
                z_hpa -= 12 / 100 * z_range
            elif z_wind == "SSW":
                z_hpa -= 10 / 100 * z_range
            elif z_wind == "SW":
                z_hpa -= 6 / 100 * z_range
            elif z_wind == "WSW":
                z_hpa -= 4.5 / 100 * z_range
            elif z_wind == "W":
                z_hpa -= 3 / 100 * z_range
            elif z_wind == "WNW":
                z_hpa -= 0.5 / 100 * z_range
            elif z_wind == "NW":
                z_hpa += 1.5 / 100 * z_range
            elif z_wind == "NNW":
                z_hpa += 3 / 100 * z_range
            if z_season == 1:
                # if Summer
                if z_trend == 1:
                    # rising
                    z_hpa += 7 / 100 * z_range
                elif z_trend == 2:
                    # falling
                    z_hpa -= 7 / 100 * z_range
        else:
            # South hemisphere
            if z_wind == "S":
                z_hpa += 6 / 100 * z_range
            elif z_wind == "SSW":
                z_hpa += 5 / 100 * z_range
            elif z_wind == "SW":
                z_hpa += 5 / 100 * z_range
            elif z_wind == "WSW":
                z_hpa += 2 / 100 * z_range
            elif z_wind == "W":
                z_hpa -= 0.5 / 100 * z_range
            elif z_wind == "WNW":
                z_hpa -= 2 / 100 * z_range
            elif z_wind == "NW":
                z_hpa -= 5 / 100 * z_range
            elif z_wind == "NNW":
                z_hpa -= 8.5 / 100 * z_range
            elif z_wind == "N":
                z_hpa -= 12 / 100 * z_range
            elif z_wind == "NNE":
                z_hpa -= 10 / 100 * z_range
            elif z_wind == "NE":
                z_hpa -= 6 / 100 * z_range
            elif z_wind == "ENE":
                z_hpa -= 4.5 / 100 * z_range
            elif z_wind == "E":
                z_hpa -= 3 / 100 * z_range
            elif z_wind == "ESE":
                z_hpa -= 0.5 / 100 * z_range
            elif z_wind == "SE":
                z_hpa += 1.5 / 100 * z_range
            elif z_wind == "SSE":
                z_hpa += 3 / 100 * z_range
            if z_season == 0:
                # Winter
                if z_trend == 1:
                    # rising
                    z_hpa += 7 / 100 * z_range
                elif z_trend == 2:
                    # falling
                    z_hpa -= 7 / 100 * z_range
            # END North / South

        if z_hpa == z_baro_top:
            z_hpa = z_baro_top - 1
        z_option = math.floor((z_hpa - z_baro_bottom) / z_constant)

        if z_option < 0:
            z_option = 0

        if z_option > 21:
            z_option = 21

        if z_trend == 1:
            # rising
            z_number = rise_options[z_option]
        elif z_trend == 2:
            # falling
            z_number = fall_options[z_option]
        else:
            # must be 'steady'
            z_number = steady_options[z_option]

        return z_number

    def zambretti_forecast(self, z_num: int):
        """ Return local forecast text based on Zambretti Number from the zambretti_num function.
        Input:
            Zambretti Number from Zambretti function
        Where:
        """
        if z_num is None:
            return None

        # Zambretti Text Equivalents of Zambretti 'dial window' letters A - Z
        # Simplified array for Language Translations
        z_forecast = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
        z_text = ""
        z_text += z_forecast[int(z_num)]

        return self.translations["zambretti"][z_text]

    def fog_probability(self, solar_elevation, wind_speed, humidity, dew_point, air_temperature):
        """ Return probability of fog in percent.
        Input:
            Solar Elevation - determine daylight
            Wind Speed
            Humidity
            Dew Point
            Air Temperature
        Where:
        """
        if (
            solar_elevation is None
            or wind_speed is None
            or humidity is None
            or dew_point is None
            or air_temperature is None
        ):
            return None
        
        fog = 0
        diff = air_temperature - dew_point

        if solar_elevation >= 0:
            # daytime
            fog = fog - 15
        else:
            # fog is more common at night
            fog = fog + 10

        if wind_speed < 2.2352:
            # fog is more likely when it is calm (<5 mph / 2.2352 m/s)
            fog = fog + 20
        elif wind_speed < 4.4704:
            # it's more windy, fog is slightly less likely (<10 mph / 4.4704 m/s)
            fog = fog + 5
        else:
            # it's unlikely fog will form above 10 mph / 4.4704 m/s
            fog = fog - 20

        if humidity > 75 and humidity < 91:
            # high humidity
            fog = fog + 5
        elif humidity > 90:
            # higher humidity
            fog = fog + 10
        else:
            # humidity is still quite low
            fog = fog - 20

        if diff < 5.1 and diff > 3.9:
            # Diff between temp and dewpoint is less than 5'C and over 4'C")
            fog = fog + 5
        elif diff < 4.1 and diff > 2.5:
            # Diff between temp and dewpoint is less than 4'C and over 2.5'C")
            fog = fog + 10
        elif diff < 2.6 and diff > 1.9:
            # Diff between temp and dewpoint is less than 3'C and over 2'C")
            fog = fog + 15
        elif diff < 2.1 and diff > 0.9:
            # Diff between temp and dewpoint is less than 2'C and over 1'C")
            fog = fog + 20
        elif diff < 1:
            # Diff between temp and dewpoint is less than 1'C"
            fog = fog + 25
        else:
            fog = fog - 20

        # 75 is the maximum possible score
        if fog > 0:
            fog = (fog / 75) * 100
        else:
            fog = 0

        fog_probability = round(fog)

        return fog_probability

# *** Work in Progress * Commented out to fix Fog Probability ***
    def snow_probability(self, solar_elevation, wind_speed, humidity, dew_point, air_temperature):
        """ Return probability of snow in percent.
        Input:
            Air Temperature
            Freezing Level
            Cloud Base
            Dew Point
            Wet Bulb
            Station Height
        Where:
        """
        if (
            air_temperature is None
            or freeze is None
            or cloud_base is None
            or dew_point is None
        ):
            return None

        var temperature = msg.temperature
        var freezing_level = msg.freezing_level
        var cloud_base = msg.cloud_base
        var dew_point = msg.dew_point
        var wet_bulb = msg.wet_bulb
        var snow_line = freezing_level - 750 // 500 ft, 150 m
        var station_height = 325 // in feet for now

        var temperature = msg.temperature
        var dew_point = msg.dew_point
        var snow_possible = msg.snow
        var A = dew_point + temperature
        var snow_prob

        # Convert from F to C
        # 2.1C = 35.78F, 1C = 33.8F, 4.1C = 39.38F, -40F = -40C
        temperature = (temperature - 32) / 1.8
        dew_point = (dew_point - 32) / 1.8
        wet_bulb = (wet_bulb - 32) / 1.8

        if ((temperature <= 2.1) && (snow_line <= station_height) && (dew_point <= 1) && (wet_bulb <= 2.1) && (freezing_line <= cloud_base) && (temperature >= -40)):
             snow_prob = 80 - 10 * A
        else:
             snow_prob = 0

        snow_probability = Math.round(snow_prob)

        return snow_probability
