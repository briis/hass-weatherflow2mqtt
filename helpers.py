"""Several Helper Functions."""

import datetime
import time
import json
import math
from typing import OrderedDict
import logging

from const import (
    UNITS_IMPERIAL,
    STORAGE_FILE,
    STORAGE_FIELDS,
    STRIKE_STORAGE_FILE,
)

_LOGGER = logging.getLogger(__name__)

class ConversionFunctions:
    """Class to help with converting from different units."""

    def __init__(self, unit_system):
        self._unit_system = unit_system
    
    async def temperature(self, value) -> float:
        """Convert Temperature Value."""
        if self._unit_system == UNITS_IMPERIAL:
            return round((value * 9 / 5) + 32, 1)
        return round(value, 1)
    
    async def pressure(self, value) -> float:
        """Convert Pressure Value."""
        if self._unit_system == UNITS_IMPERIAL:
            return round(value * 0.02953, 3)
        return round(value, 2)

    async def speed(self, value) -> float:
        """Convert Wind Speed."""
        if self._unit_system == UNITS_IMPERIAL:
            return round(value * 2.2369362920544, 2)
        return round(value, 1)

    async def distance(self, value) -> float:
        """Convert distance."""
        if self._unit_system == UNITS_IMPERIAL:
            return round(value / 1.609344, 2)
        return value

    async def rain(self, value) -> float:
        """Convert rain."""
        if self._unit_system == UNITS_IMPERIAL:
            return round(value * 0.0393700787, 2)
        return round(value, 2)

    async def rain_type(self, value) -> str:
        """Convert rain type."""
        type_array = ["None", "Rain", "Hail"]
        try:
            return type_array[int(value)]
        except IndexError as e:
            _LOGGER.debug("VALUE is: %s", value)
            return "Unknown"

    async def direction(self, value) -> str:
        """Returns a directional Wind Direction string."""
        if value is None:
            return "N"
        direction_array = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW","N"]
        direction = direction_array[int((value + 11.25) / 22.5)]
        return direction

    async def air_density(self,temperature, station_pressure):
        """Returns the Air Density."""
        kelvin = temperature + 273.15
        pressure = station_pressure
        r_specific = 287.058

        if self._unit_system == UNITS_IMPERIAL:
            pressure = station_pressure *  0.0145037738
            r_specific = 53.35

        return round((pressure * 100) / (r_specific * kelvin), 4)

    async def dewpoint(self, temperature, humidity):
        """Returns Dewpoint."""
        dewpoint_c = round(243.04*(math.log(humidity/100)+((17.625*temperature)/(243.04+temperature)))/(17.625-math.log(humidity/100)-((17.625*temperature)/(243.04+temperature))),1)
        if self._unit_system == UNITS_IMPERIAL:
            return await self.temperature(dewpoint_c)
        return dewpoint_c

    async def rain_rate(self, value):
        """Returns rain rate per hour."""
        return await self.rain(value * 60)

    async def feels_like(self, temperature, humidity, windspeed):
        """Calculates the feel like temperature."""
        if temperature is None or humidity is None or windspeed is None:
            return 0

        e_value = humidity * 0.06105 * math.exp((17.27 * temperature) / (237.7 + temperature))
        feelslike_c = temperature + 0.348 * e_value - 0.7 * windspeed - 4.25
        if self._unit_system == UNITS_IMPERIAL:
            return await self.temperature(feelslike_c)
        return round(feelslike_c, 1)

    async def humanize_time(self, value):
        """Humanize Time in Seconds."""
        if value is None:
            return "None"
        return str(datetime.timedelta(seconds=value))

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
                if time.time() - float(item) < 10800:
                    cnt += 1
            return cnt
        except FileNotFoundError as e:
            return 0
        except Exception as e:
            _LOGGER.debug("Could not read strike storage file. Error message: %s", e)

    async def write_strike_storage(self):
        """Saves an entry if a strike event occurs."""

        try:
            file = open(STRIKE_STORAGE_FILE, "a")
            # data = OrderedDict()
            # data["strike_time"] = time.time()
            file.write(f"{time.time()}\n")
            file.close()

        except Exception as e:
            _LOGGER.error("Could not save Storage File. Error message: %s", e)
