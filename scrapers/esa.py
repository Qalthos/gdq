from datetime import datetime

import pytz

from scrapers import MarathonBase
from utils import Run

EVENT = 'esaw2019s'
URL = 'https://donations.esamarathon.com'
RECORDS = sorted([
    # Original
    (58626, "ESA 2017"),
    (62783.69 + 8814.65, "ESA 2018"),

    # Winter
    (22611.53, "ESA Winter 2018"),

    # UKSG
    (680.49, "UKSG Fall 2018"),
    (1348.59, "UKSG Winter 2019"),

    # Other
    (7199.62, "ESA Movember 2018"),
])


class ESAMarathon(MarathonBase):
    index_url = f'{URL}/index/{EVENT}' + '{stream_index}'
    incentive_url = f'{URL}/bids/{EVENT}' + '{stream_index}'
    event_id = 'esa'
    stream_ids = ('2019-winter1', '2019-winter2')

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
