import smtplib
from email.message import EmailMessage

from src.models import FlightDeal
from src.flight_ranker import calculate_score


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


def build_email_body(
    flights: list[FlightDeal],
    max_results: int,
) -> str:

    if not flights:
        return (
            "Cape Town Flight Tracker\n\n"
            "No flights matching your criteria "
            "were found today."
        )

    lines = [
        "Cape Town Flight Tracker",
        "",
        "Today's Best Deals",
        "=" * 40,
        "",
    ]

    for index, flight in enumerate(
        flights[:max_results],
        start=1,
    ):

        lines.extend(
            [
                f"{index}. {flight.origin} → "
                f"{flight.destination}",
                (
                    f"   {flight.departure_date} → "
                    f"{flight.return_date}"
                ),
                f"   Price: ${flight.price:,.0f}",
                f"   Airline: {flight.airline}",
                f"   Stops: {flight.stops}",
                (
                    f"   Duration: "
                    f"{flight.duration_hours} hours"
                ),
                f"   Trip length: {flight.trip_length}",
                (
                    f"   Deal score: "
                    f"{calculate_score(flight):.0f}"
                ),
                "",
            ]
        )

    return "\n".join(lines)


def send_email(
    sender: str,
    app_password: str,
    recipient: str,
    flights: list[FlightDeal],
    max_results: int = 10,
) -> None:

    message = EmailMessage()

    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = (
        "Daily Cape Town Flight Deals"
    )

    body = build_email_body(
        flights=flights,
        max_results=max_results,
    )

    message.set_content(body)

    with smtplib.SMTP_SSL(
        SMTP_SERVER,
        SMTP_PORT,
    ) as smtp:

        smtp.login(
            sender,
            app_password,
        )

        smtp.send_message(message)