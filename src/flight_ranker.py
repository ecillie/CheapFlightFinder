from src.models import FlightDeal


STOP_PENALTY = 100
LONG_FLIGHT_THRESHOLD_MINUTES = 20 * 60
EXTRA_DURATION_PENALTY_PER_MINUTE = 0.20


def calculate_score(flight: FlightDeal) -> float:
    """
    Lower score = better flight.

    We favor:
    - cheaper flights
    - fewer stops
    - shorter durations
    """

    score = flight.price

    score += flight.stops * STOP_PENALTY

    extra_minutes = max(
        0,
        flight.duration_minutes
        - LONG_FLIGHT_THRESHOLD_MINUTES,
    )

    score += (
        extra_minutes
        * EXTRA_DURATION_PENALTY_PER_MINUTE
    )

    return round(score, 2)


def rank_flights(
    flights: list[FlightDeal],
) -> list[FlightDeal]:

    return sorted(
        flights,
        key=calculate_score,
    )