"""Several Helper Functions."""

import datetime
import time
import json
import math
from typing import OrderedDict
import logging
import yaml
from cmath import rect, phase
from math import gamma, radians, degrees

from weatherflow2mqtt.sqlite import SQLFunctions
from weatherflow2mqtt.__version__ import DB_VERSION
from weatherflow2mqtt.const import (
    DEVICE_STATUS,
    EXTERNAL_DIRECTORY,
    SUPPORTED_LANGUAGES,
    UNITS_IMPERIAL,
)

_LOGGER = logging.getLogger(__name__)


class ConversionFunctions:
    """Class to help with converting from different units."""

    def __init__(self, unit_system, translations):
        self._unit_system = unit_system
        self._translations = translations

    async def temperature(self, value) -> float:
        """Convert Temperature Value."""
        if value is not None:
            if self._unit_system == UNITS_IMPERIAL:
                return round((value * 9 / 5) + 32, 1)
            return round(value, 1)

        _LOGGER.error("FUNC: temperature ERROR: Temperature value was reported as NoneType. Check the sensor")

    async def pressure(self, value) -> float:
        """Convert Pressure Value."""
        if value is not None:
            if self._unit_system == UNITS_IMPERIAL:
                return round(value * 0.02953, 3)
            return round(value, 2)

        _LOGGER.error("FUNC: pressure ERROR: Pressure value was reported as NoneType. Check the sensor")

    async def speed(self, value, kmh=False) -> float:
        """Convert Wind Speed."""
        if value is not None:
            if self._unit_system == UNITS_IMPERIAL:
                return round(value * 2.2369362920544, 2)
            if kmh:
                return round((value * 18 / 5), 1)
            return round(value, 1)

        _LOGGER.error("FUNC: speed ERROR: Wind value was reported as NoneType. Check the sensor")

    async def distance(self, value) -> float:
        """Convert distance."""
        if value is not None:
            if self._unit_system == UNITS_IMPERIAL:
                return round(value / 1.609344, 2)
            return value

        _LOGGER.error("FUNC: distance ERROR: Lightning Distance value was reported as NoneType. Check the sensor")

    async def rain(self, value) -> float:
        """Convert rain."""
        if value is not None:
            if self._unit_system == UNITS_IMPERIAL:
                return round(value * 0.0393700787, 2)
            return round(value, 2)

        _LOGGER.error("FUNC: rain ERROR: Rain value was reported as NoneType. Check the sensor")

    async def rain_type(self, value) -> str:
        """Convert rain type."""
        type_array = ["none", "rain", "hail", "heavy"]
        try:
            precip_type = type_array[int(value)]
            return self._translations["precip_type"][precip_type]
        except IndexError as e:
            _LOGGER.debug("VALUE is: %s", value)
            return f"Unknown - {value}"

    async def direction(self, value) -> str:
        """Returns a directional Wind Direction string."""
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
        return self._translations["wind_dir"][direction_str]

    async def air_density(self, temperature, station_pressure):
        """Returns the Air Density."""
        if temperature is not None and station_pressure is not None:
            kelvin = temperature + 273.15
            pressure = station_pressure
            r_specific = 287.058
            decimals = 2

            air_dens = (pressure * 100) / (r_specific * kelvin)

            if self._unit_system == UNITS_IMPERIAL:
                air_dens = air_dens * 0.06243
                decimals = 4

            return round(air_dens, decimals)

        _LOGGER.error("FUNC: air_density ERROR: Temperature or Pressure value was reported as NoneType. Check the sensor")

    async def sea_level_pressure(self, station_press, elevation):
        """Returns Sea Level pressure.
            Converted from a JS formula made by Gary W Funk
        """
        if station_press is not None:
            elev = float(elevation)
            press = float(station_press)
            # Constants
            gravity = 9.80665
            gas_constant = 287.05
            atm_rate = 0.0065
            std_pressure = 1013.25
            std_temp = 288.15
            # Sub Calculation
            l = gravity / (gas_constant * atm_rate)
            c = gas_constant * atm_rate / gravity
            u = math.pow(1 + math.pow(std_pressure / press, c) * (atm_rate * elev / std_temp), l)
            sea_pressure = (press * u)

            return await self.pressure(sea_pressure)

        _LOGGER.error("FUNC: sea_level_pressure ERROR: Temperature or Pressure value was reported as NoneType. Check the sensor")

    async def dewpoint(self, temperature, humidity, no_conversion = False):
        """Returns Dewpoint."""
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
            return await self.temperature(dewpoint_c)

        _LOGGER.error("FUNC: dewpoint ERROR: Temperature and/or Humidity value was reported as NoneType. Check the sensor")

    async def rain_rate(self, value):
        """Returns rain rate per hour."""
        if not value:
            return 0
        return await self.rain(value * 60)

    async def feels_like(self, temperature, humidity, windspeed):
        """Calculates the feel like temperature."""
        if temperature is None or humidity is None or windspeed is None:
            return 0

        e_value = (
            humidity * 0.06105 * math.exp((17.27 * temperature) / (237.7 + temperature))
        )
        feelslike_c = temperature + 0.348 * e_value - 0.7 * windspeed - 4.25
        return await self.temperature(feelslike_c)

    async def average_bearing(self, bearing_arr) -> int:
        """Returns the average Wind Bearing from an array of bearings."""
        mean_angle = degrees(phase(sum(rect(1, radians(d)) for d in bearing_arr)/len(bearing_arr)))
        return int(abs(mean_angle))

    async def visibility(self, elevation, temp, humidity):
        """Returns the visibility.
           Input:
               Elevation in Meters
               Temperature in Celcius
               Humidity in percent
        """
        if temp is None or elevation is None or humidity is None:
            return None

        dewpoint_c = await self.dewpoint(temp, humidity, True)
        # Set minimum elevation for cases of stations below sea level
        if elevation > 2:
            elv_min = float(elevation)
        else:
            elv_min = float(2)

        # Max possible visibility to horizon (units km)
        mv = float(3.56972 * math.sqrt(elv_min))

        # Percent reduction based on quatity of water in air (no units)
        # 76 percent of visibility variation can be accounted for by humidity accourding to US-NOAA.
        pr_a = float((1.13 * abs(temp - dewpoint_c)-1.15)/10)
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

        if self._unit_system == UNITS_IMPERIAL:
            # Originally was in nautical miles; HA displays miles as imperial, therfore converted to miles
            return round(vis/1.609344, 1)
        return round(vis, 1)

    async def wetbulb(self, temp, humidity, pressure):
        """Returns the Wel Bulb Temperature.
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

        while (abs(edifference) > 0.005):
            ewguess = 6.112 * math.exp((17.67 * twguess) / (twguess + 243.5))
            eguess = ewguess - p * (t - twguess) * 0.00066 * (1 + (0.00115 * twguess))
            edifference = e2 - eguess
            if edifference == 0:
                break

            if edifference < 0:
                cursign = -1
                if (cursign != previoussign):
                    previoussign = cursign
                    incr = incr / 10
                else:
                    incr = incr
            else:
                cursign = 1
                if (cursign != previoussign):
                    previoussign = cursign
                    incr = incr / 10
                else:
                    incr = incr

            twguess = twguess + incr * previoussign

        return await self.temperature(twguess)

    async def delta_t(self, temp, humidity, pressure):
        """Returns Delta T temperature."""
        if temp is None or humidity is None or pressure is None:
            return None

        # Ensure both Wetbulb and Temperature is same unit system
        wb = await self.wetbulb(temp, humidity, pressure)
        temp_u = await self.temperature(temp)

        deltat = temp_u - wb

        return round(deltat, 1)

    async def battery_level(self, battery, is_tempest):
        """Returns the battery percentage.
           Input:
               Voltage in Volts DC (depends on the weather station type, see below)
               is_tempest in Boolean
           Tempest:
	     # data["battery_level"] = await cnv.battery_level(obs[16])
             Battery voltage range is 1.8 to 2.85 Vdc
               > 2.80 is capped at 100%
               < 1.8 is capped at 0%
           Air:
	     # data["battery_level"] = await cnv.battery_level(obs[6])
             4 AA batteries (2 in series, then parallel for 2 sets)
             Battery voltage range is 1.2(x2) => 2.4 to 1.8(x2) => 3.6 Vdc (lowered to 3.5 based on observation)
	       > 3.5 is capped at 100%
	       < 2.4 is capped at 0%
           Sky:
	     # data["battery_level"] = await cnv.battery_level(obs[8])
             8 AA batteries (2 in series, then parallel for 4 sets)
	     Battery voltage range is 1.2(x2) => 2.4 to 1.8(x2) => 3.6 Vdc (lowered to 3.5 based on observation)
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
                 pb = int((voltage - 1.8)*100)
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
                pb = int(((voltage - 2.4)/1.1)*100)

        return pb
    
    async def beaufort(self, wind_speed):
        """Returns the Beaufort Scale value based on Wind Speed."""

        if wind_speed is None:
            return 0, self._translations["beaufort"][str(0)]

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
        
        bft_text = self._translations["beaufort"][str(bft_value)]

        return bft_value, bft_text

    async def dewpoint_level(self, dewpoint_c):
        """Returns a text based comfort level, based on dewpoint F value."""
        if dewpoint_c is None:
            return "no-data"

        if self._unit_system == UNITS_IMPERIAL:
            dewpoint = dewpoint_c
        else:
            dewpoint = (dewpoint_c * 9 / 5) + 32

        if dewpoint >= 80:
            return self._translations["dewpoint"]["severely-high"]
        if dewpoint >= 75:
            return self._translations["dewpoint"]["miserable"]
        if dewpoint >= 70:
            return self._translations["dewpoint"]["oppressive"]
        if dewpoint >= 65:
            return self._translations["dewpoint"]["uncomfortable"]
        if dewpoint >= 60:
            return self._translations["dewpoint"]["ok-for-most"]
        if dewpoint >= 55:
            return self._translations["dewpoint"]["comfortable"]
        if dewpoint >= 50:
            return self._translations["dewpoint"]["very-comfortable"]
        if dewpoint >= 30:
            return self._translations["dewpoint"]["somewhat-dry"]
        if dewpoint >= 0.5:
            return self._translations["dewpoint"]["dry"]
        if dewpoint >= 0:
            return self._translations["dewpoint"]["very-dry"]
        
        return self._translations["dewpoint"]["undefined"]

    async def temperature_level(self, temperature_c):
        """Returns a text based comfort level, based on Air Temperature value."""
        if temperature_c is None:
            return "no-data"

        temperature = (temperature_c * 9 / 5) + 32

        if temperature >= 104:
            return self._translations["temperature"]["inferno"]
        if temperature >= 95:
            return self._translations["temperature"]["very-hot"]
        if temperature >= 86:
            return self._translations["temperature"]["hot"]
        if temperature >= 77:
            return self._translations["temperature"]["warm"]
        if temperature >= 68:
            return self._translations["temperature"]["nice"]
        if temperature >= 59:
            return self._translations["temperature"]["cool"]
        if temperature >= 41:
            return self._translations["temperature"]["chilly"]
        if temperature >= 32:
            return self._translations["temperature"]["cold"]
        if temperature >= 20:
            return self._translations["temperature"]["freezing"]
        if temperature <= 20:
            return self._translations["temperature"]["fridged"]
        
        return self._translations["temperature"]["undefined"]


    async def uv_level(self, uvi):
        """Returns a text based UV Description."""

        if uvi is None:
            return "no-data"

        if uvi >= 10.5:
            return self._translations["uv"]["extreme"]
        if uvi >= 7.5:
            return self._translations["uv"]["very-high"]
        if uvi >= 5.5:
            return self._translations["uv"]["high"]
        if uvi >= 2.5:
            return self._translations["uv"]["moderate"]
        if uvi > 0:
            return self._translations["uv"]["low"]
            
        return self._translations["uv"]["none"]

    async def humanize_time(self, value):
        """Humanize Time in Seconds."""
        if value is None:
            return "None"
        return str(datetime.timedelta(seconds=value))

    async def device_status(self, value):
        """Return device status as string."""
        if value is None:
            return
            
        binvalue = str(bin(value))
        binarr = binvalue[::-1]
        binarr = binarr[:len(DEVICE_STATUS)]
        return_value = []
        for x in range(len(DEVICE_STATUS)):
            if binarr[len(binarr) - 1 - x] == "1":
                return_value.append(DEVICE_STATUS[x])

        return return_value

class DataStorage:
    """Handles reading and writing of the external storage file."""

    logging.basicConfig(level=logging.DEBUG)

    async def read_config(self):
        """Reads the config file, to look for sensors."""
        try:
            filepath = f"{EXTERNAL_DIRECTORY}/config.yaml"
            with open(filepath, "r") as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
                sensors = data.get("sensors")

                return sensors

        except FileNotFoundError as e:
            return None
        except Exception as e:
            _LOGGER.debug("Could not read config.yaml file. Error message: %s", e)
            return None

    async def getLanguageFile(self, language: str):
        """Return the language file json array."""
        try:
            if language not in SUPPORTED_LANGUAGES:
                filename = "translations/en.json"
            else:
                filename = f"translations/{language.lower()}.json"

            with open(filename, "r") as json_file:
                return json.load(json_file)

        except FileNotFoundError as e:
            _LOGGER.debug("Could not read language file. Error message: %s", e)
            return None
        except Exception as e:
            _LOGGER.debug("Could not read language file. Error message: %s", e)
            return None


    def getVersion(self):
        """Returns the version number stored in the __version__.py file."""
        return DB_VERSION
