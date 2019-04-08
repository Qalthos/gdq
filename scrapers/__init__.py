from abc import ABC, abstractmethod
from datetime import datetime
import re
import shelve

from bs4 import BeautifulSoup
import requests

from utils import ChoiceIncentive, Choice, DonationIncentive


class MarathonBase(ABC):
    money = re.compile('[$,\n]')
    index_url = ''
    incentive_url = ''
    event_id = ''
    stream_ids = []

    def __init__(self):
        self.session = requests.Session()

    def read_total(self, streams):
        donation_re = re.compile(fr'Donation Total:\s+\$([\d,]+.[0-9]+)')

        total = 0
        for stream in streams:
            full_url = self.index_url.format(stream_index=stream)
            source = self.session.get(full_url).text
            soup = BeautifulSoup(source, 'html.parser')

            donation_info = donation_re.search(soup.find(string=donation_re))
            total += float(donation_info.group(1).replace(',', ''))

        return total

    def read_incentives(self, stream=1):
        """Scrapes GDQ-derrived donation trackers for incentives."""
        source = self.session.get(self.incentive_url.format(stream_index=stream)).text
        soup = BeautifulSoup(source, 'html.parser')

        incentives = {}

        for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
            game = bid.contents[3].string.strip()

            short_desc = bid.contents[1].a.string.strip()
            description = bid.contents[7].string.strip()
            current = float(self.money.sub('', bid.contents[9].string))
            try:
                total = float(self.money.sub('', bid.contents[11].string))
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
                    option_list = []

                options = [
                    Choice(
                        name=option.contents[1].a.string.strip(),
                        description=option.contents[7].string.strip(),
                        numeric_total=float(self.money.sub('', option.contents[9].string)),
                    )
                    for option in option_list
                ]

                incentive = ChoiceIncentive(
                    description=description, short_desc=short_desc,
                    current=current, options=options,
                )

            incentives.setdefault(game, []).append(incentive)

        return incentives

    def read_schedules(self):
        return [self._read_schedule(self.event_id, stream_id) for stream_id in self.stream_ids]

    def _read_schedule(self, event, stream_id):
        shelve_file = f'.{event}-{stream_id}.db'
        with shelve.open(shelve_file) as shelf:
            last_check = shelf.get('updated')
            runs = shelf.get('runs', [])

        headers = {}
        if last_check:
            headers['If-Modified-Since'] = datetime.strftime(last_check, '%a, %d %b %Y %H:%M:%S GMT')
        data = self.session.get(f'https://horaro.org/-/api/v1/events/{event}/schedules/{stream_id}', headers=headers)

        try:
            data = data.json()['data']
        except ValueError:
            return runs

        updated = datetime.strptime(data['updated'], '%Y-%m-%dT%H:%M:%S%z')
        timezone = data['timezone']
        keys = data['columns']
        schedule = data['items']

        runs = list(self.parse_data(keys, schedule, timezone))
        with shelve.open(shelve_file) as shelf:
            shelf['updated'] = updated
            shelf['runs'] = runs

        return runs

    @classmethod
    @abstractmethod
    def parse_data(cls, keys, schedule, timezone='UTC'):
        """Parses data from horaro.org using event-specific keys."""

    @staticmethod
    def strip_md(string):
        links = re.compile(r'(?:\[(?P<name>[^]]*)]\([^\)]+\))')
        return links.sub(r'\g<name>', string)


class MarathonBaseEuro(MarathonBase):
    money = re.compile('[€.\n]')

    def read_total(self, streams):
        donation_re = re.compile(fr'Donation Total:\s+€ ([\d,]+,[0-9]+)')

        source = self.session.get(self.index_url).text
        soup = BeautifulSoup(source, 'html.parser')

        donation_info = donation_re.search(soup.find(string=donation_re))
        total = float(donation_info.group(1).replace('.', '').replace(',', '.'))

        return total

    def read_incentives(self, stream=1):
        """Scrapes GDQ-derrived donation trackers for incentives."""
        source = self.session.get(self.incentive_url.format(stream_index=stream)).text
        soup = BeautifulSoup(source, 'html.parser')

        incentives = {}

        for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
            try:
                game = bid.contents[3].string.strip()
            except IndexError:
                continue

            short_desc = bid.contents[1].a.string.strip()
            description = bid.contents[5].string.strip()
            current = float(self.money.sub('', bid.contents[7].string).replace(',', '.'))
            try:
                total = float(self.money.sub('', bid.contents[9].string).replace(',', '.'))
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
                    option_list = []

                options = [
                    Choice(
                        name=option.contents[1].a.string.strip(),
                        description=option.contents[7].string.strip(),
                        numeric_total=float(self.money.sub('', option.contents[9].string).replace(',', '.')),
                    )
                    for option in option_list
                ]

                incentive = ChoiceIncentive(
                    description=description, short_desc=short_desc,
                    current=current, options=options,
                )

            incentives.setdefault(game, []).append(incentive)

        return incentives

    @classmethod
    @abstractmethod
    def parse_data(cls, keys, schedule, timezone='UTC'):
        """Parses data from horaro.org using event-specific keys."""
