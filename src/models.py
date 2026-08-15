from dataclasses import dataclass


@dataclass
class FlightDeal:
    origin: str
    destination: str
    departure_date: str
    return_date: str
    price: float
    airline: str
    airline_code: str
    stops: int
    duration_minutes: int
    trip_length: str

    @property
    def duration_hours(self) -> float:
        return round(self.duration_minutes / 60, 1)