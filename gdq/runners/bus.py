from datetime import datetime, timedelta
from typing import Optional, Tuple

from gdq.events.desert_bus import DesertBus
from gdq.runners.base import RunnerBase


class Runner(RunnerBase):
    def get_marathon(self) -> DesertBus:
        if "start" not in self.event_config:
            raise KeyError(f"`start` key missing from {self.args.stream_name} configuration")

        return DesertBus(self.event_config["start"])

    def get_times(self) -> Tuple[datetime, Optional[datetime]]:
        event = self.get_marathon()
        event.refresh_all()

        return (event.start, event.start + timedelta(hours=event.hours))
