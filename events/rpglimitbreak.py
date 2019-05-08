from datetime import datetime
from typing import Generator, List

from dateutil import tz
import pyplugs

from events import MarathonBase
from models import Run
from parsers import horaro
from utils import strip_md


def parse_data(keys, schedule, timezone="UTC") -> Generator[Run, None, None]:
    for run in schedule:
        run_data = dict(zip(keys, run["data"]))

        yield Run(
            game=run_data["Game"],
            platform=run_data["System"],
            category=run_data["Category"],
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
        ]
    )

    def _read_schedule(self, stream_id) -> List[Run]:
        event_id = "rpglb"
        return horaro.read_schedule(event_id, stream_id, parse_data)
