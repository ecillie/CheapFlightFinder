import requests

from src.config import AppConfig


SERPAPI_URL = "https://serpapi.com/search.json"


TRAVEL_CLASS_MAP = {
    "economy": 1,
    "premium_economy": 2,
    "business": 3,
    "first": 4,
}


def max_stops_to_api_value(max_stops: int) -> int:
    """
    SerpApi Travel Explore stop values:

    0 = any number of stops
    1 = nonstop only
    2 = 1 stop or fewer
    3 = 2 stops or fewer
    """

    if max_stops == 0:
        return 1

    if max_stops == 1:
        return 2

    if max_stops == 2:
        return 3

    return 0


def search_flights(
    config: AppConfig,
    api_key: str,
    trip_duration: int,
) -> dict:

    departure_airports = ",".join(config.origins)

    params = {
        "engine": "google_travel_explore",
        "departure_id": departure_airports,
        "arrival_id": config.destination,
        "currency": config.currency,
        "gl": "us",
        "hl": "en",

        # Flexible dates across next 6 months
        "month": 0,

        # 2 = one week
        # 3 = two weeks
        "travel_duration": trip_duration,

        "travel_class": TRAVEL_CLASS_MAP.get(
            config.travel_class.lower(),
            1,
        ),

        "adults": 1,

        "stops": max_stops_to_api_value(
            config.max_stops
        ),

        "max_price": config.max_price,

        "api_key": api_key,
    }

    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(
            f"SerpApi returned an error: {data['error']}"
        )

    return data


def search_all_trip_durations(
    config: AppConfig,
    api_key: str,
) -> list[tuple[int, dict]]:

    results = []

    for trip_duration in config.trip_durations:
        data = search_flights(
            config=config,
            api_key=api_key,
            trip_duration=trip_duration,
        )

        results.append(
            (trip_duration, data)
        )

    return results