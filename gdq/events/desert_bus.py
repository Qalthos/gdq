import argparse
import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests

from gdq import utils
from gdq.events import Marathon
from gdq.models.bus_shift import SHIFTS
from gdq.money import Dollar


@dataclass(order=True, frozen=True)
class Record:
    total: Dollar
    year: int
    hope: bool = False
    number: str = ""
    subtitle: str = ""

    def __str__(self) -> str:
        name = f"Desert Bus{' For Hope' if self.hope else ''} {self.number or self.year}"
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
    Record(year=2007, total=Dollar(22_805.00), hope=True),
    Record(year=2008, total=Dollar(70_423.79), hope=True, number="2", subtitle="Bus Harder"),
    Record(year=2009, total=Dollar(140_449.68), hope=True, number="3", subtitle="It's Desert Bus 6 in Japan"),
    Record(year=2010, total=Dollar(209_482.00), hope=True, number="4", subtitle="A New Hope"),
    Record(year=2011, total=Dollar(383_125.10), hope=True, number="5", subtitle="De5ert Bus"),
    Record(year=2012, total=Dollar(443_630.00), hope=True, number="6", subtitle="Desert Bus 3 in America"),
    Record(year=2013, total=Dollar(523_520.00), hope=True, number="007"),
    Record(year=2014, total=Dollar(643_242.58), hope=True, number="8"),
    Record(year=2015, total=Dollar(683_720.00), hope=True, number="9", subtitle="The Joy of Bussing"),
    Record(year=2016, total=Dollar(695_242.57), number="X"),
    Record(year=2017, total=Dollar(655_402.56)),
    Record(year=2018, total=Dollar(730_099.90)),
    Record(year=2019, total=Dollar(865_015.00), subtitle="Untitled Bus Fundraiser"),
]


class DesertBus(Marathon):
    _start: datetime
    total: Dollar
    offline: bool = False

    def __init__(self, start: datetime):
        self._start = start

    def refresh_all(self) -> None:
        # Money raised
        try:
            state = requests.get("https://desertbus.org/wapi/init").json()
        except IOError:
            self.offline = True
        else:
            self.total = Dollar(state["total"])
            self.offline = False

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self.start + timedelta(hours=self.hours)

    @property
    def desert_bucks(self) -> float:
        return self.total / RECORDS[0].total

    @property
    def desert_toonies(self) -> float:
        return self.total / RECORDS[1].total

    def header(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if utils.now < self.start:
            yield f"Starting in {self.start - utils.now}".center(width)
        elif utils.now < (self.start + timedelta(hours=self.hours + 1)):
            yield shift_banners(utils.now, width)
        else:
            yield "It's over!"

        yield "|".join(even_banner(
            [
                str(self.total),
                f"{self.hours} hours",
                f"d฿{self.desert_bucks:,.2f}",
                f"d฿²{self.desert_toonies:,.2f}",
            ],
            width,
        ))
        if args.extended_header:
            totals = []
            if utils.now > self.start:
                totals.append(self.calculate_estimate())
            totals.append(f"{self.total + sum([record.total for record in RECORDS], Dollar())} lifetime")
            yield "|".join(even_banner(totals, width))

    def render(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if width:
            # Reserved for future use
            pass

        if args:
            # Reserved for future use
            pass

        if utils.now < self.start + (timedelta(hours=(self.hours + 1))):
            yield from self.print_records()

    def footer(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        start = self.start
        elapsed = max(utils.now - start, timedelta())
        total = timedelta(hours=self.hours)
        remaining = min(start + total - utils.now, total)

        hours_done = f"[{utils.timedelta_as_hours(elapsed)}]"
        hours_left = f"[{utils.timedelta_as_hours(remaining)}]"
        progress_width = width - len(hours_done) - len(hours_left) - 3

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

        if args.overall:
            last_record = timedelta()

        completed_width = math.floor(
            progress_width * (elapsed - last_record) / (total - last_record)
        )
        progress = f"{'─' * completed_width}🚍{' ' * (progress_width - completed_width - 1)}🏁"

        for stop in future_stops:
            stop_location = math.floor(
                (last_record - stop) / (last_record - total) * progress_width
            )
            if progress[stop_location:stop_location + 2] == "  ":
                progress = progress[:stop_location] + "🚏" + progress[stop_location + 2:]

        yield f"{hours_done}{progress}{hours_left}"

    def calculate_estimate(self) -> str:
        future_hours = 0
        future_total = self.total
        while future_hours != dollars_to_hours(future_total):
            future_hours = dollars_to_hours(future_total)
            future_multiplier = timedelta(hours=future_hours) / (utils.now - self.start)
            future_total = self.total * future_multiplier
        return f"{future_total} estimated ({future_hours}h)"

    def print_records(self) -> Iterable[str]:
        yield ""

        others = artificial_records(self.total)
        next_other = next(others)
        for event in sorted(RECORDS):
            if event.total > self.total:
                while next_other[0] < event.total:
                    yield f"{next_other[0] - self.total} until {next_other[1]}"
                    next_other = next(others)

                yield event.distance(self.total)
                next_level = event.total

        if next_level == Dollar():
            yield "NEW RECORD!"

        yield f"{next_other[0] - self.total} until {next_other[1]}"


def dollars_to_hours(dollars: Dollar, rate: float = 1.07) -> int:
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars.to_float() * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours: int, rate: float = 1.07) -> Dollar:
    return Dollar((1 - (rate ** hours)) / (1 - rate))


def shift_banners(timestamp: datetime, width: int) -> str:
    # Shift detection
    banners = even_banner([shift.name for shift in SHIFTS], width, fill_char='═')

    for index, shift in enumerate(SHIFTS):
        boldness = 2
        if shift.is_active(timestamp):
            boldness = 7
        banners[index] = f"{shift.color};{boldness}m{banners[index]}\x1b[0m"

    return "|".join(banners)


def artificial_records(start: Dollar) -> Iterator[tuple[Dollar, str]]:
    def next_hours(start: Dollar) -> Iterator[tuple[Dollar, str]]:
        hour = dollars_to_hours(start) + 1
        while True:
            if hour % 24 == 0:
                yield hours_to_dollars(hour), f"hour {hour} ({hour // 24} days!)"
            else:
                yield hours_to_dollars(hour), f"hour {hour}"
            hour += 1
    hours = next_hours(start)
    next_hour = next(hours)

    def fun_numbers(start: Dollar) -> Iterator[tuple[Dollar, str]]:
        bases = (1, 2, 5)
        zeroes = 0
        while True:
            for base in bases:
                current = Dollar(base * 10 ** zeroes)
                if start < current:
                    yield current, str(current)
                    start = current
            zeroes += 1
    numbers = fun_numbers(start)
    next_number = next(numbers)

    while True:
        if next_hour < next_number:
            yield next_hour
            next_hour = next(hours)
        else:
            yield next_number
            next_number = next(numbers)


def even_banner(items: list[str], width: int, fill_char: str = " ") -> list[str]:
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
