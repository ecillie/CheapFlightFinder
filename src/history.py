"""Persist normalized flight prices between scheduled workflow runs."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeAlias

from src.config import PROJECT_ROOT
from src.models import FlightDeal, SearchReport


HistoryEntry: TypeAlias = dict[str, Any]
DEFAULT_HISTORY_PATH = PROJECT_ROOT / "data" / "price_history.json"


def load_history(
    path: Path = DEFAULT_HISTORY_PATH,
) -> list[HistoryEntry]:
    """Read saved history, returning an empty list for a new empty file."""

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        if path.stat().st_size == 0:
            return []
        raise ValueError(f"Invalid JSON in history file: {path}") from error

    if not isinstance(data, list):
        raise ValueError(f"History file must contain a JSON list: {path}")
    return data


def save_history(
    history: list[HistoryEntry],
    path: Path = DEFAULT_HISTORY_PATH,
) -> None:
    """Atomically write price history as formatted JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)
        file.write("\n")
    temporary_path.replace(path)


def add_reports_to_history(
    reports: tuple[SearchReport, ...],
    path: Path = DEFAULT_HISTORY_PATH,
) -> None:
    """Append every flight in the current grouped report to history."""

    history = load_history(path)
    searched_at = datetime.now(timezone.utc).isoformat()

    for report in reports:
        history.extend(
            _history_entry(report.name, report.currency, flight, searched_at)
            for flight in report.flights
        )

    save_history(history=history, path=path)


def _history_entry(
    search_name: str,
    currency: str,
    flight: FlightDeal,
    searched_at: str,
) -> HistoryEntry:
    """Serialize a flight with the search name that produced it."""

    return {
        "searched_at": searched_at,
        "search_name": search_name,
        "origin": flight.origin,
        "destination": flight.destination,
        "departure_date": flight.departure_date,
        "return_date": flight.return_date,
        "price": flight.price,
        "currency": currency,
        "airline": flight.airline,
        "airline_code": flight.airline_code,
        "stops": flight.stops,
        "duration_minutes": flight.duration_minutes,
        "trip_length": flight.trip_length,
    }
