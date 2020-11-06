import argparse
from datetime import datetime, timedelta
from typing import Optional

from gdq.events.desert_bus import DesertBus
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self) -> DesertBus:
        if "start" not in self.event_config:
            raise KeyError("`start` key missing from configuration")

        return DesertBus(self.event_config["start"])

    def get_times(self) -> tuple[datetime, Optional[datetime]]:
        event = self.get_marathon()
        event.refresh_all()

        return (event.start, event.start + timedelta(hours=event.hours))

    def set_options(self, event_args: list[str]) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-o", "--overall", action="store_true",
            help="Show total bus progress instead of current hout to next",
        )

        self.args = parser.parse_args(event_args)
