"""Load and validate public configuration and private credentials."""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"

SUPPORTED_TRAVEL_CLASSES = {
    "economy",
    "premium_economy",
    "business",
    "first",
}
SUPPORTED_TRIP_LENGTHS = {"weekend", "one_week", "two_weeks"}


class ConfigError(ValueError):
    """Raised when ``config.json`` contains an invalid value."""


@dataclass(frozen=True, slots=True)
class Secrets:
    """Credentials loaded from environment variables or a local ``.env``."""

    serpapi_key: str
    email_address: str
    email_app_password: str
    email_recipient: str


@dataclass(frozen=True, slots=True)
class ScheduleConfig:
    """How often a scheduled workflow may send a report."""

    every_hours: int


@dataclass(frozen=True, slots=True)
class SearchConfig:
    """Settings for one origin-to-destination flight search."""

    name: str
    origins: tuple[str, ...]
    destination: str
    currency: str
    travel_class: str
    max_stops: int
    max_price: int
    trip_lengths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level application settings loaded from ``config.json``."""

    schedule: ScheduleConfig
    results_per_search: int
    searches: tuple[SearchConfig, ...]


def load_secrets() -> Secrets:
    """Load required credentials and report all missing names at once."""

    # Import lazily so the scheduler can read config before dependencies are
    # installed on a GitHub-hosted runner.
    from dotenv import load_dotenv

    load_dotenv()

    serpapi_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAI_KEY")
    values = {
        "SERPAPI_KEY (or SERPAI_KEY)": serpapi_key,
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_APP_PASSWORD": os.getenv("EMAIL_APP_PASSWORD"),
        "EMAIL_RECIPIENT": os.getenv("EMAIL_RECIPIENT"),
    }
    missing = [name for name, value in values.items() if not value]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return Secrets(
        serpapi_key=serpapi_key or "",
        email_address=values["EMAIL_ADDRESS"] or "",
        email_app_password=values["EMAIL_APP_PASSWORD"] or "",
        email_recipient=values["EMAIL_RECIPIENT"] or "",
    )


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Read and validate a tracker configuration file.

    Args:
        path: Location of the JSON configuration file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ConfigError: If the JSON structure or any setting is invalid.
    """

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Could not find configuration file: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as error:
        raise ConfigError(f"Invalid JSON in {config_path}: {error}") from error

    data = _require_mapping(raw_data, "config")
    schedule_data = _require_mapping(data.get("schedule", {}), "schedule")

    raw_searches = data.get("searches")
    if not isinstance(raw_searches, list) or not raw_searches:
        raise ConfigError("'searches' must be a non-empty list")

    searches = tuple(
        _parse_search(_require_mapping(item, f"searches[{index}]"), index)
        for index, item in enumerate(raw_searches)
    )
    names = [search.name.casefold() for search in searches]
    if len(names) != len(set(names)):
        raise ConfigError("Each search must have a unique 'name'")

    return AppConfig(
        schedule=ScheduleConfig(
            every_hours=_read_integer(
                schedule_data,
                "every_hours",
                default=24,
                minimum=1,
            )
        ),
        results_per_search=_read_integer(
            data,
            "results_per_search",
            default=10,
            minimum=1,
        ),
        searches=searches,
    )


def _parse_search(data: Mapping[str, Any], index: int) -> SearchConfig:
    """Validate one item from the top-level ``searches`` list."""

    label = f"searches[{index}]"
    origins = _read_string_list(data, "origins", label)
    trip_lengths = _read_string_list(data, "trip_lengths", label)

    unsupported_lengths = set(trip_lengths) - SUPPORTED_TRIP_LENGTHS
    if unsupported_lengths:
        valid = ", ".join(sorted(SUPPORTED_TRIP_LENGTHS))
        invalid = ", ".join(sorted(unsupported_lengths))
        raise ConfigError(
            f"{label}.trip_lengths contains {invalid}; valid values: {valid}"
        )

    travel_class = _read_string(data, "travel_class", default="economy").lower()
    if travel_class not in SUPPORTED_TRAVEL_CLASSES:
        valid = ", ".join(sorted(SUPPORTED_TRAVEL_CLASSES))
        raise ConfigError(f"{label}.travel_class must be one of: {valid}")

    max_stops = _read_integer(data, "max_stops", default=2, minimum=0)
    if max_stops > 2:
        raise ConfigError(f"{label}.max_stops must be 0, 1, or 2")

    return SearchConfig(
        name=_read_string(data, "name"),
        origins=origins,
        destination=_read_string(data, "destination"),
        currency=_read_string(data, "currency", default="USD").upper(),
        travel_class=travel_class,
        max_stops=max_stops,
        max_price=_read_integer(data, "max_price", default=1500, minimum=1),
        trip_lengths=trip_lengths,
    )


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    """Return a JSON object or raise a contextual configuration error."""

    if not isinstance(value, dict):
        raise ConfigError(f"'{label}' must be a JSON object")
    return value


def _read_string(
    data: Mapping[str, Any],
    key: str,
    default: str | None = None,
) -> str:
    """Read, trim, and validate a string setting."""

    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{key}' must be a non-empty string")
    return value.strip()


def _read_string_list(
    data: Mapping[str, Any],
    key: str,
    label: str,
) -> tuple[str, ...]:
    """Read a non-empty JSON list of non-empty strings."""

    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{label}.{key} must be a non-empty list")

    cleaned = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"Every value in {label}.{key} must be a string")
        cleaned.append(item.strip())

    return tuple(cleaned)


def _read_integer(
    data: Mapping[str, Any],
    key: str,
    *,
    default: int,
    minimum: int,
) -> int:
    """Read an integer setting and enforce its lower bound."""

    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigError(f"'{key}' must be an integer of at least {minimum}")
    return value
