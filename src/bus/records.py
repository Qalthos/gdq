import json
import math
from dataclasses import dataclass
from importlib import resources
from typing import NotRequired, Self, TypedDict

from gdq.money import Dollar


class RecordJSON(TypedDict):
    total: float
    year: int
    number: NotRequired[int | str]
    subtitle: NotRequired[str]


@dataclass(order=True, frozen=True)
class Record:
    total: Dollar
    year: int
    number: int | str = ""
    subtitle: str = ""

    def __str__(self) -> str:
        name = f"Desert Bus For Hope {self.number or self.year}"
        if self.subtitle:
            name += f": {self.subtitle}"
        return name

    @classmethod
    def from_json(cls, data: RecordJSON) -> Self:
        total = Dollar(data["total"])
        return cls(
            total=total,
            year=data["year"],
            number=data.get("number", ""),
            subtitle=data.get("subtitle", ""),
        )

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

    def distance(self, current: Dollar) -> str:
        next_level = self.total - current
        if next_level <= Dollar():
            return ""

        return f"{next_level} until {self!s}"


def dollars_to_hours(dollars: Dollar, rate: float = 1.07) -> int:
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars.to_float() * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours: int, rate: float = 1.07) -> Dollar:
    return Dollar((1 - (rate**hours)) / (1 - rate))


records_file = resources.files("bus") / "records.json"
records = json.loads(records_file.read_text())
RECORDS: list[Record] = [Record.from_json(record) for record in records]
LIFETIME = sum([record.total for record in RECORDS], Dollar())
