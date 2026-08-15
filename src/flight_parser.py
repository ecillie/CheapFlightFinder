from src.models import FlightDeal


TRIP_DURATION_NAMES = {
    1: "weekend",
    2: "1 week",
    3: "2 weeks",
}


def parse_flights(
    raw_data: dict,
    trip_duration: int,
) -> list[FlightDeal]:

    departure_date = raw_data.get("start_date")
    return_date = raw_data.get("end_date")

    raw_flights = raw_data.get("flights", [])

    flights = []

    for flight in raw_flights:

        departure_airport = flight.get(
            "departure_airport",
            {},
        )

        arrival_airport = flight.get(
            "arrival_airport",
            {},
        )

        origin = departure_airport.get("id")
        destination = arrival_airport.get("id")
        price = flight.get("price")

        if not origin or not destination or price is None:
            continue

        parsed_flight = FlightDeal(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            price=float(price),
            airline=flight.get(
                "airline",
                "Unknown",
            ),
            airline_code=flight.get(
                "airline_code",
                "",
            ),
            stops=int(
                flight.get(
                    "number_of_stops",
                    0,
                )
            ),
            duration_minutes=int(
                flight.get(
                    "duration",
                    0,
                )
            ),
            trip_length=TRIP_DURATION_NAMES.get(
                trip_duration,
                "Unknown",
            ),
        )

        flights.append(parsed_flight)

    return flights


def parse_all_results(
    search_results: list[tuple[int, dict]],
) -> list[FlightDeal]:

    all_flights = []

    for trip_duration, raw_data in search_results:
        flights = parse_flights(
            raw_data=raw_data,
            trip_duration=trip_duration,
        )

        all_flights.extend(flights)

    return all_flights