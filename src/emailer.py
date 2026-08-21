"""Build and send a grouped flight-deal report through Gmail SMTP."""

import smtplib
from email.message import EmailMessage

from src.flight_ranker import calculate_score
from src.models import FlightDeal, PriceTrend, SearchReport


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

        lines.extend(_format_price_trends(report.price_trends, report.currency))

        for index, flight in enumerate(
            report.flights[:max_results_per_search], start=1
        ):
            lines.extend(_format_flight(index, flight, report.currency))

    return "\n".join(lines)


def _format_price_trends(
    trends: tuple[PriceTrend, ...],
    currency: str,
) -> list[str]:
    """Format best-fare movements as a compact report summary."""

    if not trends:
        return []

    lines = ["Price trends (cheapest fare by run):"]
    for trend in trends:
        current = format_price(trend.current_lowest, currency)
        movement = _format_price_movement(trend, currency)
        tracked_range = (
            f"{format_price(trend.tracked_lowest, currency)}–"
            f"{format_price(trend.tracked_highest, currency)}"
        )
        run_label = "run" if trend.tracked_runs == 1 else "runs"
        lines.append(
            f"  {trend.trip_length}: {current} now | {movement} | "
            f"tracked {tracked_range} over {trend.tracked_runs} {run_label}"
        )

    lines.append("")
    return lines


def _format_price_movement(trend: PriceTrend, currency: str) -> str:
    """Describe a trend's movement relative to the previous tracker run."""

    change = trend.change_amount
    percent = trend.change_percent
    previous_lowest = trend.previous_lowest
    if change is None or percent is None or previous_lowest is None:
        return "first tracked result"
    if change == 0:
        return "no change vs previous run"

    direction = "↓" if change < 0 else "↑"
    amount = format_price(abs(change), currency)
    previous = format_price(previous_lowest, currency)
    return f"{direction} {amount} ({abs(percent):.1f}%) vs {previous}"


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
