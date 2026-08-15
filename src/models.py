"""Shared domain models for normalized flights and email reports."""

from dataclasses import dataclass
from typing import Any, TypeAlias


JsonObject: TypeAlias = dict[str, Any]
SearchResult: TypeAlias = tuple[str, JsonObject]


@dataclass(frozen=True, slots=True)
class FlightDeal:
    """A normalized flight returned by SerpApi.

    Dates use ``YYYY-MM-DD`` strings, prices use the currency configured for
    the search, and duration is stored in minutes.
    """

    origin: str
    destination: str
    departure_date: str
    return_date: str
    price: float
    airline: str
    airline_code: str
    stops: int
    duration_minutes: int
    trip_length: str

    @property
    def duration_hours(self) -> float:
        """Return the flight duration in hours, rounded to one decimal."""

        return round(self.duration_minutes / 60, 1)


@dataclass(frozen=True, slots=True)
class SearchReport:
    """Ranked results for one named search configured by the user."""

    name: str
    currency: str
    flights: tuple[FlightDeal, ...]
