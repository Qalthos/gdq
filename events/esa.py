from datetime import datetime
from typing import List

from dateutil import tz
import pyplugs

from parsers.horaro import read_schedule
from events import MarathonBase
from utils import strip_md
from models import Run


def parse_data(keys, schedule, timezone='UTC') -> List[Run]:
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


@pyplugs.register
class ESAMarathon(MarathonBase):
    url = 'https://donations.esamarathon.com'
    event_id = 'esa'
    records = sorted([
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
    stream_ids = ('2019-winter1', '2019-winter2')

    def _read_schedule(self, stream_id) -> List[Run]:
        return read_schedule(self.event_id, stream_id, parse_data)
