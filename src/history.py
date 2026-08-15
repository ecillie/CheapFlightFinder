import json
from datetime import datetime, timezone
from pathlib import Path

from src.models import FlightDeal


DEFAULT_HISTORY_PATH = Path(
    "data/price_history.json"
)


def load_history(
    path: Path = DEFAULT_HISTORY_PATH,
) -> list[dict]:

    if not path.exists():
        return []

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError:
        return []


def save_history(
    history: list[dict],
    path: Path = DEFAULT_HISTORY_PATH,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            history,
            file,
            indent=2,
        )


def add_search_to_history(
    flights: list[FlightDeal],
    path: Path = DEFAULT_HISTORY_PATH,
) -> None:

    history = load_history(path)

    searched_at = datetime.now(
        timezone.utc
    ).isoformat()

    for flight in flights:

        history.append(
            {
                "searched_at": searched_at,
                "origin": flight.origin,
                "destination": flight.destination,
                "departure_date": flight.departure_date,
                "return_date": flight.return_date,
                "price": flight.price,
                "airline": flight.airline,
                "stops": flight.stops,
                "duration_minutes": flight.duration_minutes,
                "trip_length": flight.trip_length,
            }
        )

    save_history(
        history=history,
        path=path,
    )