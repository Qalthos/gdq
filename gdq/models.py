from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter
from textwrap import wrap
from typing import Final, Iterator, List, Union

from gdq import utils


PREFIX: Final[str] = " " * 7


@dataclass
class Event(metaclass=ABCMeta):
    name: str
    short_name: str

    @property
    @abstractmethod
    def total(self) -> float:
        raise NotImplementedError


@dataclass
class SingleEvent(Event):
    event_id: int
    target: float
    _total: float

    @property
    def total(self) -> float:
        return self._total


@dataclass
class MultiEvent(Event):
    subevents: List[SingleEvent]

    @property
    def target(self) -> float:
        return sum((event.target for event in self.subevents if event.target))

    @property
    def total(self) -> float:
        return sum((event.total for event in self.subevents))


@dataclass
class Runner:
    runner_id: int
    name: str
    pronouns: str = ""

    def __str__(self):
        return f"{self.pronouns}{self.name}"


@dataclass
class Run:
    game: str
    platform: str
    category: str
    runners: List[Union[Runner, str]]

    start: datetime
    estimate: int

    run_id: int = None

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
class Incentive(metaclass=ABCMeta):
    incentive_id: int
    description: str
    short_desc: str
    current: float
    state: str

    @property
    def closed(self):
        return self.state == "CLOSED"


@dataclass
class ChoiceIncentive(Incentive):
    options: list

    @property
    def max_option(self) -> float:
        return max((option.numeric_total for option in self.options))

    def __len__(self) -> int:
        if self.options:
            if len(self.options) == 1:
                return len(self.options[0].name)
            return max(*(len(option.name) for option in self.options))
        return 0

    def render(self, width: int, align: int, args) -> Iterator[str]:
        # Skip incentive if applicable
        if args.hide_completed and self.closed:
            return

        # Remove fixed elements
        width -= 4

        desc_size = max(align, len(self.short_desc))
        rest_size = width - desc_size
        lines = wrap(self.description, rest_size - 1)
        description = "{0}├┬{1:<" + str(desc_size) + "s}  {2: <" + str(rest_size) + "s}│"
        if lines:
            yield description.format(PREFIX, self.short_desc, lines[0])
            for line in lines[1:]:
                description = (
                    "{0}││{0:<" + str(desc_size) + "s}  {1: <" + str(rest_size) + "s}│"
                )
                yield description.format(PREFIX, line)
        else:
            yield description.format(PREFIX, self.short_desc, "")

        sorted_options = sorted(self.options, key=attrgetter("numeric_total"), reverse=True)

        for index, option in enumerate(sorted_options):
            try:
                percent = option.numeric_total / self.current * 100
            except ZeroDivisionError:
                percent = 0

            if percent < args.min_percent and index >= args.min_options and index != len(self.options) - 1:
                remaining = sorted_options[index:]
                total = sum(option.numeric_total for option in remaining)
                description = "And {} more".format(len(remaining))
                incentive_bar = utils.progress_bar(0, total, self.max_option, width - align - 6)
                yield f"{PREFIX}│╵ {description:<{align}s}▕{incentive_bar}▏{option.total: >5s}│"
                break

            incentive_bar = utils.progress_bar(0, option.numeric_total, self.max_option, width - align - 6)

            leg = "├│"
            if index == len(self.options) - 1:
                leg = "└ "

            yield f"{PREFIX}│{leg[0]}▶{option.name:<{align}s}▕{incentive_bar}▏{option.total: >5s}│"
            if option.description:
                lines = wrap(option.description, width)
                yield f"{PREFIX}│{leg[1]} └▶{lines[0].ljust(width - 1)}│"
                for line in lines[1:]:
                    yield f"{PREFIX}│{leg[1]}   {line.ljust(width - 1)}│"

            if self.closed:
                break


@dataclass
class Choice:
    name: str
    description: str
    numeric_total: float

    @property
    def total(self) -> str:
        return utils.short_number(self.numeric_total)


@dataclass
class DonationIncentive(Incentive):
    numeric_total: float

    @property
    def percent(self) -> float:
        return self.current / self.numeric_total * 100

    @property
    def total(self) -> str:
        return utils.short_number(self.numeric_total)

    def __len__(self) -> int:
        return len(self.short_desc)

    def render(self, width: int, align: int, args) -> Iterator[str]:
        # Skip incentive if applicable
        if args.hide_completed and self.closed:
            return

        # Remove fixed elements
        width -= 4

        lines = wrap(self.description, width + 1)
        incentive_bar = utils.progress_bar_decorated(0, self.current, self.numeric_total, width - align)
        if lines:
            yield f"{PREFIX}├┬{lines[0].ljust(width + 2)}│"
            for line in lines[1:]:
                yield f"{PREFIX}││{line.ljust(width + 2)}│"

            yield f"{PREFIX}│└▶{self.short_desc:<{align}s}{incentive_bar}│"
        else:
            yield f"{PREFIX}├─▶{self.short_desc:<{align}s}{incentive_bar}│"
