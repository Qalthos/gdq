import argparse
from datetime import datetime

from gdq.events.gdq import GDQTracker
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self) -> GDQTracker:
        if "url" not in self.event_config:
            raise KeyError("`url` key missing from configuration")

        record_offsets = {}
        if "offsets" in self.event_config:
            record_offsets = self.event_config["offsets"]

        return GDQTracker(
            url=self.event_config["url"],
            stream_index=-self.args.stream_index,
            offset=self.args.delta_total,
            record_offsets=record_offsets,
        )

    def set_options(self, event_args: list[str]) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-d", "--delta-total", type=float, default=0,
            help="Offset to subtract from event total to reconcile discrepencies",
        )
        parser.add_argument(
            "-i", "--stream_index", type=int, default=1,
            help="Follow only a single stream",
        )
        parser.add_argument(
            "-o", "--min-options", type=int, default=5,
            help="Minimum number of choices before applying percent cutoff.",
        )
        parser.add_argument(
            "-p", "--min-percent", type=int, default=5,
            help="Minimum percent before displaying choice incentive.",
        )
        parser.add_argument(
            "-s", "--split-pane", action="store_true",
            help="Display a split view with schedule on the left and incentives on the right",
        )
        parser.add_argument(
            "-w", "--min-width", type=int, default=16,
            help="Minimum width for option description names",
        )
        parser.add_argument(
            "-x", "--extended-header", action="store_true",
            help="Show expanded information in the header",
        )
        parser.add_argument(
            "--hide-completed", action="store_true",
            help="Hide completed donation incentives.",
        )
        parser.add_argument(
            "--hide-basic", action="store_true",
            help="Hide runs with no active incentives",
        )
        parser.add_argument(
            "--hide-incentives", action="store_true",
            help="Hide run incentives",
        )
        parser.add_argument(
            "--list", action="store_true",
            help="Show known marathons and status",
        )

        self.args = parser.parse_args(event_args)
