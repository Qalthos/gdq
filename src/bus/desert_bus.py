# Copyright 2024
# SPDX-License-Identifier: MIT
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from bus.db_api import get_events
from bus.shifts import OMEGA, SHIFTS, Shift
from bus.utils import dollars_to_hours, hours_to_dollars
from gdq import utils
from gdq.money import Dollar

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence


RECORDS = get_events("12pEtImeluwLBvtnl7zlaV")
RECORDS.reverse()
LIFETIME = sum((event.total for event in RECORDS), start=Dollar(0))


class Record(Protocol):
    total: Dollar
    name: str


def record_key(record: Record):
    return record.total


@dataclass
class VirtualRecord:
    total: Dollar
    name: str


class DesertBuck(Dollar):
    _symbol = "d฿"

    def __init__(self, value: Dollar):
        super().__init__(value / RECORDS[0].total)


class DesertToonie(Dollar):
    _symbol = "d฿²"

    def __init__(self, value: Dollar):
        super().__init__(value / RECORDS[1].total)


class DesertBus:
    _start: datetime
    total: Dollar = Dollar(0)
    offline: bool = False
    width: int = 0

    def __init__(self, start: datetime):
        self._start = start

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

    @property
    def estimate(self) -> VirtualRecord:
        now = datetime.now(UTC).replace(microsecond=0, second=0)
        future_hours = 0
        future_total = self.total
        current_hours = min(now - self.start, timedelta(hours=self.hours))
        while future_hours != dollars_to_hours(future_total):
            future_hours = dollars_to_hours(future_total)
            future_multiplier = timedelta(hours=future_hours) / (current_hours) if now > self.start else 1
            future_total = self.total * future_multiplier
        return VirtualRecord(future_total, f"current estimate ({future_total})")

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self.start + timedelta(hours=self.hours)

    def header(self, *, extended: bool = True) -> Iterable[str]:
        now = datetime.now(UTC).replace(microsecond=0)
        if now < self.start:
            yield f"Starting in {self.start - now}".center(self.width)
        elif now < (self.start + timedelta(hours=self.hours + 1)):
            yield self.shift_banners(now)
        else:
            yield "It's over!".center(self.width)

        yield "|".join(
            _even_banner(
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
            if now > self.start:
                estimate = self.estimate
                totals.append(f"{estimate.total} estimated ({dollars_to_hours(estimate.total)}h)")
            totals.append(f"{self.total + LIFETIME} lifetime")
            yield "|".join(_even_banner(totals, self.width))

    def render(self) -> Iterable[str]:
        now = datetime.now(UTC)
        if now < self.start + (timedelta(hours=(self.hours + 1))):
            yield from self.print_records()

    def footer(self, *, overall: bool = True) -> Iterable[str]:
        now = datetime.now(UTC)
        total = timedelta(hours=self.hours)
        elapsed = max(min(now - self.start, total), timedelta())
        remaining = total - elapsed

        hours_done = f"[{utils.timedelta_as_hours(elapsed)}]"
        hours_left = f"[{utils.timedelta_as_hours(remaining)}]"
        progress_width = self.width - len(hours_done) - len(hours_left) - 4

        # Scaled to last passed record
        last_record = timedelta()
        future_stops = []

        for record in sorted(RECORDS, key=record_key):
            td_record = timedelta(hours=dollars_to_hours(record.total))
            if td_record <= elapsed:
                # We've passed this record, but make a note that we've come this far.
                last_record = td_record
            elif td_record < total:
                # In the future, but still on the hook for it.
                future_stops.append(td_record)
            else:
                # Don't worry about records we haven't reached yet.
                break

        if overall:
            last_record = timedelta()

        try:
            completed_width = math.floor(
                progress_width * (elapsed - last_record) / (total - last_record),
            )
        except ZeroDivisionError:
            completed_width = 0
        progress = f"{'─' * completed_width}🚍{' ' * (progress_width - completed_width - 1)}🏁"

        for stop in future_stops:
            stop_location = math.floor(
                (last_record - stop) / (last_record - total) * progress_width,
            )
            if progress[stop_location : stop_location + 2] == "  ":
                progress = progress[:stop_location] + "🚏" + progress[stop_location + 2 :]

        yield f"{hours_done}{progress}{hours_left}"

    def shift_banners(self, timestamp: datetime) -> str:
        shifts: Sequence[Shift] = SHIFTS
        # OMEGA detected
        if timestamp > self.end - timedelta(hours=3):
            shifts = OMEGA

        banners = _even_banner(
            [shift.name for shift in shifts],
            self.width,
            fill_char="═",
        )

        for index, shift in enumerate(shifts):
            boldness = 2
            if shift.is_active(timestamp):
                boldness = 7
            banners[index] = f"{shift.color};{boldness}m{banners[index]}\x1b[0m"

        return "|".join(banners)

    def print_records(self) -> Iterable[str]:
        others = self.artificial_records()
        next_other, sentinel = next(others)
        while next_other.total <= self.total:
            next_other, sentinel = next(others)

        next_level = Dollar()
        for event in sorted(RECORDS, key=record_key):
            if event.total > self.total:
                while next_other.total < event.total:
                    yield f"{next_other.total - self.total} until {next_other.name}"
                    if not sentinel:
                        return
                    next_other, sentinel = next(others)

                yield event.distance(self.total)
                next_level = event.total

        if next_level == Dollar():
            yield "NEW RECORD!"

        while True:
            yield f"{next_other.total - self.total} until {next_other.name}"
            next_other, sentinel = next(others)

    def artificial_records(self) -> Iterator[tuple[Record, bool]]:
        records: list[tuple[Record, bool, Iterator[tuple[Record, bool]]]] = [
            (
                self.estimate,
                False,
                iter(lambda: (VirtualRecord(Dollar(sys.maxsize), ""), True), 0),
            ),
        ]

        hours = next_hours(self.total)
        records.append((*next(hours), hours))
        numbers = fun_numbers(self.total)
        records.append((*next(numbers), numbers))
        lifetimes = fun_numbers(self.total, lifetime=True)
        records.append((*next(lifetimes), lifetimes))

        while True:
            records.sort()
            value, sentinel, generator = records.pop(0)
            records.append((*next(generator), generator))
            yield value, sentinel


def next_hours(total: Dollar) -> Iterator[tuple[Record, bool]]:
    hour = dollars_to_hours(total) + 1
    while True:
        if hour % 24 == 0:
            yield (
                VirtualRecord(hours_to_dollars(hour), f"hour {hour} ({hour // 24} days!)"),
                True,
            )
        else:
            yield VirtualRecord(hours_to_dollars(hour), f"hour {hour}"), True
        hour += 1


def fun_numbers(total: Dollar, *, lifetime: bool = False) -> Iterator[tuple[Record, bool]]:
    zeroes = 0
    while True:
        for fives in range(2, 20):
            current = Dollar(fives * 5 * 10**zeroes)
            if lifetime:
                if total + LIFETIME < current:
                    yield VirtualRecord(current - LIFETIME, f"{current} lifetime"), True
            elif total < current:
                yield VirtualRecord(current, str(current)), True
        zeroes += 1


def _even_banner(items: list[str], width: int = 80, fill_char: str = " ") -> list[str]:
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
