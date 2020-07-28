import argparse
from datetime import datetime
from typing import List, Optional, Tuple

from gdq.events.horarobase import HoraroSchedule
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self) -> HoraroSchedule:
        try:
            return HoraroSchedule(
                group=self.event_config["group"],
                event=self.event_config["event"],
                key_map=self.event_config["keys"],
            )
        except KeyError as exc:
            raise KeyError(f"`{exc!s}` key missing from configuration")

    def get_times(self) -> Tuple[datetime, Optional[datetime]]:
        event = self.get_marathon()
        event.refresh_all()

        start = event.schedules[0][0].start
        end = event.schedules[0][-1].start
        return (start, end)

    def set_options(self, event_args: List[str]) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-i", "--stream_index", type=int, default=1,
            help="follow only a single stream",
        )

        self.args = parser.parse_args(event_args)
