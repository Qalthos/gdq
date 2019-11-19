from abc import ABC, abstractmethod
import re
from typing import Iterator, List, Optional

import pyplugs

from gdq.models import Event, Run
from gdq.parsers import gdq_api, horaro

names = pyplugs.names_factory(__package__)
marathon = pyplugs.call_factory(__package__)


def money_parser(string: str) -> float:
    return float(re.compile('[$,\n]').sub("", string))


class MarathonBase(ABC):
    # Tracker base URL
    url = ""

    # Cached live data
    current_events = []
    schedules = [[]]

    @abstractmethod
    def refresh_all(self) -> None:
        raise NotImplementedError


class GDQTracker(MarathonBase):
    # Historical donation records
    records = []

    # Cached live data
    total = 0
    incentives = {}

    def __init__(self, url: str = None, streams: int = 1) -> None:
        self.url = url or self.url

        self.current_events: List[Optional[Event]] = [None] * streams
        self.read_events()

    def refresh_all(self) -> None:
        self.read_events()
        self.total = sum((event.total for event in self.current_events))
        self.schedules = [gdq_api.get_runs(self.url, event.event_id) for event in self.current_events]
        self.read_incentives()

    def read_events(self) -> None:
        events = list(gdq_api.get_events(self.url))
        for i in range(len(self.current_events)):
            self.current_events[i] = events.pop(-1)

        self.records = sorted(
            [(event.total, event.short_name.upper()) for event in events]
        )

    def read_incentives(self) -> None:
        incentives = {}
        for event in self.current_events:
            incentives.update(
                gdq_api.get_incentives_for_event(self.url, event.event_id)
            )
        self.incentives = incentives


class HoraroSchedule(MarathonBase):
    # horaro.org keys
    group_name = ""

    def refresh_all(self) -> None:
        self.schedules = [
            horaro.read_schedule(self.group_name, stream_id, self.parse_data)
            for stream_id in self.current_events
        ]

    @staticmethod
    @abstractmethod
    def parse_data(keys, schedule, timezone="UTC") -> Iterator[Run]:
        raise NotImplementedError
