# Copyright 2019
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from operator import attrgetter
from textwrap import wrap
from typing import TYPE_CHECKING

from common.progress_bar import progress_bar_money
from gdq import utils
from gdq.models import Event as BaseEvent
from gdq.models import Incentive

if TYPE_CHECKING:
    import argparse
    from datetime import datetime

    from common import money


@dataclass
class Event(BaseEvent):
    _offset: money.Money

    @property
    def offset(self) -> money.Money:
        return self._offset

    def update_offset(self, offset: float) -> None:
        self._offset = self.currency(offset)


@dataclass
class SingleEvent(Event):
    id: int
    target: money.Money


@dataclass
class MultiEvent(Event):
    id: int
    subevents: list[SingleEvent]

    @property
    def start_time(self) -> datetime:
        return min(event.start_time for event in self.subevents)

    @property
    def target(self) -> money.Money:
        targets = [event.target for event in self.subevents if event.target]
        return sum(targets, self.currency())

    @property
    def total(self) -> money.Money:
        totals = [event.total for event in self.subevents]
        return sum(totals, -self._offset)

    @property
    def receiver(self) -> str:
        return self.subevents[0].receiver


@dataclass
class ChoiceIncentive(Incentive):
    options: list[Choice]

    @property
    def max_option(self) -> money.Money:
        return max(option.total for option in self.options)

    def __len__(self) -> int:
        if self.options:
            if len(self.options) == 1:
                return len(self.options[0].name)
            return max(*(len(option.name) for option in self.options))
        return 0

    def render(self, width: int, align: int, args: argparse.Namespace) -> list[str]:
        incentive = []

        # Skip incentive if applicable
        if not (args.hide_completed and self.closed):
            # Remove fixed elements
            width -= 4

            desc_size = max(align, len(self.short_desc))
            rest_size = width - desc_size
            lines = wrap(self.description, rest_size - 1)
            if lines:
                incentive.append(
                    f"       ├┬{self.short_desc:<{desc_size}s}  {lines[0]: <{rest_size}s}│",
                )
                incentive.extend(f"       ││{'':<{desc_size}s}  {line: <{rest_size}s}│" for line in lines[1:])
            else:
                incentive.append(
                    f"       ├┬{self.short_desc:<{desc_size}s}  {'': <{rest_size}s}│",
                )

            sorted_options = sorted(self.options, key=attrgetter("total"), reverse=True)
            for index, option in enumerate(sorted_options):
                try:
                    percent = option.total / self.current * 100
                except ZeroDivisionError:
                    percent = 0

                if percent < args.min_percent and index >= args.min_options and index != len(self.options) - 1:
                    remaining = sorted_options[index:]
                    option_totals = [option.total for option in remaining]
                    total = sum(option_totals, self.currency())
                    description = f"And {len(remaining)} more"
                    prog_bar = utils.progress_bar(
                        0,
                        total.to_float(),
                        self.max_option.to_float(),
                        width - align - 7,
                    )
                    incentive.append(
                        f"       │╵ {description:<{align}s}▕{prog_bar}▏{total.short: >6s}│",
                    )
                    break

                prog_bar = utils.progress_bar(
                    0,
                    option.total.to_float(),
                    self.max_option.to_float(),
                    width - align - 7,
                )

                leg = "├│"
                if index == len(self.options) - 1:
                    leg = "└ "

                incentive.append(
                    f"       │{leg[0]}▶{option.name:<{align}s}▕{prog_bar}▏{option.total.short: >6s}│",
                )
                if option.description and option.description != option.name:
                    lines = wrap(option.description, width - 1)
                    incentive.append(f"       │{leg[1]} └▶{lines[0].ljust(width - 1)}│")
                    incentive.extend(f"       │{leg[1]}   {line.ljust(width - 1)}│" for line in lines[1:])

                if self.closed:
                    break

        return incentive


@dataclass(order=True)
class Choice:
    name: str
    description: str
    total: money.Money


@dataclass
class DonationIncentive(Incentive):
    total: money.Money

    def __len__(self) -> int:
        return len(self.short_desc)

    def render(self, width: int, align: int, args: argparse.Namespace) -> list[str]:
        incentive = []

        # Skip incentive if applicable
        if not (args.hide_completed and self.closed):
            # Remove fixed elements
            width -= 3

            lines = wrap(self.description, width)
            incentive_bar = progress_bar_money(
                self.currency(),
                self.current,
                self.total,
                width - align,
            )
            if lines:
                incentive.append(f"       ├┬{lines[0].ljust(width + 1)}│")
                incentive.extend(f"       ││{line.ljust(width + 1)}│" for line in lines[1:])
                incentive.append(
                    f"       │└▶{self.short_desc:<{align}s}{incentive_bar}│",
                )
            else:
                incentive.append(
                    f"       ├─▶{self.short_desc:<{align}s}{incentive_bar}│",
                )

        return incentive
