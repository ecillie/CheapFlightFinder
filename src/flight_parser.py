"""Normalize SerpApi response objects into application flight models."""

from collections.abc import Iterable
from typing import Any

from src.models import FlightDeal, JsonObject, SearchResult


TRIP_LENGTH_LABELS = {
    "weekend": "Weekend",
    "one_week": "1 week",
    "two_weeks": "2 weeks",
}


def parse_flights(
    raw_data: JsonObject,
    trip_length: str,
) -> list[FlightDeal]:
    """Parse all valid flights from a single SerpApi response."""

    departure_date = raw_data.get("start_date")
    return_date = raw_data.get("end_date")
    if not isinstance(departure_date, str) or not isinstance(return_date, str):
        return []

    raw_flights = raw_data.get("flights", [])
    if not isinstance(raw_flights, list):
        return []

    flights: list[FlightDeal] = []
    for raw_flight in raw_flights:
        if not isinstance(raw_flight, dict):
            continue

        origin = _airport_id(raw_flight.get("departure_airport"))
        destination = _airport_id(raw_flight.get("arrival_airport"))
        price = raw_flight.get("price")
        if not origin or not destination or price is None:
            continue

        try:
            numeric_price = float(price)
            stops = int(raw_flight.get("number_of_stops", 0))
            duration = int(raw_flight.get("duration", 0))
        except (TypeError, ValueError):
            continue

        if numeric_price < 0 or stops < 0 or duration < 0:
            continue

        flights.append(
            FlightDeal(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                price=numeric_price,
                airline=_text_or_default(raw_flight.get("airline"), "Unknown"),
                airline_code=_text_or_default(raw_flight.get("airline_code"), ""),
                stops=stops,
                duration_minutes=duration,
                trip_length=TRIP_LENGTH_LABELS[trip_length],
            )
        )

    return flights


def parse_all_results(
    search_results: Iterable[SearchResult],
) -> list[FlightDeal]:
    """Combine parsed flights from several configured trip lengths."""

    all_flights: list[FlightDeal] = []
    for trip_length, raw_data in search_results:
        all_flights.extend(
            parse_flights(
                raw_data=raw_data,
                trip_length=trip_length,
            )
        )

    return all_flights


def _airport_id(value: Any) -> str | None:
    """Return an airport ID from a nested SerpApi airport object."""

    if not isinstance(value, dict):
        return None
    airport_id = value.get("id")
    if not isinstance(airport_id, str) or not airport_id.strip():
        return None
    return airport_id.strip()


def _text_or_default(value: Any, default: str) -> str:
    """Return a non-empty string value or the supplied default."""

    if not isinstance(value, str) or not value.strip():
        return default
    return value.strip()
