"""Command-line entry point for the flight-deal tracker."""

from src.config import AppConfig, Secrets, load_config, load_secrets
from src.emailer import send_email
from src.flight_parser import parse_all_results
from src.flight_ranker import rank_flights
from src.flight_search import search_all_trip_lengths
from src.history import add_price_trends, add_reports_to_history, load_history
from src.models import SearchReport
from src.scheduler import mark_run_completed


def build_reports(config: AppConfig, secrets: Secrets) -> tuple[SearchReport, ...]:
    """Run every configured route search and return its ranked results."""

    reports: list[SearchReport] = []
    for search in config.searches:
        origins = ", ".join(search.origins)
        print(f"Searching '{search.name}': {origins} → {search.destination}")

        raw_results = search_all_trip_lengths(
            config=search,
            api_key=secrets.serpapi_key,
        )
        ranked_flights = rank_flights(parse_all_results(raw_results))
        result_count = len(ranked_flights)
        noun = "flight" if result_count == 1 else "flights"
        print(f"Found {result_count} {noun} for '{search.name}'.")

        reports.append(
            SearchReport(
                name=search.name,
                currency=search.currency,
                flights=tuple(ranked_flights),
                origins=search.origins,
                destination=search.destination,
            )
        )

    return tuple(reports)


def main() -> None:
    """Search configured routes, email one report, and save run metadata."""

    config = load_config()
    secrets = load_secrets()
    reports = add_price_trends(build_reports(config, secrets), load_history())

    send_email(
        sender=secrets.email_address,
        app_password=secrets.email_app_password,
        recipient=secrets.email_recipient,
        reports=reports,
        max_results_per_search=config.results_per_search,
    )

    add_reports_to_history(reports)
    mark_run_completed()
    print("Flight report sent successfully.")


if __name__ == "__main__":
    main()
