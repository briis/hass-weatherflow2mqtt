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

from sqlite import SQLFunctions
from const import (
    DEVICE_STATUS,
    EXTERNAL_DIRECTORY,
    PRESSURE_STORAGE_FILE,
    PRESSURE_TREND_TIMER,
    STORAGE_FILE,
    STORAGE_FIELDS,
    STRIKE_STORAGE_FILE,
    UNITS_IMPERIAL,
)

_LOGGER = logging.getLogger(__name__)


class ConversionFunctions:
    """Class to help with converting from different units."""

    def __init__(self, unit_system):
        self._unit_system = unit_system

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
        type_array = ["None", "Rain", "Hail", "Heavy Rain"]
        try:
            return type_array[int(value)]
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
        direction = direction_array[int((value + 11.25) / 22.5)]
        return direction

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
        """Returns Sea Level pressure."""
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

    async def dewpoint(self, temperature, humidity):
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
            return await self.temperature(dewpoint_c)

        _LOGGER.error("FUNC: dewpoint ERROR: Temperature and/or Humidity value was reported as NoneType. Check the sensor")

    async def rain_rate(self, value):
        """Returns rain rate per hour."""
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
        binarr = binvalue[2:]
        return_value = []
        for x in range(len(binarr)):
            if binarr[x:x+1] == "1":
                return_value.append(DEVICE_STATUS[len(binarr)-x])

        return return_value

class DataStorage:
    """Handles reading and writing of the external storage file."""

    logging.basicConfig(level=logging.DEBUG)

    def _initialize_storage(self):

        _LOGGER.info("Creating new Storage file...")
        data = OrderedDict()
        for item in STORAGE_FIELDS:
            data[item[0]] = item[1]

        try:
            with open(STORAGE_FILE, "w") as jsonFile:
                json.dump(data, jsonFile)
        except Exception as e:
            _LOGGER.error("Could not save Storage File. Error message: %s", e)

        return data

    async def read_storage(self):
        """Read the storage file, and return values."""
        try:
            with open(STORAGE_FILE, "r") as jsonFile:
                tmp_data = json.load(jsonFile)
                data = await self._data_integrity(tmp_data)
                return data
        except FileNotFoundError as e:
            data = self._initialize_storage()
            return data
        except Exception as e:
            _LOGGER.debug("Could not Read storage file. Error message: %s", e)

    async def _data_integrity(self, data):
        """Checks the Integrity of the Data File."""

        for item in STORAGE_FIELDS:
            if item[0] not in data:
                data[item[0]] = item[1]

        await self.write_storage(data)
        return data

    async def write_storage(self, data: OrderedDict):
        """Saves the last values in the Stotage file."""

        try:
            with open(STORAGE_FILE, "w") as jsonFile:
                json.dump(data, jsonFile)
        except Exception as e:
            _LOGGER.error("Could not save Storage File. Error message: %s", e)

    async def read_strike_storage(self):
        """Read the strike storage file, and return number of strikes in last three hours."""
        try:
            with open(STRIKE_STORAGE_FILE, "r") as file:
                lines = file.readlines()
            cnt = 0
            for item in lines:
                if item != "\n":
                    if time.time() - float(item) < 10800:
                        cnt += 1
            return cnt
        except FileNotFoundError as e:
            return 0
        except Exception as e:
            _LOGGER.debug("Could not read strike storage file. Error message: %s", e)
            return 0

    async def write_strike_storage(self):
        """Saves an entry if a strike event occurs."""

        try:
            file = open(STRIKE_STORAGE_FILE, "a")
            file.write(f"{time.time()}\n")
            file.close()

        except Exception as e:
            _LOGGER.error("Could not save Lightning Storage File. Error message: %s", e)

    async def housekeeping_strike(self):
        """Performs housekeeping tasks on the strike data file."""

        try:
            with open(STRIKE_STORAGE_FILE, "r") as file:
                lines = file.readlines()
            newlines = ""
            for item in lines:
                if item != "\n":
                    if time.time() - float(item) < 10800:
                        newlines += item
            file = open(STRIKE_STORAGE_FILE, "w")
            file.write(f"{newlines}\n")
            file.close()

        except FileNotFoundError as e:
            return 0
        except Exception as e:
            _LOGGER.debug(
                "Could not perform housekeeping on strike storage file. Error message: %s",
                e,
            )

    async def read_pressure_storage(self):
        """Read the pressure storage file, and return pressure value 3 hours ago."""
        try:
            with open(PRESSURE_STORAGE_FILE, "r") as file:
                lines = file.readlines()
            val_available = False
            for item in lines:
                if item != "\n":
                    if time.time() - PRESSURE_TREND_TIMER < float(item[0]):
                        pressure = item[1]
                        break
            return pressure
        except FileNotFoundError as e:
            return 0
        except Exception as e:
            _LOGGER.debug("Could not read strike storage file. Error message: %s", e)
            return 0

    async def write_pressure_storage(self, value):
        """Saves a pressure entry."""

        try:
            file = open(PRESSURE_STORAGE_FILE, "a")
            file.write(f"[{time.time()}, {value}]\n")
            file.close()

        except Exception as e:
            _LOGGER.error("Could not save Pressure Storage File. Error message: %s", e)

    async def housekeeping_pressure_storage(self):
        """Performs housekeeping tasks on the pressure data file."""

        try:
            with open(PRESSURE_STORAGE_FILE, "r") as file:
                lines = file.readlines()
            newlines = ""
            for item in lines:
                if item != "\n":
                    if time.time() - float(item) < PRESSURE_TREND_TIMER:
                        newlines += item
            file = open(PRESSURE_STORAGE_FILE, "w")
            file.write(f"{newlines}\n")
            file.close()

        except FileNotFoundError as e:
            return 0
        except Exception as e:
            _LOGGER.debug(
                "Could not perform housekeeping on pressure storage file. Error message: %s",
                e,
            )

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

    def getVersion(self):
        """Returns the version number stored in the VERSION file."""
        try:
            filepath = f"{EXTERNAL_DIRECTORY}/VERSION"
            with open(filepath, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line != "\n":
                        return line.replace("\n", "")


        except FileNotFoundError as e:
            return None
        except Exception as e:
            _LOGGER.debug("Could not read config.yaml file. Error message: %s", e)
            return None

