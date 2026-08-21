"""Persist normalized flight prices between scheduled workflow runs."""

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeAlias

from src.config import PROJECT_ROOT
from src.models import FlightDeal, PriceTrend, SearchReport


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


def add_price_trends(
    reports: tuple[SearchReport, ...],
    history: list[HistoryEntry],
) -> tuple[SearchReport, ...]:
    """Return reports enriched with best-fare trends from saved history."""

    return tuple(
        replace(report, price_trends=_build_report_trends(report, history))
        for report in reports
    )


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


def _build_report_trends(
    report: SearchReport,
    history: list[HistoryEntry],
) -> tuple[PriceTrend, ...]:
    """Calculate one best-fare trend for every current trip length."""

    relevant_history = _history_for_report(report, history)
    trip_lengths = tuple(
        dict.fromkeys(flight.trip_length for flight in report.flights)
    )
    trends: list[PriceTrend] = []

    for trip_length in trip_lengths:
        current_lowest = min(
            flight.price
            for flight in report.flights
            if flight.trip_length == trip_length
        )
        prior_run_lows = _best_fare_by_run(relevant_history, trip_length)
        previous_lowest = prior_run_lows[-1][1] if prior_run_lows else None
        tracked_lows = [price for _, price in prior_run_lows] + [current_lowest]

        trends.append(
            PriceTrend(
                trip_length=trip_length,
                current_lowest=current_lowest,
                previous_lowest=previous_lowest,
                tracked_lowest=min(tracked_lows),
                tracked_highest=max(tracked_lows),
                tracked_runs=len(tracked_lows),
            )
        )

    return tuple(trends)


def _history_for_report(
    report: SearchReport,
    history: list[HistoryEntry],
) -> list[HistoryEntry]:
    """Find comparable entries, with a route fallback for renamed profiles."""

    route_matches = [
        entry
        for entry in history
        if entry.get("currency") == report.currency
        and entry.get("destination") == report.destination
        and entry.get("origin") in report.origins
    ]
    named_matches = [
        entry for entry in route_matches if entry.get("search_name") == report.name
    ]
    return named_matches or route_matches


def _best_fare_by_run(
    history: list[HistoryEntry],
    trip_length: str,
) -> list[tuple[str, float]]:
    """Return chronological best fares for a trip length, one per run."""

    best_by_timestamp: dict[str, float] = {}
    for entry in history:
        if entry.get("trip_length") != trip_length:
            continue

        timestamp = entry.get("searched_at")
        price = entry.get("price")
        if not isinstance(timestamp, str) or not isinstance(price, (int, float)):
            continue

        numeric_price = float(price)
        previous = best_by_timestamp.get(timestamp)
        if previous is None or numeric_price < previous:
            best_by_timestamp[timestamp] = numeric_price

    return sorted(best_by_timestamp.items())


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
