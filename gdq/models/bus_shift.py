from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PACIFIC = timezone(timedelta(hours=-8))


@dataclass(order=True, frozen=True)
class Shift:
    start_hour: int
    color: str
    name: str

    def is_active(self, timestamp: datetime) -> bool:
        current_hour = timestamp.astimezone(PACIFIC).hour
        return bool(self.start_hour <= current_hour < self.start_hour + 6)


SHIFTS = [
    Shift(color="\x1b[33", start_hour=6, name="Dawn Guard"),
    Shift(color="\x1b[31", start_hour=12, name="Alpha Flight"),
    Shift(color="\x1b[34", start_hour=18, name="Night Watch"),
    Shift(color="\x1b[35", start_hour=0, name="Zeta"),
]
