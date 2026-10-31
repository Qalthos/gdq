# Copyright 2023
# SPDX-License-Identifier: MIT
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Protocol, Self

from bus.db_api import (
    TIME_F,
    Auction,
    AuctionStatus,
    Prize,
    PrizeState,
    PrizeType,
    _money_from_message,
    get_history,
    get_lifetime,
    get_prizes,
    is_omega,
)
from bus.shifts import OMEGA, SHIFTS, BaseShift, Omega, Shift
from bus.utils import dollars_to_hours, hours_to_dollars
from common.display import SquishableString, String
from common.money import Dollar
from common.time import timedelta_as_hours

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    from bus.types import AuctionMessage, PrizeMessage, TotalMessage
    from common.money import Money


RECORDS = get_history()
LIFETIME = get_lifetime()


class Record(Protocol):
    total: Money
    name: str


def record_key(record: Record) -> Money:
    return record.total


@dataclass
class VirtualRecord:
    total: Money
    name: str


class DesertBuck(Dollar):
    _symbol = "d฿"

    @classmethod
    def convert(cls, value: Money) -> Self:
        if isinstance(value, Dollar):
            return cls(value / RECORDS[0].total)
        err = f"Conversion not defined on {type(value)}"
        raise ValueError(err)


class DesertToonie(Dollar):
    _symbol = "d฿²"

    @classmethod
    def convert(cls, value: Money) -> Self:
        if isinstance(value, Dollar):
            return cls(value / RECORDS[1].total)
        err = f"Conversion not defined on {type(value)}"
        raise ValueError(err)


class DesertBus:
    start: datetime
    total: Money
    offline: bool = False

    _event_id: str
    _auction: Auction | None = None
    _prizes: dict[str, Prize]

    def __init__(self, event: str, start: datetime, total: Money):
        self._event_id = event
        self._prizes = {p.id: p for p in get_prizes(event)}
        self.start = start
        self.total = total

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
    def end(self) -> datetime:
        return self.start + timedelta(hours=self.hours)

    # State modifiers
    def update_auction(self, message: AuctionMessage) -> None:
        self._auction = Auction.from_json(message)

    def update_prize(self, message: PrizeMessage) -> None:
        prize = Prize.from_json(message)
        self._prizes[prize.id] = prize

    def update_total(self, message: TotalMessage) -> None:
        self.total = _money_from_message(message)

    # Render functions
    def header(self, *, extended: bool = True) -> list[String]:
        lines: list[String] = []

        now = datetime.now(UTC).replace(microsecond=0)
        if now < self.start:
            lines.append(SquishableString(f"Starting in {self.start - now}", str.center))
        elif now < (self.start + timedelta(hours=self.hours + 1)):
            lines.append(self.shift_banners())
        else:
            lines.append(SquishableString("It's over!", str.center))

        lines.append(
            SquishableString(
                [
                    str(self.total),
                    f"{self.hours} hours",
                    str(DesertBuck.convert(self.total)),
                    str(DesertToonie.convert(self.total)),
                ],
                even_banner,
            ),
        )
        if extended:
            datetime_f = f"%m-%d {TIME_F}"
            totals = []
            totals.append(f"{self.total + LIFETIME} lifetime")
            current_end = (self.start + timedelta(hours=self.hours)).astimezone()
            current = f"running until {current_end.strftime(datetime_f)}"
            totals.append(current)
            lines.append(SquishableString(totals, even_banner))

            if now > self.start:
                totals = []
                estimate = self.estimate
                estimate_h = dollars_to_hours(estimate.total)
                totals.append(f"{estimate.total} estimated ({estimate_h}h)")
                current_end = (self.start + timedelta(hours=estimate_h)).astimezone()
                current = f"estimate end {current_end.strftime(datetime_f)}"
                totals.append(current)
                lines.append(SquishableString(totals, even_banner))

        lines.extend(self.show_live_prizes(PrizeType.GIVEAWAY))

        return lines

    def render(self) -> Iterable[str]:
        yield from self.show_auction()
        yield from self.show_live_prizes(PrizeType.SILENT)
        yield from self.show_upcoming_prizes()
        now = datetime.now(UTC)
        if now < self.start + (timedelta(hours=(self.hours + 1))):
            yield from self.print_records()

    def footer(self, *, overall: bool = True) -> tuple[SquishableString]:
        return (SquishableString(overall, self._bus_progress),)

    def _bus_progress(self, overall: bool, width: int) -> str:  # noqa: FBT001
        now = datetime.now(UTC)
        total = timedelta(hours=self.hours)
        elapsed = max(min(now - self.start, total), timedelta())
        remaining = total - elapsed

        hours_done = f"[{timedelta_as_hours(elapsed)}]"
        hours_left = f"[{timedelta_as_hours(remaining)}]"
        progress_width = width - len(hours_done) - len(hours_left)
        # Offset to account for some wide characters
        progress_width -= 3

        # Scaled to last passed record
        last_record = timedelta()
        future_stops = []

        for record in sorted(RECORDS, key=record_key):
            td_record = timedelta(hours=dollars_to_hours(record.total))
            if td_record <= elapsed:
                # We've passed this record, but make a note that we've come this far.
                if not overall:
                    last_record = td_record
            elif td_record < total:
                # In the future, but still on the hook for it.
                future_stops.append(td_record)
            else:
                # Don't worry about records we haven't reached yet.
                break

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

        return f"{hours_done}{progress}{hours_left}"

    def shift_banners(self) -> SquishableString[list[Shift] | list[Omega]]:
        shifts = OMEGA if is_omega() else SHIFTS

        return SquishableString(shifts, partial(even_shift_banner, fill_char="═"))

    def show_auction(self) -> Iterable[str]:
        if self._auction is not None:
            prize = self._prizes[self._auction.prize_id]
            yield str(prize)
            bid = self._auction.high_bid
            exclamations = list(AuctionStatus).index(self._auction.status)
            if exclamations > 0:
                yield f"{self._auction.status}{'!' * exclamations}"
            if bid is not None and bid.message:
                yield f"{bid.name} says {bid.message}"

            if self._auction.status == AuctionStatus.SOLD and self._auction.updated_at + timedelta(
                seconds=30,
            ) < datetime.now(UTC):
                self._auction = None

    def show_live_prizes(self, prize_type: PrizeType) -> Iterable[str]:
        for prize in sorted(self._prizes.values(), key=lambda p: p.starts_at):
            if prize.state == PrizeState.ACTIVE and prize.type == prize_type:
                yield prize

    def show_upcoming_prizes(self) -> Iterable[str]:
        for prize in sorted(self._prizes.values(), key=lambda p: p.starts_at):
            if prize.upcoming:
                yield prize

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
                        break
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
                True,
                iter(lambda: (VirtualRecord(Dollar(sys.maxsize), ""), True), 0),
            ),
        ]

        hours = next_hours(self.total)
        records.append((*next(hours), hours))
        numbers = fun_numbers(self.total)
        records.append((*next(numbers), numbers))
        lifetimes = lifetime(self.total)
        records.append((*next(lifetimes), lifetimes))

        while True:
            records.sort(key=lambda r: r[0].total)
            value, sentinel, generator = records.pop(0)
            records.append((*next(generator), generator))
            yield value, sentinel


def next_hours(total: Money) -> Iterator[tuple[Record, bool]]:
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


def fun_numbers(total: Money) -> Iterator[tuple[Record, bool]]:
    zeroes = 0
    while True:
        for fives in range(2, 20):
            current = Dollar(fives * 5 * 10**zeroes)
            if total < current:
                yield VirtualRecord(current, str(current)), True
        zeroes += 1


def lifetime(total: Money) -> Iterator[tuple[Record, bool]]:
    millions = 1
    while True:
        current = Dollar(millions * 1_000_000)
        if total + LIFETIME < current:
            yield VirtualRecord(current - LIFETIME, f"{current} lifetime"), True
        millions += 1


def _bannerize(items: Sequence, width: int) -> tuple[int, int]:
    # Adjust for dividers
    width -= len(items) - 1
    # Need extra characters for spacers
    min_width = sum(len(s) for s in items)
    # Minimum for even spacing
    min_even = max(len(s) for s in items) * len(items)
    # reflow is extra spaces that should be distributed amongst the
    # groups in the banner.
    reflow = 0
    if width <= min_even:
        shift_width = 0
        if width > min_width:
            # reflow is negative, width will be compressed if possible
            reflow = min_width - width
    else:
        shift_width = width // len(items)
        # reflow is positive, an extra space will be added
        reflow = width - (shift_width * len(items))
    return shift_width, reflow


def even_banner(items: list[str], width: int, fill_char: str = " ") -> str:
    item_w, reflow = _bannerize(items, width)

    display = []
    for index, stat in enumerate(items):
        mod = 0
        if reflow < 0 and index == len(items) - 1:
            mod = len(items) - reflow
        elif index < reflow:
            mod = 1
        display.append(stat.center(item_w + mod, fill_char))

    return "|".join(display)


def even_shift_banner(items: Sequence[BaseShift], width: int, fill_char: str = " ") -> str:
    shift_width, reflow = _bannerize(items, width)

    display = []
    for index, stat in enumerate(items):
        mod = 0
        if reflow < 0 and index == len(items) - 1:
            mod = len(items) - reflow
        elif index < reflow:
            mod = 1
        display.append(stat.colorize(str(stat).center(shift_width + mod, fill_char)))

    return "|".join(display)
