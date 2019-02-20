from datetime import datetime

from bs4 import BeautifulSoup
import pytz

from scrapers import MarathonBase
from utils import Run

EVENT = 'esaw2019s'
URL = 'https://donations.esamarathon.com'
RECORDS = sorted([
    (22611.53, "ESA Winter 2018"),
    (62783.69 + 8814.65, "ESA 2018"),
    (7199.62, "ESA Movember 2018"),

    (680.49, "UKSG Fall 2018"),
    (1348.59, "UKSG Winter 2019"),
])


class ESAMarathon(MarathonBase):
    index_url = f'{URL}/index/{EVENT}' + '{stream_index}'
    incentive_url = f'{URL}/bids/{EVENT}' + '{stream_index}'
    event_id = 'esa'
    stream_ids = ('2019-winter1', '2019-winter2')

    def read_total(self, streams):
        total = 0
        for stream in streams:
            full_url = self.index_url.format(stream_index=stream)
            source = self.session.get(full_url).text
            soup = BeautifulSoup(source, 'html.parser')

            total_str = soup.find('h3').small.string
            total += float(total_str.split()[2].split(' (')[0].replace(',', '')[1:])

        return total

    @classmethod
    def parse_data(cls, keys, schedule, timezone='UTC'):
        for run in schedule:
            rundata = dict(zip(keys, run['data']))

            yield Run(
                game=rundata['Game'],
                platform=rundata['Platform'],
                category=rundata['Category'],
                runner=cls.strip_md(rundata['Player(s)']),
                start=datetime.fromtimestamp(run['scheduled_t'], tz=pytz.timezone(timezone)),
                estimate=run['length_t'],
            )
