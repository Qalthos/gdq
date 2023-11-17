import math
from dataclasses import dataclass

from gdq.money import Dollar


@dataclass(order=True, frozen=True)
class Record:
    total: Dollar
    year: int
    hope: bool = False
    number: str = ""
    subtitle: str = ""

    def __str__(self) -> str:
        name = (
            f"Desert Bus{' For Hope' if self.hope else ''} {self.number or self.year}"
        )
        if self.subtitle:
            name += f": {self.subtitle}"
        return name

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

    def distance(self, current: Dollar) -> str:
        next_level = self.total - current
        if next_level <= Dollar():
            return ""

        return f"{next_level} until {self!s}"


RECORDS = [
    Record(year=2007, total=Dollar(22_805.00), hope=True, number="\033[D"),
    Record(
        year=2008,
        total=Dollar(70_423.79),
        hope=True,
        number="2",
        subtitle="Bus Harder",
    ),
    Record(
        year=2009,
        total=Dollar(140_449.68),
        hope=True,
        number="3",
        subtitle="It's Desert Bus 6 in Japan",
    ),
    Record(
        year=2010,
        total=Dollar(209_482.00),
        hope=True,
        number="4",
        subtitle="A New Hope",
    ),
    Record(
        year=2011,
        total=Dollar(383_125.10),
        hope=True,
        number="5",
        subtitle="De5ert Bus",
    ),
    Record(
        year=2012,
        total=Dollar(443_630.00),
        hope=True,
        number="6",
        subtitle="Desert Bus 3 in America",
    ),
    Record(year=2013, total=Dollar(523_520.00), hope=True, number="007"),
    Record(year=2014, total=Dollar(643_242.58), hope=True, number="8"),
    Record(
        year=2015,
        total=Dollar(683_720.00),
        hope=True,
        number="9",
        subtitle="The Joy of Bussing",
    ),
    Record(year=2016, total=Dollar(695_242.57), number="X"),
    Record(year=2017, total=Dollar(655_402.56)),
    Record(year=2018, total=Dollar(730_099.90), subtitle="The Bus Place"),
    Record(year=2019, total=Dollar(865_015.00), subtitle="Untitled Bus Fundraiser"),
    Record(year=2020, total=Dollar(1_052_902.40)),
    Record(year=2021, total=Dollar(1_223_108.83), subtitle="Ajony"),
    Record(year=2022, total=Dollar(1_138_674.80), subtitle="Target Kids"),
]

LIFETIME = sum([record.total for record in RECORDS], Dollar())


def dollars_to_hours(dollars: Dollar, rate: float = 1.07) -> int:
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars.to_float() * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours: int, rate: float = 1.07) -> Dollar:
    return Dollar((1 - (rate**hours)) / (1 - rate))
