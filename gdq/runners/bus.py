import argparse
from datetime import datetime, timedelta
from typing import Optional, Tuple

from gdq.events import MarathonBase
from gdq.events.desert_bus import DesertBus
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self, event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
        if "start" in event_config:
            return DesertBus(event_config["start"])
        else:
            print(f"`start` key missing from {args.stream_name} configuration")

        return None

    def get_times(self, event_config: dict) -> Tuple[datetime, Optional[datetime]]:
        event = DesertBus(event_config["start"])
        event.refresh_all()
        return (event.start, event.start + timedelta(hours=event.hours))
