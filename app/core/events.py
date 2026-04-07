from dataclasses import dataclass
from operator import ge, le
from typing import Callable

from app.models.enums import EventType, IntensityUnit


@dataclass(frozen=True)
class EventDefinition:
    intensity_unit: IntensityUnit
    intensity_comparator: Callable[[float, float], bool]


EVENT_DEFINITIONS: dict[EventType, EventDefinition] = {
    EventType.RAIN: EventDefinition(
        intensity_unit=IntensityUnit.MM_PER_HOUR,
        intensity_comparator=ge,
    ),
    EventType.STRONG_WIND: EventDefinition(
        intensity_unit=IntensityUnit.KM_PER_HOUR,
        intensity_comparator=ge,
    ),
    EventType.HAIL: EventDefinition(
        intensity_unit=IntensityUnit.MM,
        intensity_comparator=ge,
    ),
    EventType.FROST: EventDefinition(
        intensity_unit=IntensityUnit.CELSIUS,
        intensity_comparator=le,
    ),
}


def get_event_definition(event_type: EventType) -> EventDefinition:
    return EVENT_DEFINITIONS[event_type]
