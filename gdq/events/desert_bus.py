import argparse
import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests

from gdq import utils
from gdq.events import Marathon
from gdq.money import Dollar


@dataclass(order=True, frozen=True)
class Record:
    total: Dollar
    year: int
    name: str = ""


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
            yield from shift_banners(utils.now)
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
        td_bussed = max(utils.now - self.start, timedelta())
        td_total = timedelta(hours=self.hours)
        td_remaining = min(self.start + td_total - utils.now, td_total)

        hours_done = f"[{timedelta_as_hours(td_bussed)}]"
        hours_left = f"[{timedelta_as_hours(td_remaining)}]"
        progress_width = width - len(hours_done) - len(hours_left) - 3

        # Scaled to last passed record
        last_record = timedelta()
        future_stops = []

        for record in sorted(RECORDS):
            td_record = timedelta(hours=dollars_to_hours(record.total))
            if td_record <= td_bussed:
                # We've passed this record, but make a note that we've come this far.
                last_record = td_record
            elif td_record < td_total:
                # In the future, but still on the hook for it.
                future_stops.append(td_record)
            else:
                # Don't worry about records we havent reached yet.
                break

        if args.overall:
            last_record = timedelta()

        bussed_width = math.floor(
            progress_width * (td_bussed - last_record) / (td_total - last_record)
        )
        bus = f"{'─' * bussed_width}🚍{' ' * (progress_width - bussed_width - 1)}🏁"

        for stop in future_stops:
            stop_location = math.floor(
                (last_record - stop) / (last_record - td_total) * progress_width
            )
            if bus[stop_location:stop_location + 2] == "  ":
                bus = bus[:stop_location] + "🚏" + bus[stop_location + 2:]

        yield f"{hours_done}{bus}{hours_left}\x1b[0m"

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
        for event in sorted(RECORDS):
            record = event.total
            if record > self.total:
                hours = dollars_to_hours(record)
                while hours > last_hour:
                    last_hour += 1
                    next_hour = hours_to_dollars(last_hour) - self.total
                    yield f"{next_hour} until hour {last_hour}"

                next_level = record - self.total
                if event.name:
                    yield f"{next_level} until {event.name}"
                else:
                    yield f"{next_level} until Desert Bus {event.year}"

        if next_level == Dollar():
            yield "NEW RECORD!"

        last_hour += 1
        yield f"{hours_to_dollars(last_hour) - self.total} until hour {last_hour}"


def dollars_to_hours(dollars: Dollar, rate: float = 1.07) -> int:
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars.to_float() * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours: int, rate: float = 1.07) -> Dollar:
    return Dollar((1 - (rate ** hours)) / (1 - rate))


def shift_banners(timestamp: datetime) -> str:
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
    if utils.term_width <= (11 * 4) + 3:
        shift_width = 0
        if utils.term_width >= min_width:
            reflow = min_width - utils.term_width
    else:
        shift_width = (utils.term_width - 3) // 4
        reflow = utils.term_width - 3 - (shift_width * 4)

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


def timedelta_as_hours(delta: timedelta) -> str:
    """Format a timedelta in HHH:MM format."""

    minutes = delta.total_seconds() // 60
    hours, minutes = divmod(minutes, 60)

    return f"{hours:.0f}:{minutes:02.0f}"
