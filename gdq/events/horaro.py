import argparse
from collections.abc import Iterable
from datetime import datetime

from gdq.events import TrackerBase
from gdq.parsers import horaro


class HoraroTracker(TrackerBase):
    # horaro.org keys
    group_name: str = ""
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

    @property
    def start(self) -> datetime:
        return self.schedules[0][0].start

    @property
    def end(self) -> datetime:
        return self.schedules[0][-1].end

    def header(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if args:
            # reserved for future use
            pass

        yield f"{self.current_event} by {self.group_name}".center(width)
