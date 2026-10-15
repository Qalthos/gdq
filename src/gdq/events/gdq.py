# Copyright 2019
# SPDX-License-Identifier: MIT
from enum import StrEnum, auto
from typing import TYPE_CHECKING, NamedTuple

from common.progress_bar import progress_bar_money
from gdq import utils
from gdq.events import TrackerBase
from gdq.models import Event, v1, v2
from gdq.parsers import gdq_v1, gdq_v2

type SingleEvent = v1.SingleEvent | v2.Event
type MultiEvent = v1.MultiEvent

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable
    from datetime import datetime

    from common.money import Money
    from gdq.parsers import Parser


class FakeRecord(NamedTuple):
    short: str
    total: Money


class GDQVersion(StrEnum):
    V1 = auto()
    V2 = auto()


class GDQTracker(TrackerBase):
    # Tracker base URL
    url: str
    _version: GDQVersion = GDQVersion.V2

    # Historical donation records
    records: list[Event]

    # Cached live data
    parser: Parser
    current_event: Event

    def __init__(
        self,
        url: str,
        stream_name: str = "",
    ) -> None:
        # We need to have a trailing '/' for urljoin to work properly
        if not url.endswith("/"):
            url += "/"

        self.url = url
        self.stream_name = stream_name

        match self._version:
            case GDQVersion.V1:
                self.parser = gdq_v1.GDQV1(url)
            case GDQVersion.V2:
                self.parser = gdq_v2.GDQV2(url)

    @property
    def start(self) -> datetime:
        return self.current_event.start_time

    @property
    def end(self) -> datetime:
        if self.schedules:
            return max(schedule[-1].end for schedule in self.schedules)

        return self.start

    @property
    def total(self) -> Money:
        return self.current_event.total

    @property
    def currency(self) -> type[Money]:
        return type(self.current_event.total)

    @property
    def current_events(self) -> list[Event]:
        if isinstance(self.current_event, Event):
            return [self.current_event]
        if isinstance(self.current_event, v1.MultiEvent):
            return self.current_event.subevents
        msg = "Unexpected event type encountered"
        raise ValueError(msg)

    def refresh_all(self) -> None:
        readers = (self.read_events, self.read_schedules)
        for reader in utils.show_iterable_progress(readers):
            reader()

    def read_events(self) -> None:
        events = self.parser.get_events(event_name=self.stream_name)
        if not events:
            msg = f"Couldn't find any events at {self.url}"
            raise IndexError(msg)

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

    def read_schedules(self) -> None:
        self.schedules = []
        for event in self.current_events:
            schedule = self.parser.get_runs()
            self.schedules.append(schedule)

    def header(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        if args.extended_header and self.current_event.receiver:
            header = f"{self.current_event.name} supporting {self.current_event.receiver}"
            yield header.center(width)

        last_record: FakeRecord | Event = FakeRecord(
            total=self.currency(),
            short="GO!",
        )
        for record in self.records:
            if record.total > self.total:
                break
            last_record = record
        else:
            record = self.current_event

        trim = len(last_record.short) + len(record.short) + 2
        bar_width = width - trim
        prog_bar = progress_bar_money(
            last_record.total,
            self.total,
            record.total,
            width=bar_width,
        )
        yield f"{last_record.short.upper()} {prog_bar} {record.short.upper()}"
