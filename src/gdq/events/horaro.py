from typing import TYPE_CHECKING

from common.display import SquishableString
from gdq.events import TrackerBase
from gdq.parsers.horaro import Horaro

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable
    from datetime import datetime


class HoraroTracker(TrackerBase):
    current_event: str
    event_name: str

    def __init__(self, group: str, key_map: dict[str, str]):
        self.event_name = group
        self.parser = Horaro(key_map=key_map)

    def refresh_all(self) -> None:
        events = self.parser.get_events(self.event_name)

        records = []
        future = []
        for event in events:
            if event.future:
                future.append(event)
            else:
                records.append(event)

        if not future:
            err = "No upcoming events scheduled"
            raise ValueError(err)
        self.current_event = min(future, key=lambda x: x.start_time)
        if self.parser is not None:
            self.parser.event_id = self.current_event.id
            self.parser.currency = self.current_event.total.__class__

        self.records = sorted(events, key=lambda x: x.total)

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

        yield SquishableString(f"{self.current_event} by {self.event_name}", str.center)
