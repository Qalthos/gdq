from abc import ABC, abstractmethod
import re
from typing import Iterator, List

import pyplugs

from gdq.models import Run, Event, SingleEvent
from gdq.parsers import gdq_api, horaro

names = pyplugs.names_factory(__package__)
marathon = pyplugs.call_factory(__package__)


def money_parser(string: str) -> float:
    return float(re.compile('[$,\n]').sub("", string))


class MarathonBase(ABC):
    # Tracker base URL
    url = ""

    # Cached live data
    display_streams: int
    schedules = [[]]

    @abstractmethod
    def refresh_all(self) -> None:
        raise NotImplementedError


class GDQTracker(MarathonBase):
    # Historical donation records
    records = []

    # Cached live data
    current_event: Event
    incentives = {}

    def __init__(self, url: str = None, streams: int = 1) -> None:
        self.url = url or self.url
        self.display_streams = streams
        self.read_events()

    @property
    def total(self):
        return self.current_event.total

    @property
    def current_events(self) -> List[SingleEvent]:
        if events := getattr(self.current_event, "subevents", None):
            return events
        else:
            return [self.current_event]

    def refresh_all(self) -> None:
        self.read_events()
        self.schedules = [gdq_api.get_runs(self.url, event.event_id) for event in self.current_events]
        self.read_incentives()

    def read_events(self) -> None:
        events = list(gdq_api.get_events(self.url))
        self.current_event = events.pop(-1)

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
    current_event: str

    def refresh_all(self) -> None:
        horaro.read_schedule(self.group_name, self.current_event, self.parse_data)

    @staticmethod
    @abstractmethod
    def parse_data(keys, schedule, timezone="UTC") -> Iterator[Run]:
        raise NotImplementedError
