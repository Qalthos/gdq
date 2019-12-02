from datetime import datetime
from typing import Iterator

from dateutil import tz
import pyplugs

from gdq.events import HoraroSchedule
from gdq.models import Run


@pyplugs.register
class SpeedrunsRochester(HoraroSchedule):
    group_name = "srrocsm"
    current_event = "schedule"

    @staticmethod
    def parse_data(keys, schedule, timezone="UTC") -> Iterator[Run]:
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
