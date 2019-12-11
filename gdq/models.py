from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime, timedelta
from operator import attrgetter
from textwrap import wrap
from typing import Iterator, List

from gdq import utils


PREFIX = " " * 7


@dataclass
class Event(metaclass=ABCMeta):
    name: str
    short_name: str


@dataclass
class SingleEvent(Event):
    event_id: int
    target: float
    total: float


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
class Run:
    game: str
    platform: str
    category: str
    runner: str

    start: datetime
    estimate: int

    run_id: int = None

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
    description: str
    short_desc: str
    current: float


@dataclass
class ChoiceIncentive(Incentive):
    options: list

    @property
    def max_percent(self) -> float:
        nonzero_options = (
            option.numeric_total / self.current
            for option in self.options
            if option.numeric_total > 0
        )
        return max((0, *nonzero_options)) * 100

    def __len__(self) -> int:
        if self.options:
            if len(self.options) == 1:
                return len(self.options[0].name)
            return max(*(len(option.name) for option in self.options))
        return 0

    def render(self, width: int, align: int, args) -> Iterator[str]:
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

        max_percent = self.max_percent
        sorted_options = sorted(self.options, key=attrgetter("numeric_total"), reverse=True)
        for index, option in enumerate(sorted_options):
            try:
                percent = option.numeric_total / self.current * 100
            except ZeroDivisionError:
                percent = 0

            if percent < args.min_percent and index >= args.min_options and index != len(self.options) - 1:
                remaining = sorted_options[index:]
                total = sum(option.numeric_total for option in remaining)
                try:
                    percent = total / self.current * 100
                except ZeroDivisionError:
                    percent = 0
                description = "And {} more".format(len(remaining))
                incentive_bar = utils.show_progress(percent, width - align - 7, max_percent)
                line_one = "{0}│╵ {1:<" + str(align) + "s}▕{2}▏{3: >6s}│"
                yield line_one.format(PREFIX, description, incentive_bar, utils.short_number(total))
                break

            incentive_bar = utils.show_progress(percent, width - align - 7, max_percent)

            leg = "├│"
            if index == len(self.options) - 1:
                leg = "└ "

            line_one = "{0}│{1}▶{2:<" + str(align) + "s}▕{3}▏{4: >6s}│"
            yield line_one.format(PREFIX, leg[0], option.name, incentive_bar, option.total)
            if option.description:
                lines = wrap(option.description, width)
                yield f"{PREFIX}│{leg[1]} └▶{lines[0].ljust(width - 1)}│"
                for line in lines[1:]:
                    yield f"{PREFIX}│{leg[1]}   {line.ljust(width - 1)}│"


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

    def render(self, width: int, align: int) -> Iterator[str]:
        # Remove fixed elements
        width -= 4

        lines = wrap(self.description, width + 1)
        incentive_bar = utils.show_progress(self.percent, width - align - 7)
        if lines:
            yield f"{PREFIX}├┬{lines[0].ljust(width + 2)}│"
            for line in lines[1:]:
                yield f"{PREFIX}││{line.ljust(width + 2)}│"

            progress = "{0}│└▶{1:<" + str(align) + "s}▕{2}▏{3: >6s}│"
        else:
            progress = "{0}├─▶{1:<" + str(align) + "s}▕{2}▏{3: >6s}│"

        yield progress.format(PREFIX, self.short_desc, incentive_bar, self.total)
