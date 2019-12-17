from datetime import datetime
from typing import Iterator

from dateutil import tz
import pyplugs

from gdq.events.horarobase import HoraroSchedule
from gdq.models import Run


@pyplugs.register
class FrameFatales(HoraroSchedule):
    group_name = "framefatales"
    current_event = "a19schedule"

    @staticmethod
    def parse_data(keys, schedule, timezone="UTC") -> Iterator[Run]:
        for run in schedule:
            run_data = dict(zip(keys, run["data"]))
            game, runner = "", ""
            for splitval in ("by", "with", "of"):
                try:
                    game, runner = run_data["Description"].split(f" {splitval} ")
                except ValueError:
                    continue
                else:
                    break
            else:
                game = run_data["Description"]

            if "%" in game:
                # Really crappy category detection
                game, cat_tail = game.split("%")
                game, cat_head = game.rsplit(" ", 1)
                category = "%".join((cat_head, cat_tail))
            else:
                category = ""

            yield Run(
                game=game,
                platform="",
                category=category,
                runner=runner,
                start=datetime.fromtimestamp(run["scheduled_t"], tz=tz.gettz(timezone)),
                estimate=run["length_t"],
            )
