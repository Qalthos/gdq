from gdq.events import TrackerBase
from gdq.parsers import horaro


class HoraroTracker(TrackerBase):
    # horaro.org keys
    group_name = ""
    current_event: str
    key_map: dict[str, str]

    def __init__(self, group: str, event: str, key_map: dict[str, str]):
        self.group_name = group
        self.current_event = event
        self.key_map = key_map

    def refresh_all(self) -> None:
        self.schedules = [
            horaro.read_schedule(self.group_name, self.current_event, self.key_map)
        ]
