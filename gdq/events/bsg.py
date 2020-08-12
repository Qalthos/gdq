from gdq.events import TrackerBase
from gdq.parsers import bsg


class BSGTracker(TrackerBase):
    event_name: str

    def __init__(self, url: str, event_name: str):
        self.url = url
        self.event_name = event_name

    def refresh_all(self) -> None:
        self.schedules = [
            bsg.get_runs(self.url, self.event_name)
        ]
