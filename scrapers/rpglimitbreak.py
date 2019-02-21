from datetime import datetime

import pytz

from scrapers import MarathonBase
from utils import Run

EVENT = 'rpglb2018'
URL = 'https://www.rpglimitbreak.com/tracker'
RECORDS = sorted([
    (46595, "RPGLB 2015"),
    (75194.33, "RPGLB 2016"),
    (111773.56, "RPGLB 2017"),
    (164099.31, "RPGLB 2018"),
])


class RPGLimitBreak(MarathonBase):
    index_url = f'{URL}/index/{EVENT}'
    incentive_url = f'{URL}/bids/{EVENT}'
    event_id = 'rpglb'
    stream_ids = ('2018',)

    @classmethod
    def parse_data(cls, keys, schedule, timezone='UTC'):
        for run in schedule:
            rundata = dict(zip(keys, run['data']))

            yield Run(
                game=rundata['Game'],
                platform=rundata['System'],
                category=rundata['Category'],
                runner=cls.strip_md(rundata['Runner(s)']),
                start=datetime.fromtimestamp(run['scheduled_t'], tz=pytz.timezone(timezone)),
                estimate=run['length_t'],
            )
