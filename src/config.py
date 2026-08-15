import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Secrets:
    serpapi_key: str
    email_address: str
    email_app_password: str
    email_recipient: str


@dataclass
class AppConfig:
    origins: list[str]
    destination: str
    currency: str
    travel_class: str
    max_stops: int
    max_price: int
    results_per_email: int
    trip_durations: list[int]


def load_secrets() -> Secrets:
    required = {
        "SERPAPI_KEY": os.getenv("SERPAPI_KEY"),
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_APP_PASSWORD": os.getenv("EMAIL_APP_PASSWORD"),
        "EMAIL_RECIPIENT": os.getenv("EMAIL_RECIPIENT"),
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return Secrets(
        serpapi_key=required["SERPAPI_KEY"],
        email_address=required["EMAIL_ADDRESS"],
        email_app_password=required["EMAIL_APP_PASSWORD"],
        email_recipient=required["EMAIL_RECIPIENT"],
    )


def load_config(path: str = "config.json") -> AppConfig:
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Could not find configuration file: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return AppConfig(
        origins=data["origins"],
        destination=data["destination"],
        currency=data.get("currency", "USD"),
        travel_class=data.get("travel_class", "economy"),
        max_stops=data.get("max_stops", 2),
        max_price=data.get("max_price", 1500),
        results_per_email=data.get("results_per_email", 10),

        # SerpApi Travel Explore:
        # 2 = 1 week
        # 3 = 2 weeks
        trip_durations=data.get("trip_durations", [2, 3]),
    )