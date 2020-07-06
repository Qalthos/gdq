import argparse
from datetime import datetime
from typing import Optional

from gdq.events import MarathonBase
from gdq.events.horarobase import HoraroSchedule
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self, event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
        try:
            return HoraroSchedule(
                group=event_config["group"],
                event=event_config["event"],
                key_map=event_config["keys"],
            )
        except KeyError:
            print(f"Incomplete configuration for {args.stream_name}")

        return None

    def get_start(self, event_config: dict) -> datetime:
        marathon = HoraroSchedule(
            group=event_config["group"],
            event=event_config["event"],
            key_map=event_config["keys"],
        )
        marathon.refresh_all()
        return marathon.schedules[0][0].start

    def get_options(self, parser: argparse.ArgumentParser) -> argparse.Namespace:
        parser.add_argument(
            "-i", "--stream_index", type=int, default=1,
            help="follow only a single stream",
        )
        return parser.parse_args()
