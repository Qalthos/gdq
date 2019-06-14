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

        yield Run(
            game=run_data["Game"],
            platform=run_data["Console"] or "",
            category=run_data["Category"] or "",
            runner=run_data["Runner"] or "",
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
