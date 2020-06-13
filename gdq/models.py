from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter
from textwrap import wrap
from typing import List, Union

from gdq import money, utils


@dataclass
class Event(ABC):
    name: str
    short_name: str

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
    def charity(self):
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
        return self._total

    @property
    def charity(self):
        return self._charity


@dataclass
class MultiEvent(Event):
    subevents: List[SingleEvent]

    @property
    def start_time(self) -> datetime:
        return min(event.start_time for event in self.subevents)

    @property
    def target(self) -> money.Money:
        targets = [event.target for event in self.subevents if event.target]
        return sum(targets, type(targets[0])(0))

    @property
    def total(self) -> money.Money:
        totals = [event.total for event in self.subevents]
        return sum(totals, type(totals[0])(0))

    @property
    def charity(self):
        return self.subevents[0].charity


@dataclass
class Runner:
    runner_id: int
    name: str
    pronouns: str = ""

    def __str__(self):
        if self.pronouns:
            return f"{self.name}({self.pronouns})"
        return self.name


@dataclass
class Run:
    game: str
    platform: str
    category: str
    runners: List[Union[Runner, str]]

    start: datetime
    estimate: int

    run_id: int

    @property
    def runner_str(self):
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
        return self.remaining > timedelta(0)

    @property
    def str_estimate(self) -> str:
        hours, minutes = divmod(self.remaining.seconds, 3600)
        minutes //= 60
        return f"+{hours}:{minutes:02d}"

    @property
    def game_desc(self) -> str:
        if self.platform:
            return f"{self.game} ({self.platform})"
        return self.game


@dataclass
class Incentive(ABC):
    incentive_id: int
    description: str
    short_desc: str
    current: money.Money
    state: str

    @property
    def closed(self):
        return self.state == "CLOSED"

    @abstractmethod
    def render(self, width: int, align: int, args) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError


@dataclass
class ChoiceIncentive(Incentive):
    options: list

    @property
    def max_option(self) -> money.Money:
        return max((option.total for option in self.options))

    def __len__(self) -> int:
        if self.options:
            if len(self.options) == 1:
                return len(self.options[0].name)
            return max(*(len(option.name) for option in self.options))
        return 0

    def render(self, width: int, align: int, args) -> List[str]:
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
                    total = sum(option_totals, type(option_totals[0])(0))
                    description = f"And {len(remaining)} more"
                    prog_bar = utils.progress_bar(0, total.to_float(), self.max_option.to_float(), width - align - 6)
                    incentive.append(f"       │╵ {description:<{align}s}▕{prog_bar}▏{total.short: >6s}│")
                    break

                prog_bar = utils.progress_bar(0, option.total.to_float(), self.max_option.to_float(), width - align - 6)

                leg = "├│"
                if index == len(self.options) - 1:
                    leg = "└ "

                incentive.append(f"       │{leg[0]}▶{option.name:<{align}s}▕{prog_bar}▏{option.total.short: >5s}│")
                if option.description:
                    lines = wrap(option.description, width)
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

    @property
    def percent(self) -> float:
        return self.current / self.total * 100

    def __len__(self) -> int:
        return len(self.short_desc)

    def render(self, width: int, align: int, args) -> List[str]:
        incentive = []

        # Skip incentive if applicable
        if not (args.hide_completed and self.closed):
            # Remove fixed elements
            width -= 3

            lines = wrap(self.description, width)
            incentive_bar = money.progress_bar_money(type(self.total)(0), self.current, self.total, width - align)
            if lines:
                incentive.append(f"       ├┬{lines[0].ljust(width + 1)}│")
                for line in lines[1:]:
                    incentive.append(f"       ││{line.ljust(width + 1)}│")

                incentive.append(f"       │└▶{self.short_desc:<{align}s}{incentive_bar}│")
            else:
                incentive.append(f"       ├─▶{self.short_desc:<{align}s}{incentive_bar}│")

        return incentive
