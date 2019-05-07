from datetime import datetime
from typing import List

from dateutil import tz

from parsers.horaro import read_schedule
from events import MarathonBase
from utils import strip_md
from models import Run

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


def parse_data(keys, schedule, timezone='UTC'):
    for run in schedule:
        run_data = dict(zip(keys, run['data']))

        yield Run(
            game=run_data['Game'],
            platform=run_data['Platform'],
            category=run_data['Category'],
            runner=strip_md(run_data['Player(s)']),
            start=datetime.fromtimestamp(run['scheduled_t'], tz=tz.gettz(timezone)),
            estimate=run['length_t'],
        )


class ESAMarathon(MarathonBase):
    index_url = f'{URL}/index/{EVENT}' + '{stream_index}'
    incentive_url = f'{URL}/bids/{EVENT}' + '{stream_index}'
    event_id = 'esa'
    stream_ids = ('2019-winter1', '2019-winter2')

    def _read_schedule(self, stream_id) -> List[Run]:
        return read_schedule(self.event_id, stream_id, parse_data)
