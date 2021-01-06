import argparse
from datetime import datetime

from gdq.events.horaro import HoraroTracker
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self) -> HoraroTracker:
        try:
            return HoraroTracker(
                group=self.event_config["group"],
                event=self.event_config["event"],
                key_map=self.event_config["keys"],
            )
        except KeyError as exc:
            raise KeyError(f"`{exc!s}` key missing from configuration")

    def set_options(self, event_args: list[str]) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-i", "--stream_index", type=int, default=1,
            help="Follow only a single stream",
        )

        self.args = parser.parse_args(event_args)
