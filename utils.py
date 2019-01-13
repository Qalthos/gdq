from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup
import pytz
import requests


NOW = datetime.now(pytz.utc)


@dataclass
class Run:
    game: str
    platform: str
    runtype: str
    runner: str

    start: datetime
    str_estimate: str

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
    def raw_estimate(self):
        hours, minutes = self.str_estimate.split(':')
        estimate = timedelta(hours=int(hours), minutes=int(minutes))
        if self.start < NOW:
            estimate = self.start + estimate - NOW
        return estimate

    @property
    def estimate(self):
        hours, minutes = divmod(self.raw_estimate.seconds, 3600)
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
        return max(*(option.numeric_total / self.current for option in self.options if option.numeric_total > 0)) * 100

    def __len__(self):
        return max(*(len(option.name) for option in self.options))


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


def read_incentives(incentive_url, stream=1):
    source = requests.get(incentive_url.format(stream_index=stream)).text
    soup = BeautifulSoup(source, 'html.parser')

    incentives = {}

    money = re.compile('[$,\n]')
    for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
        game = bid.contents[3].string.strip()

        short_desc = bid.contents[1].a.string.strip()
        description = bid.contents[7].string.strip()
        current = float(money.sub('', bid.contents[9].string))
        try:
            total = float(money.sub('', bid.contents[11].string))
            incentive = DonationIncentive(
                description=description, short_desc=short_desc,
                current=current, numeric_total=total,
            )
        except ValueError:
            # Assume bid war
            try:
                option_list = bid.find_next_sibling('tr').find('tbody').find_all('tr')
            except AttributeError:
                # bid war with no options (e.g. filename with no bids yet)
                pass
            else:
                options = [
                    Choice(
                        name=option.contents[1].a.string.strip(),
                        description=option.contents[7].string.strip(),
                        numeric_total=float(money.sub('', option.contents[9].string)),
                    )
                    for option in option_list
                ]

            incentive = ChoiceIncentive(
                description=description, short_desc=short_desc,
                current=current, options=options,
            )

        incentives.setdefault(game, []).append(incentive)

    return incentives


def short_number(number):
    if number > 1e6:
        return '{0:.1f}M'.format(number / 1e6)
    if number > 100e3:
        return '{0:.0f}k'.format(number / 1e3)
    if number > 10e3:
        return '{0:.1f}k'.format(number / 1e3)
    return f'{number:,.0f}'
