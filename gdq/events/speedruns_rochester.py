from datetime import datetime
from typing import Generator, List

from dateutil import tz
import pyplugs

from gdq.events import MarathonBase
from gdq.parsers import horaro
from gdq.models import Run


def parse_data(keys, schedule, timezone="UTC") -> Generator:
    for run in schedule:
        run_data = dict(zip(keys, run["data"]))

        if run_data["Runner"] is None:
            continue

        yield Run(
            game=run_data["Game"],
            platform=run_data["Console"],
            category=run_data["Category"],
            runner=run_data["Runner"],
            start=datetime.fromtimestamp(run["scheduled_t"], tz=tz.gettz(timezone)),
            estimate=run["length_t"],
        )


@pyplugs.register
class SpeedrunsRochester(MarathonBase):
    schedule_only = True
    event = "srrocsm"
    stream_ids = ("schedule",)

    def _read_schedule(self, stream_id: str) -> List[Run]:
        return horaro.read_schedule(self.event, stream_id, parse_data)
