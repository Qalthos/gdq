from datetime import datetime
from typing import List

from dateutil import tz
import pyplugs

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import horaro
from gdq.utils import strip_md


def parse_data(keys, schedule, timezone='UTC') -> List[Run]:
    for run in schedule:
        run_data = dict(zip(keys, run['data']))

        yield Run(
            game=run_data['Game'],
            platform=run_data['Platform'] or "",
            category=run_data['Category'] or "",
            runner=strip_md(run_data['Player(s)']),
            start=datetime.fromtimestamp(run['scheduled_t'], tz=tz.gettz(timezone)),
            estimate=run['length_t'],
        )


@pyplugs.register
class ESAMarathon(MarathonBase):
    url = 'https://donations.esamarathon.com'
    event = 'esa'
    stream_ids = ('2019s1', '2019s2')
    records = sorted([
        # Original
        (58626, "ESA 2017"),
        (62783.69 + 8814.65, "ESA 2018"),
        (78255.44 + 6880.43, "ESA 2019"),

        # Winter
        (22611.53, "ESA Winter 2018"),
        (27574.68 + 2501.00, "ESA Winter 2019"),

        # UKSG
        (680.49, "UKSG Fall 2018"),
        (1348.59, "UKSG Winter 2019"),

        # Other
        (7199.62, "ESA Movember 2018"),
        (6175.67, "Twitchcon Europe 2019")
    ])

    def _read_schedule(self, stream_id) -> List[Run]:
        stream_map = {
            "2019s1": "2019-one",
            "2019s2": "2019-two",
        }
        return horaro.read_schedule(self.event, stream_map[stream_id], parse_data)
