from enum import Enum


class EventType(str, Enum):
    RAIN = "RAIN"
    FROST = "FROST"
    HAIL = "HAIL"
    STRONG_WIND = "STRONG_WIND"


class IntensityUnit(str, Enum):
    MM_PER_HOUR = "MM_PER_HOUR"
    KM_PER_HOUR = "KM_PER_HOUR"
    MM = "MM"
    CELSIUS = "CELSIUS"


class ValidityWindowKind(str, Enum):
    RELATIVE = "RELATIVE"
    ABSOLUTE = "ABSOLUTE"


class RelativeWindowUnit(str, Enum):
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"
