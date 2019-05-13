from datetime import datetime
from typing import Generator, List

from dateutil import tz
import pyplugs

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import horaro


def parse_data(keys, schedule, timezone="UTC") -> Generator:
    for run in schedule:
        run_data = dict(zip(keys, run['data']))
        try:
            game, runner = run_data['Description'].split(" by ")
        except ValueError:
            game = run_data['Description']
            runner = ""

        yield Run(
            game=game,
            platform="",
            category="",
            runner=runner,
            start=datetime.fromtimestamp(run['scheduled_t'], tz=tz.gettz(timezone)),
            estimate=run['length_t'],
        )


@pyplugs.register
class FrameFatales(MarathonBase):
    event = 'framefatales'
    stream_ids = ('schedule',)
    schedule_only = True

    def _read_schedule(self, stream_id: str) -> List[Run]:
        return horaro.read_schedule(self.event, stream_id, parse_data)