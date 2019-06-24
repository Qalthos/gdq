from datetime import datetime
from typing import Callable, Generator, List

import pyplugs
import requests
from bs4 import BeautifulSoup
from dateutil import parser, tz

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import horaro
from gdq.utils import NOW, strip_md


def read_schedule(schedule_url: str, parse_run: Callable) -> Generator:
    source = requests.get(schedule_url).text
    soup = BeautifulSoup(source, 'html.parser')

    schedule = soup.find('table')
    run_starts = schedule.find_all('span', class_='datetime')

    for index, row in enumerate(run_starts):
        time = parser.parse(row.text)
        if time > NOW:
            # If we havent started yet, index should still be 0
            start = max(index - 1, 0)
            for td in run_starts[start:]:
                yield parse_run(td.parent)


def parse_data(keys, schedule, timezone="UTC") -> Generator:
    for run in schedule:
        run_data = dict(zip(keys, run["data"]))

        yield Run(
            game=run_data["Game"],
            platform=run_data["System"] or "",
            category=run_data["Category"] or "",
            runner=strip_md(run_data["Runner(s)"]),
            start=datetime.fromtimestamp(run["scheduled_t"], tz=tz.gettz(timezone)),
            estimate=run["length_t"],
        )


@pyplugs.register
class RPGLimitBreak(MarathonBase):
    event = "rpglb"
    url = "https://www.rpglimitbreak.com/tracker"
    stream_ids = ("2019",)
    records = sorted(
        [
            (46595, "RPGLB 2015"),
            (75194.33, "RPGLB 2016"),
            (111773.56, "RPGLB 2017"),
            (164099.31, "RPGLB 2018"),
            (200339.84, "RPGLB 2019"),
        ]
    )

    def _read_schedule(self, stream_id) -> List[Run]:
        return horaro.read_schedule(self.event, stream_id, parse_data)
