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
        hours, minutes = divmod(delta.seconds // 60, 60)
        return f'{delta.days}:{hours:02d}:{minutes:02d}'

    @property
    def raw_estimate(self):
        hours, minutes, seconds = self.str_estimate.split(':')
        estimate = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
        if self.start < NOW:
            estimate = self.start + estimate - NOW
        return estimate

    @property
    def estimate(self):
        hours, minutes = divmod(self.raw_estimate.seconds, 3600)
        minutes = minutes // 60
        return f'+{hours}:{minutes:02d}'

    @property
    def game_desc(self):
        return f'{self.game} ({self.platform})'


def read_incentives(incentive_url):
    source = requests.get(incentive_url).text
    soup = BeautifulSoup(source, 'html.parser')

    incentives = {}

    money = re.compile('[$,\n]')
    for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
        game = bid.contents[3].string.strip()
        gamedata = dict(
            short_desc=bid.contents[1].a.string.strip(),
            description=bid.contents[7].string.strip(),
        )
        gamedata['current'] = float(money.sub('', bid.contents[9].string))
        try:
            gamedata['total'] = float(money.sub('', bid.contents[11].string))
        except ValueError:
            # Assume bid war
            try:
                option_list = bid.find_next_sibling('tr').find('tbody').find_all('tr')
            except AttributeError:
                # bid war with no options (e.g. filename with no bids yet)
                pass
            else:
                gamedata['options'] = [
                    dict(
                        choice=option.contents[1].a.string.strip(),
                        description=option.contents[7].string.strip(),
                        total=float(money.sub('', option.contents[9].string)),
                    )
                    for option in option_list
                ]

        incentives.setdefault(game, []).append(gamedata)

    return incentives
