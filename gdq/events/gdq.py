import argparse
import operator
from collections import namedtuple
from collections.abc import Iterable

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
            self, url: str, stream_index: int = -1,
            offset: float = 0, record_offsets: dict[str, float] = {}):
        # We need to have a trailing '/' for urljoin to work properly
        if url[-1] != "/":
            url += "/"

        self.url = url
        self.stream_index = stream_index
        self.offset = offset
        self.record_offsets = record_offsets

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
        events = gdq_api.get_events(self.url)
        if not events:
            raise IndexError(f"Couldn't find any events at {self.url}")

        for event in events:
            if event.short_name in self.record_offsets:
                event.offset = self.record_offsets[event.short_name]

        self.current_event = events.pop(self.stream_index)

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

        last_record = FakeRecord(total=self.currency(), short_name="GO!")
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

    def render(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        first_line = True

        # TODO: Do this properly with columns
        schedule = self.schedules[0]
        for run in schedule:
            for line in run.render(width=width, args=args):
                if first_line:
                    line = utils.flatten(line)
                    first_line = False
                yield line

    def footer(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if width:
            # Reserved for future use
            pass

        if args:
            # Reserved for future use
            pass

        return
        yield
