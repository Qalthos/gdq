from typing import Any

from gdq.events.gdq import GDQTracker
from gdq.parsers import bsg


class BSGTracker(GDQTracker):
    event_name: str

    def __init__(self, event_name: str, *args: Any, **kwargs: Any):
        self.event_name = event_name
        super().__init__(*args, **kwargs)

    def read_schedules(self) -> None:
        self.schedules = [bsg.get_runs(self.url, self.event_name)]
