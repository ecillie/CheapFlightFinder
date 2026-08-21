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
class PriceTrend:
    """Best-fare movement for one trip length across saved tracker runs."""

    trip_length: str
    current_lowest: float
    previous_lowest: float | None
    tracked_lowest: float
    tracked_highest: float
    tracked_runs: int

    @property
    def change_amount(self) -> float | None:
        """Return the current best fare minus the prior run's best fare."""

        if self.previous_lowest is None:
            return None
        return self.current_lowest - self.previous_lowest

    @property
    def change_percent(self) -> float | None:
        """Return the percentage movement from the prior run's best fare."""

        if self.previous_lowest is None or self.previous_lowest == 0:
            return None
        change = self.change_amount
        if change is None:
            return None
        return change / self.previous_lowest * 100


@dataclass(frozen=True, slots=True)
class SearchReport:
    """Ranked results for one named search configured by the user."""

    name: str
    currency: str
    flights: tuple[FlightDeal, ...]
    origins: tuple[str, ...] = ()
    destination: str = ""
    price_trends: tuple[PriceTrend, ...] = ()
