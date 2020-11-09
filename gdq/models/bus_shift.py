from dataclasses import dataclass


@dataclass(order=True, frozen=True)
class Shift:
    end_hour: int
    color: str
    name: str


SHIFTS = [
    Shift(color="\x1b[33", end_hour=20, name="Dawn Guard"),
    Shift(color="\x1b[31", end_hour=2, name="Alpha Flight"),
    Shift(color="\x1b[34", end_hour=8, name="Night Watch"),
    Shift(color="\x1b[35", end_hour=14, name="Zeta"),
]
