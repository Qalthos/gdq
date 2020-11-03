import argparse
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter
from textwrap import wrap
from typing import Union

from gdq import money, utils


@dataclass
class Event(ABC):
    name: str
    short_name: str
    _offset: money.Money

    @property
    @abstractmethod
    def start_time(self) -> datetime:
        raise NotImplementedError

    @property
    @abstractmethod
    def total(self) -> money.Money:
        raise NotImplementedError

    @property
    @abstractmethod
    def charity(self) -> str:
        raise NotImplementedError

    @property
    def currency(self) -> type[money.Money]:
        return type(self.total)

    @property
    def offset(self) -> money.Money:
        return self._offset

    @offset.setter
    def offset(self, offset: float) -> None:
        self._offset = self.currency(offset)


@dataclass
class Incentive(ABC):
    incentive_id: int
    description: str
    short_desc: str
    current: money.Money
    state: str

    @property
    def closed(self) -> bool:
        return self.state == "CLOSED"

    @property
    def currency(self) -> type[money.Money]:
        return type(self.current)

    @abstractmethod
    def render(self, width: int, align: int, args: argparse.Namespace) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError


@dataclass
class SingleEvent(Event):
    event_id: int
    target: money.Money
    _start_time: datetime
    _total: money.Money
    _charity: str

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def total(self) -> money.Money:
        return self._total - self._offset

    @property
    def charity(self) -> str:
        return self._charity


@dataclass
class MultiEvent(Event):
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
    def charity(self) -> str:
        return self.subevents[0].charity


@dataclass
class Runner:
    runner_id: int
    name: str
    pronouns: str = ""

    def __str__(self) -> str:
        if self.pronouns:
            return f"{self.name}({self.pronouns})"
        return self.name


@dataclass
class Run:
    game: str
    platform: str
    category: str
    runners: list[Union[Runner, str]]
    incentives: list[Incentive]

    start: datetime
    estimate: int

    run_id: int


    @property
    def runner_str(self) -> str:
        return ", ".join((str(runner) for runner in self.runners))

    @property
    def delta(self) -> str:
        if self.start < utils.now:
            return "  NOW  "
        delta = self.start - utils.now
        if delta.days >= 10:
            return f"{delta.days} DAYS"
        hours, minutes = divmod(delta.seconds // 60, 60)
        return f"{delta.days}:{hours:02d}:{minutes:02d}"

    @property
    def remaining(self) -> timedelta:
        remaining = timedelta(seconds=self.estimate)
        if self.start < utils.now:
            remaining -= utils.now - self.start
        return remaining

    @property
    def is_live(self) -> bool:
        return self.remaining > timedelta()

    @property
    def str_estimate(self) -> str:
        hours, minutes = divmod(self.remaining.seconds, 3600)
        minutes //= 60
        return f"+{hours}:{minutes:02d}"

    @property
    def game_desc(self) -> str:
        if self.platform:
            return f"{self.game.strip()} ({self.platform.strip()})"
        return self.game

    def render(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        # If the run is over, skip it
        if not self.is_live:
            return

        width -= 8
        if not any(self.runners):
            desc_width = max(len(self.game_desc), len(self.category))
            if desc_width > width:
                # If display too long, tself.ate run
                self.game = self.game[:width - 1] + "…"
                self.category = self.category[:width - 1] + "…"

            yield "{0}┼{1}┤".format("─" * 7, "─" * (width - 1))
            yield f"{self.delta}│{self.game_desc:<{width - 1}s}│"
            yield f"{self.str_estimate: >7s}│{self.category:<{width - 1}}│"

        else:
            desc_width = max(width - 2 - len(self.runner_str), len(self.game_desc), len(self.category))

            runner = "│" + self.runner_str + "│"
            if desc_width + len(runner) > width:
                # Tself.ate runner display if too long
                runner_width = width - 3 - desc_width
                runner = "│" + self.runner_str[:runner_width] + "…│"

            if desc_width + len(runner) > width:
                # If display still too long, tself.ate run
                overrun = desc_width + len(runner) - width
                desc_width -= overrun
                self.game = self.game[: -(overrun + 1)] + "…"

            border = "─" * (len(runner) - 2)
            yield f"───────┼{'─' * desc_width}┬{border}┤"
            yield f"{self.delta}│{self.game_desc:<{desc_width}s}{runner}"
            yield f"{self.str_estimate: >7s}│{self.category:<{desc_width}}└{border}┤"

        # Handle incentives
        if self.incentives and not args.hide_incentives:
            align_width = max(args.min_width, *(len(incentive) for incentive in self.incentives))
            for incentive in self.incentives:
                yield from incentive.render(width, align_width, args)


@dataclass
class ChoiceIncentive(Incentive):
    options: list["Choice"]

    @property
    def max_option(self) -> money.Money:
        return max((option.total for option in self.options))

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
                incentive.append(f"       ├┬{self.short_desc:<{desc_size}s}  {lines[0]: <{rest_size}s}│")
                for line in lines[1:]:
                    incentive.append(f"       ││{'':<{desc_size}s}  {line: <{rest_size}s}│")
            else:
                incentive.append(f"       ├┬{self.short_desc:<{desc_size}s}  {'': <{rest_size}s}│")

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
                    prog_bar = utils.progress_bar(0, total.to_float(), self.max_option.to_float(), width - align - 7)
                    incentive.append(f"       │╵ {description:<{align}s}▕{prog_bar}▏{total.short: >6s}│")
                    break

                prog_bar = utils.progress_bar(0, option.total.to_float(), self.max_option.to_float(), width - align - 7)

                leg = "├│"
                if index == len(self.options) - 1:
                    leg = "└ "

                incentive.append(f"       │{leg[0]}▶{option.name:<{align}s}▕{prog_bar}▏{option.total.short: >6s}│")
                if option.description and option.description != option.name:
                    lines = wrap(option.description, width - 1)
                    incentive.append(f"       │{leg[1]} └▶{lines[0].ljust(width - 1)}│")
                    for line in lines[1:]:
                        incentive.append(f"       │{leg[1]}   {line.ljust(width - 1)}│")

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
            incentive_bar = money.progress_bar_money(self.currency(), self.current, self.total, width - align)
            if lines:
                incentive.append(f"       ├┬{lines[0].ljust(width + 1)}│")
                for line in lines[1:]:
                    incentive.append(f"       ││{line.ljust(width + 1)}│")

                incentive.append(f"       │└▶{self.short_desc:<{align}s}{incentive_bar}│")
            else:
                incentive.append(f"       ├─▶{self.short_desc:<{align}s}{incentive_bar}│")

        return incentive
