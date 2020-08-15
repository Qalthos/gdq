from gdq.events.gdq import GDQTracker
from gdq.parsers import bsg


class BSGTracker(GDQTracker):
    def read_schedules(self) -> None:
        self.schedules = [bsg.get_runs(self.url, self.current_event.short_name.lower())]
