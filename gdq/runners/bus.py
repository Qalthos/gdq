import argparse
from datetime import datetime
from typing import Optional

from gdq.events import MarathonBase
from gdq.events.desert_bus import DesertBus
from gdq.runners import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self, event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
        if "start" in event_config:
            return DesertBus(event_config["start"])
        else:
            print(f"`start` key missing from {args.stream_name} configuration")

        return None

    def get_start(self, event_config: dict) -> datetime:
        return event_config["start"]
