"""Build and execute Google Travel Explore searches through SerpApi."""

from typing import Any

import requests

from src.config import SearchConfig
from src.models import JsonObject, SearchResult


SERPAPI_URL = "https://serpapi.com/search.json"
REQUEST_TIMEOUT_SECONDS = 60

TRAVEL_CLASS_MAP = {
    "economy": 1,
    "premium_economy": 2,
    "business": 3,
    "first": 4,
}

TRIP_LENGTH_MAP = {
    "weekend": 1,
    "one_week": 2,
    "two_weeks": 3,
}

MAX_STOPS_MAP = {
    0: 1,
    1: 2,
    2: 3,
}


def max_stops_to_api_value(max_stops: int) -> int:
    """Translate a human-friendly maximum into SerpApi's stop filter.

    SerpApi uses ``1`` for nonstop, ``2`` for one stop or fewer, and ``3``
    for two stops or fewer.
    """

    return MAX_STOPS_MAP[max_stops]


def build_search_params(
    config: SearchConfig,
    api_key: str,
    trip_length: str,
) -> dict[str, str | int]:
    """Build query parameters for one configured trip length."""

    try:
        travel_duration = TRIP_LENGTH_MAP[trip_length]
    except KeyError as error:
        raise ValueError(f"Unsupported trip length: {trip_length}") from error

    return {
        "engine": "google_travel_explore",
        "departure_id": ",".join(config.origins),
        "arrival_id": config.destination,
        "currency": config.currency,
        "gl": "us",
        "hl": "en",
        "month": 0,
        "travel_duration": travel_duration,
        "travel_class": TRAVEL_CLASS_MAP[config.travel_class],
        "adults": 1,
        "stops": max_stops_to_api_value(config.max_stops),
        "max_price": config.max_price,
        "api_key": api_key,
    }


def search_flights(
    config: SearchConfig,
    api_key: str,
    trip_length: str,
) -> JsonObject:
    """Request flexible-date flights for one search and trip length."""

    response = requests.get(
        SERPAPI_URL,
        params=build_search_params(config, api_key, trip_length),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data: Any = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("SerpApi returned an unexpected non-object response")

    if "error" in data:
        raise RuntimeError(f"SerpApi returned an error: {data['error']}")

    return data


def search_all_trip_lengths(
    config: SearchConfig,
    api_key: str,
) -> list[SearchResult]:
    """Run one request for every trip length in a search profile."""

    return [
        (
            trip_length,
            search_flights(
                config=config,
                api_key=api_key,
                trip_length=trip_length,
            ),
        )
        for trip_length in config.trip_lengths
    ]
