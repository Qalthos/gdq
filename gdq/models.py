from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from gdq import utils


@dataclass
class Event(metaclass=ABCMeta):
    name: str
    short_name: str

    @property
    @abstractmethod
    def target(self) -> float:
        pass

    @property
    @abstractmethod
    def total(self) -> float:
        pass


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
