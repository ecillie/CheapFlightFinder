"""Score and rank normalized flights by practical deal quality."""

from collections.abc import Iterable

from src.models import FlightDeal


STOP_PENALTY = 100
LONG_FLIGHT_THRESHOLD_MINUTES = 20 * 60
EXTRA_DURATION_PENALTY_PER_MINUTE = 0.20


def calculate_score(flight: FlightDeal) -> float:
    """Return a deal score where lower values indicate better flights.

    The base score is the price. Each stop adds 100 points, and every minute
    beyond 20 hours adds 0.2 points.
    """

    extra_minutes = max(
        0, flight.duration_minutes - LONG_FLIGHT_THRESHOLD_MINUTES
    )
    score = (
        flight.price
        + (flight.stops * STOP_PENALTY)
        + (extra_minutes * EXTRA_DURATION_PENALTY_PER_MINUTE)
    )

    return round(score, 2)


def rank_flights(
    flights: Iterable[FlightDeal],
) -> list[FlightDeal]:
    """Return flights ordered from lowest to highest deal score."""

    return sorted(flights, key=calculate_score)
