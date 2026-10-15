# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from operator import attrgetter
from textwrap import wrap
from typing import TYPE_CHECKING, Literal

from common.progress_bar import progress_bar_money
from gdq import utils
from gdq.models import Event as BaseEvent
from gdq.models import Incentive

if TYPE_CHECKING:
    import argparse
    from datetime import datetime

    from common.money import Money


@dataclass
class Event(BaseEvent):
    type: Literal["event"]
    id: int
    short: str
    start_time: datetime
    total: Money


@dataclass
class ChoiceIncentive(Incentive):
    options: list[Choice]

    @property
    def max_option(self) -> Money:
        return max(option.current for option in self.options)

    def __len__(self) -> int:
        if self.options:
            if len(self.options) == 1:
                return len(self.options[0].short_desc)
            return max(*(len(option.short_desc) for option in self.options))
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
                    percent = option.current / self.current * 100
                except ZeroDivisionError:
                    percent = 0

                if percent < args.min_percent and index >= args.min_options and index != len(self.options) - 1:
                    remaining = sorted_options[index:]
                    option_totals = [option.current for option in remaining]
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
                    option.current.to_float(),
                    self.max_option.to_float(),
                    width - align - 7,
                )

                leg = "├│"
                if index == len(self.options) - 1:
                    leg = "└ "

                incentive.append(
                    f"       │{leg[0]}▶{option.short_desc:<{align}s}▕{prog_bar}▏{option.current.short: >6s}│",
                )
                if option.description and option.description != option.short_desc:
                    lines = wrap(option.description, width - 1)
                    incentive.append(f"       │{leg[1]} └▶{lines[0].ljust(width - 1)}│")
                    incentive.extend(f"       │{leg[1]}   {line.ljust(width - 1)}│" for line in lines[1:])

                if self.closed:
                    break

        return incentive


@dataclass(order=True)
class Choice:
    incentive_id: int
    description: str
    short_desc: str
    current: Money


@dataclass
class DonationIncentive(Incentive):
    total: Money

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
