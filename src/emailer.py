"""Build and send a grouped flight-deal report through Gmail SMTP."""

import smtplib
from email.message import EmailMessage

from src.flight_ranker import calculate_score
from src.models import FlightDeal, SearchReport


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
}


def format_price(price: float, currency: str) -> str:
    """Format a price with a familiar symbol and its currency code."""

    normalized_currency = currency.upper()
    symbol = CURRENCY_SYMBOLS.get(normalized_currency, "")
    return f"{symbol}{price:,.0f} {normalized_currency}"


def build_email_body(
    reports: tuple[SearchReport, ...],
    max_results_per_search: int,
) -> str:
    """Create a plain-text email with one section per configured search."""

    lines = ["Flight Deal Tracker", "", "Today's Best Deals", "=" * 40, ""]

    for report in reports:
        lines.extend([report.name, "-" * len(report.name)])

        if not report.flights:
            lines.extend(["No matching flights were found.", ""])
            continue

        for index, flight in enumerate(
            report.flights[:max_results_per_search], start=1
        ):
            lines.extend(_format_flight(index, flight, report.currency))

    return "\n".join(lines)


def _format_flight(
    index: int,
    flight: FlightDeal,
    currency: str,
) -> list[str]:
    """Format one flight as readable lines for the report body."""

    return [
        f"{index}. {flight.origin} → {flight.destination}",
        f"   {flight.departure_date} → {flight.return_date}",
        f"   Price: {format_price(flight.price, currency)}",
        f"   Airline: {flight.airline}",
        f"   Stops: {flight.stops}",
        f"   Duration: {flight.duration_hours} hours",
        f"   Trip length: {flight.trip_length}",
        f"   Deal score: {calculate_score(flight):.0f}",
        "",
    ]


def build_email_message(
    sender: str,
    recipient: str,
    reports: tuple[SearchReport, ...],
    max_results_per_search: int,
) -> EmailMessage:
    """Build the complete message without opening a network connection."""

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = "Your Flight Deal Report"
    message.set_content(
        build_email_body(
            reports=reports,
            max_results_per_search=max_results_per_search,
        )
    )
    return message


def send_email(
    sender: str,
    app_password: str,
    recipient: str,
    reports: tuple[SearchReport, ...],
    max_results_per_search: int = 10,
) -> None:
    """Authenticate with Gmail SMTP and send the grouped deal report."""

    message = build_email_message(
        sender=sender,
        recipient=recipient,
        reports=reports,
        max_results_per_search=max_results_per_search,
    )

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(message)
