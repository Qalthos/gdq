from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup
from dateutil import tz
import requests


NOW: datetime = datetime.now(tz.UTC)


@dataclass
class Run:
    game: str
    platform: str
    category: str
    runner: str

    start: datetime
    estimate: int

    @property
    def delta(self):
        if self.start < NOW:
            return '  NOW  '
        delta = self.start - NOW
        if delta.days >= 10:
            return f'{delta.days} DAYS'
        hours, minutes = divmod(delta.seconds // 60, 60)
        return f'{delta.days}:{hours:02d}:{minutes:02d}'

    @property
    def remaining(self):
        remaining = timedelta(seconds=self.estimate)
        if self.start < NOW:
            remaining -= NOW - self.start
        return remaining

    @property
    def str_estimate(self):
        hours, minutes = divmod(self.remaining.seconds, 3600)
        minutes //= 60
        return f'+{hours}:{minutes:02d}'

    @property
    def game_desc(self):
        if self.platform:
            return f'{self.game} ({self.platform})'
        return self.game


@dataclass
class ChoiceIncentive:
    description: str
    short_desc: str
    current: float
    options: list

    @property
    def max_percent(self):
        nonzero_options = (option.numeric_total / self.current for option in self.options if option.numeric_total > 0)
        return max((0, *nonzero_options)) * 100

    def __len__(self):
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
    def total(self):
        return short_number(self.numeric_total)


@dataclass
class DonationIncentive:
    description: str
    short_desc: str
    current: float
    numeric_total: float

    @property
    def percent(self):
        return self.current / self.numeric_total * 100

    @property
    def total(self):
        return short_number(self.numeric_total)

    def __len__(self):
        return len(self.short_desc)


def short_number(number):
    if number > 1e6:
        return '{0:.2f}M'.format(number / 1e6)
    if number > 100e3:
        return '{0:.0f}k'.format(number / 1e3)
    if number > 10e3:
        return '{0:.1f}k'.format(number / 1e3)
    return f'{number:,.0f}'
