"""Several Helper Functions."""

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
        return value

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
