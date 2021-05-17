"""Several Helper Functions."""
import math
from const import UNITS_IMPERIAL

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
        return value

    async def rain_type(self, value) -> str:
        """Convert rain type."""
        type_array = ["None", "Rain", "Hail"]
        return type_array[int(value)]

    async def direction(self, value) -> str:
        """Returns a directional Wind Direction string."""
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

    async def humanize_time(self, seconds):
        """Humanize Time in Seconds."""
        seconds_in_day = 60 * 60 * 24
        seconds_in_hour = 60 * 60
        seconds_in_minute = 60
        days = seconds // seconds_in_day
        hours = (seconds - (days * seconds_in_day)) // seconds_in_hour
        minutes = (seconds - (days * seconds_in_day) - (hours * seconds_in_hour)) // seconds_in_minute
        time_array = {
            "days": days,
            "hours": hours,
            "minutes": minutes
        }
        return time_array
