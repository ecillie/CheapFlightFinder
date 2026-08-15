from src.config import load_config, load_secrets
from src.flight_search import search_all_trip_durations
from src.flight_parser import parse_all_results
from src.flight_ranker import rank_flights
from src.history import add_search_to_history
from src.emailer import send_email


def main():
    # Load non-sensitive config and sensitive environment variables
    config = load_config()
    secrets = load_secrets()

    print("Starting Cape Town flight search...")

    # Search SerpApi for each configured trip duration
    raw_results = search_all_trip_durations(
        config=config,
        api_key=secrets.serpapi_key,
    )

    # Convert raw API responses into FlightDeal objects
    flights = parse_all_results(raw_results)

    print(f"Found {len(flights)} flights.")

    # Rank flights by price, stops, and duration
    ranked_flights = rank_flights(flights)

    # Save today's results to history
    add_search_to_history(ranked_flights)

    # Send the best results by email
    send_email(
        sender=secrets.email_address,
        app_password=secrets.email_app_password,
        recipient=secrets.email_recipient,
        flights=ranked_flights,
        max_results=config.results_per_email,
    )

    print("Flight report sent successfully.")


if __name__ == "__main__":
    main()