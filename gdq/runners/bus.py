import argparse

from gdq.events.desert_bus import DesertBus
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self) -> DesertBus:
        if "start" not in self.event_config:
            raise KeyError("`start` key missing from configuration")

        return DesertBus(self.event_config["start"])

    def set_options(self, event_args: list[str]) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-o", "--overall", action="store_true",
            help="Show total bus progress instead of current hout to next",
        )
        parser.add_argument(
            "-x", "--extended-header", action="store_true",
            help="Show expanded information in the header",
        )

        self.args = parser.parse_args(event_args)
