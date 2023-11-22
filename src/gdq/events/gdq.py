import argparse
import operator
from collections import namedtuple
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import Union

from gdq import money, utils
from gdq.events import TrackerBase
from gdq.models import Event, MultiEvent, SingleEvent
from gdq.parsers import gdq_api

FakeRecord = namedtuple("FakeRecord", ["short_name", "total"])


class GDQTracker(TrackerBase):
    # Tracker base URL
    url: str

    # Historical donation records
    records: list[Event]
    record_offsets: dict[str, float]

    # Cached live data
    current_event: Event

    # Set to account for discrepencies between computed and reported totals.
    offset: float

    def __init__(
            self, url: str, stream_name: str = "",
            offset: float = 0, record_offsets: dict[str, float] = {}):
        # We need to have a trailing '/' for urljoin to work properly
        if url[-1] != "/":
            url += "/"

        self.url = url
        self.stream_name = stream_name
        self.offset = offset
        self.record_offsets = record_offsets

    @property
    def start(self) -> datetime:
        return self.current_event.start_time

    @property
    def end(self) -> datetime:
        if self.schedules:
            return max(schedule[-1].end for schedule in self.schedules)

        return self.start

    @property
    def total(self) -> money.Money:
        return self.current_event.total - self.currency(self.offset)

    @property
    def currency(self) -> type[money.Money]:
        return type(self.current_event.total)

    @property
    def current_events(self) -> list[SingleEvent]:
        if isinstance(self.current_event, SingleEvent):
            return [self.current_event]
        if isinstance(self.current_event, MultiEvent):
            return self.current_event.subevents
        raise ValueError("Unexpected event type encountered")

    def refresh_all(self) -> None:
        readers = (self.read_events, self.read_schedules)
        for reader in utils.show_iterable_progress(readers):
            reader()

    def read_events(self) -> None:
        events = gdq_api.get_events(self.url, event_name=self.stream_name)
        if not events:
            raise IndexError(f"Couldn't find any events at {self.url}")

        for event in events:
            if event.short_name in self.record_offsets:
                event.offset = self.record_offsets[event.short_name]
            if event.start_time > datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=10):
                self.current_event = event
                events.remove(event)
                break

        self.records = sorted(events, key=operator.attrgetter("total"))

    def read_schedules(self) -> None:
        self.schedules = []
        for event in self.current_events:
            self.schedules.append(
                gdq_api.get_runs(self.url, event.event_id, self.currency)
            )

    def header(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if args.extended_header and self.current_event.charity:
            header = f"{self.current_event.name} supporting {self.current_event.charity}"
            yield header.center(width)

        last_record: Union[FakeRecord, Event] = FakeRecord(total=self.currency(), short_name="GO!")
        for record in self.records:
            if record.total > self.total:
                break
            last_record = record
        else:
            record = self.current_event

        trim = len(last_record.short_name) + len(record.short_name) + 2
        bar_width = width - trim
        prog_bar = money.progress_bar_money(last_record.total, self.total, record.total, width=bar_width)
        yield f"{last_record.short_name.upper()} {prog_bar} {record.short_name.upper()}"
