import math
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Self

from gdq import utils
from gdq.models.bus_shift import SHIFTS
from gdq.money import Dollar


@dataclass(order=True, frozen=True)
class Record:
    total: Dollar
    year: int
    hope: bool = False
    number: str = ""
    subtitle: str = ""

    def __str__(self: Self) -> str:
        name = (
            f"Desert Bus{' For Hope' if self.hope else ''} {self.number or self.year}"
        )
        if self.subtitle:
            name += f": {self.subtitle}"
        return name

    @property
    def hours(self: Self) -> int:
        return dollars_to_hours(self.total)

    def distance(self: Self, current: Dollar) -> str:
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
    Record(year=2021, total=Dollar(1_223_108.83)),
    Record(year=2022, total=Dollar(1_138_674.80)),
]
FakeRecord = tuple[Dollar, str, bool]
LIFETIME = sum([record.total for record in RECORDS], Dollar())


class DesertBuck(Dollar):
    _symbol = "d฿"

    def __init__(self: Self, value: Dollar) -> None:
        super().__init__(value / RECORDS[0].total)


class DesertToonie(Dollar):
    _symbol = "d฿²"

    def __init__(self: Self, value: Dollar) -> None:
        super().__init__(value / RECORDS[1].total)


class DesertBus:
    _start: datetime
    total: Dollar
    offline: bool = False
    width: int = 0

    def __init__(self: Self, start: datetime) -> None:
        self._start = start

    @property
    def hours(self: Self) -> int:
        return dollars_to_hours(self.total)

    @property
    def estimate(self: Self) -> Dollar:
        future_hours = 0
        future_total = self.total
        while future_hours != dollars_to_hours(future_total):
            future_hours = dollars_to_hours(future_total)
            if utils.now > self.start:
                future_multiplier = timedelta(hours=future_hours) / (
                    utils.now - self.start
                )
            else:
                future_multiplier = 1
            future_total = self.total * future_multiplier
        return future_total

    @property
    def start(self: Self) -> datetime:
        return self._start

    @property
    def end(self: Self) -> datetime:
        return self.start + timedelta(hours=self.hours)

    def header(self: Self, *, extended: bool = False) -> Iterable[str]:
        if utils.now < self.start:
            yield f"Starting in {self.start - utils.now}".center(self.width)
        elif utils.now < (self.start + timedelta(hours=self.hours + 1)):
            yield self.shift_banners(utils.now)
        else:
            yield "It's over!"

        yield "|".join(
            even_banner(
                [
                    str(self.total),
                    f"{self.hours} hours",
                    str(DesertBuck(self.total)),
                    str(DesertToonie(self.total)),
                ],
                self.width,
            ),
        )
        if extended:
            totals = []
            if utils.now > self.start:
                estimate = self.estimate
                totals.append(f"{estimate} estimated ({dollars_to_hours(estimate)}h)")
            totals.append(f"{self.total + LIFETIME} lifetime")
            yield "|".join(even_banner(totals, self.width))

    def render(self: Self) -> Iterable[str]:
        if utils.now < self.start + (timedelta(hours=(self.hours + 1))):
            yield from self.print_records()

    def footer(self: Self, *, overall: bool = False) -> Iterable[str]:
        start = self.start
        elapsed = max(utils.now - start, timedelta())
        total = timedelta(hours=self.hours)
        remaining = min(start + total - utils.now, total)

        hours_done = f"[{utils.timedelta_as_hours(elapsed)}]"
        hours_left = f"[{utils.timedelta_as_hours(remaining)}]"
        progress_width = self.width - len(hours_done) - len(hours_left) - 3

        # Scaled to last passed record
        last_record = timedelta()
        future_stops = []

        for record in sorted(RECORDS):
            td_record = timedelta(hours=dollars_to_hours(record.total))
            if td_record <= elapsed:
                # We've passed this record, but make a note that we've come this far.
                last_record = td_record
            elif td_record < total:
                # In the future, but still on the hook for it.
                future_stops.append(td_record)
            else:
                # Don't worry about records we havent reached yet.
                break

        if overall:
            last_record = timedelta()

        try:
            completed_width = math.floor(
                progress_width * (elapsed - last_record) / (total - last_record),
            )
        except ZeroDivisionError:
            completed_width = 0
        progress = (
            f"{'─' * completed_width}🚍{' ' * (progress_width - completed_width - 1)}🏁"
        )

        for stop in future_stops:
            stop_location = math.floor(
                (last_record - stop) / (last_record - total) * progress_width,
            )
            if progress[stop_location : stop_location + 2] == "  ":
                progress = (
                    progress[:stop_location] + "🚏" + progress[stop_location + 2 :]
                )

        yield f"{hours_done}{progress}{hours_left}"

    def shift_banners(self: Self, timestamp: datetime) -> str:
        # Shift detection
        if timestamp > self.end - timedelta(hours=4):
            return "|".join(even_banner(list("OMEGA"), self.width))

        banners = even_banner(
            [shift.name for shift in SHIFTS],
            self.width,
            fill_char="═",
        )

        for index, shift in enumerate(SHIFTS):
            boldness = 2
            if shift.is_active(timestamp):
                boldness = 7
            banners[index] = f"{shift.color};{boldness}m{banners[index]}\x1b[0m"

        return "|".join(banners)

    def print_records(self: Self) -> Iterable[str]:
        yield ""

        others = self.artificial_records()
        next_other = next(others)
        while next_other[0] <= self.total:
            next_other = next(others)

        next_level = Dollar()
        for event in sorted(RECORDS):
            if event.total > self.total:
                while next_other[0] < event.total:
                    yield f"{next_other[0] - self.total} until {next_other[1]}"
                    if not next_other[2]:
                        return
                    next_other = next(others)

                yield event.distance(self.total)
                next_level = event.total

        if next_level == Dollar():
            yield "NEW RECORD!"

        while True:
            yield f"{next_other[0] - self.total} until {next_other[1]}"
            next_other = next(others)

    def artificial_records(self: Self) -> Iterator[FakeRecord]:
        records: list[tuple[FakeRecord, Iterator[FakeRecord]]] = [
            (
                (self.estimate, f"current estimate ({self.estimate})", False),
                iter(lambda: (Dollar(sys.maxsize), "", True), 0),
            ),
        ]

        hours = self.next_hours()
        records.append((next(hours), hours))
        numbers = self.fun_numbers()
        records.append((next(numbers), numbers))
        lifetimes = self.fun_numbers(lifetime=True)
        records.append((next(lifetimes), lifetimes))

        while True:
            records.sort()
            value, generator = records.pop(0)
            records.append((next(generator), generator))
            yield value

    def next_hours(self: Self) -> Iterator[FakeRecord]:
        hour = dollars_to_hours(self.total) + 1
        while True:
            if hour % 24 == 0:
                yield hours_to_dollars(
                    hour,
                ), f"hour {hour} ({hour // 24} days!)", True
            else:
                yield hours_to_dollars(hour), f"hour {hour}", True
            hour += 1

    def fun_numbers(self: Self, *, lifetime: bool = False) -> Iterator[FakeRecord]:
        zeroes = 0
        while True:
            for fives in range(2, 20):
                current = Dollar(fives * 5 * 10**zeroes)
                if lifetime:
                    if self.total + LIFETIME < current:
                        yield current - LIFETIME, f"{current} lifetime", True
                elif self.total < current:
                    yield current, str(current), True
            zeroes += 1


def dollars_to_hours(dollars: Dollar, rate: float = 1.07) -> int:
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars.to_float() * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours: int, rate: float = 1.07) -> Dollar:
    return Dollar((1 - (rate**hours)) / (1 - rate))


def even_banner(items: list[str], width: int = 80, fill_char: str = " ") -> list[str]:
    width -= len(items) - 1
    min_width = sum(len(s) for s in items)
    # reflow is extra spaces that should be distributed amongst the
    # groups in the banner.
    reflow = 0
    if width <= max(len(s) for s in items) * len(items):
        shift_width = 0
        if width > min_width:
            # reflow is negative, width will be compressed if possible
            reflow = min_width - width
    else:
        shift_width = width // len(items)
        # reflow is positive, an extra space will be added
        reflow = width - (shift_width * len(items))

    for index, stat in enumerate(items):
        mod = 0
        if reflow < 0 and index == len(items) - 1:
            mod = len(items) - reflow
        elif int(index * reflow / len(items)) > int((index - 1) * reflow / len(items)):
            mod = 1
        items[index] = stat.center(shift_width + mod, fill_char)

    return items
