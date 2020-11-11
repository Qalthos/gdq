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
    name: str = ""

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

    def distance(self, current: Dollar) -> str:
        next_level = self.total - current
        if next_level <= Dollar():
            return ""

        if self.name:
            return f"{next_level} until {self.name}"
        return f"{next_level} until Desert Bus {self.year}"


RECORDS = [
    Record(year=2007, total=Dollar(22_805.00), name="Desert Bus for Hope"),
    Record(year=2008, total=Dollar(70_423.79), name="Desert Bus for Hope 2: Bus Harder"),
    Record(year=2009, total=Dollar(140_449.68), name="Desert Bus for Hope 3: It's Desert Bus 6 in Japan"),
    Record(year=2010, total=Dollar(208_250.00), name="Desert Bus for Hope 4: A New Hope"),
    Record(year=2011, total=Dollar(383_125.10), name="Desert Bus for Hope 5: De5ert Bus"),
    Record(year=2012, total=Dollar(443_630.00), name="Desert Bus for Hope 6: Desert Bus 3 in America"),
    Record(year=2013, total=Dollar(523_520.00), name="Desert Bus for Hope 007"),
    Record(year=2014, total=Dollar(643_242.58), name="Desert Bus for Hope 8"),
    Record(year=2015, total=Dollar(683_720.00), name="Desert Bus for Hope 9: The Joy of Bussing"),
    Record(year=2016, total=Dollar(695_242.57), name="Desert Bus X"),
    Record(year=2017, total=Dollar(650_215.00)),
    Record(year=2018, total=Dollar(730_099.90)),
    Record(year=2019, total=Dollar(865_015.00)),
]


class DesertBus(Marathon):
    start: datetime
    total: Dollar

    def __init__(self, start: datetime):
        self.start = start

    def refresh_all(self) -> None:
        # Money raised
        state = requests.get("https://desertbus.org/wapi/init").json()
        self.total = Dollar(state["total"])

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

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
        if args:
            # Reserved for future use
            pass

        if utils.now < self.start:
            yield f"Starting in {self.start - utils.now}".center(width)
        elif utils.now < (self.start + timedelta(hours=self.hours + 1)):
            yield from shift_banners(utils.now, width)
        else:
            yield "It's over!"

        yield f"{self.total} | {self.hours} hours | d฿{self.desert_bucks:,.2f} | d฿²{self.desert_toonies:,.2f}"
        yield f"{self.total + sum([record.total for record in RECORDS], Dollar())} lifetime total."

    def render(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if width:
            # Reserved for future use
            pass

        if args:
            # Reserved for future use
            pass

        if utils.now < self.start + (timedelta(hours=(self.hours + 1))):
            if utils.now > self.start:
                yield self.calculate_estimate()
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
        return f"{future_total} estimated total ({future_hours} hours)"

    def print_records(self) -> Iterable[str]:
        yield ""

        last_hour = self.hours
        next_level = Dollar()
        fun_iter = fun_numbers(self.total)
        next_fun = next(fun_iter)
        for event in sorted(RECORDS):
            if event.total > self.total:
                while event.hours > last_hour:
                    last_hour += 1
                    next_hour = hours_to_dollars(last_hour)
                    if next_hour > next_fun:
                        yield f"{next_fun - self.total} until {next_fun}"
                        next_fun = next(fun_iter)
                    yield distance_to_hour(self.total, last_hour)

                event.distance(self.total)
                next_level = event.total

        if next_level == Dollar():
            yield "NEW RECORD!"

        last_hour += 1
        yield distance_to_hour(self.total, last_hour)


def dollars_to_hours(dollars: Dollar, rate: float = 1.07) -> int:
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars.to_float() * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours: int, rate: float = 1.07) -> Dollar:
    return Dollar((1 - (rate ** hours)) / (1 - rate))


def shift_banners(timestamp: datetime, width: int) -> str:
    # Shift detection
    shifts = sorted(SHIFTS)
    for shift in shifts:
        if timestamp.hour < shift.end_hour:
            break
    else:
        shift = shifts[0]

    banners = []
    min_width = 10 + 12 + 11 + 4 + 3

    reflow = 0
    if width <= (11 * 4) + 3:
        shift_width = 0
        if width >= min_width:
            reflow = min_width - width
    else:
        shift_width = (width - 3) // 4
        reflow = width - 3 - (shift_width * 4)

    for index, shift_info in enumerate(SHIFTS):
        boldness = "2"
        if shift_info == shift:
            boldness = "7"

        mod = 0
        if reflow < 0 and index == 3:
            mod = 4 - reflow
        elif index < reflow:
            mod = 1
        banners.append(f"{shift_info.color};{boldness}m{shift_info.name.center(shift_width+mod, '═')}\x1b[0m")

    return "|".join(banners)


def distance_to_hour(current: Dollar, hour: int) -> str:
    next_hour = hours_to_dollars(hour) - current
    if hour % 24 == 0:
        return f"{next_hour} until hour {hour} ({hour // 24} days!)"
    return f"{next_hour} until hour {hour}"


def fun_numbers(start: Dollar) -> Iterator[Dollar]:
    bases = (1, 2, 5)
    zeroes = 0
    while True:
        for base in bases:
            current = Dollar(base * 10 ** zeroes)
            if start < current:
                yield current
                start = current
        zeroes += 1
