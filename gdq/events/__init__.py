from abc import ABC, abstractmethod
import re
from typing import Dict, List

import pyplugs

from gdq.models import Incentive, Run
from gdq.parsers import gdq_api, gdq_tracker, horaro
from gdq import utils

IncentiveDict = Dict[str, Incentive]
names = pyplugs.names_factory(__package__)
marathon = pyplugs.call_factory(__package__)


class MarathonBase(ABC):
    # Tracker base URL
    url = ""

    # Cached live data
    schedules = [[]]

    @abstractmethod
    def refresh_all(self):
        raise NotImplementedError


class GDQTracker(MarathonBase):
    # Historical donation records
    records = []

    # Cached live data
    total = 0
    incentives = {}

    def __init__(self):
        self.events = list(gdq_api.get_events(self.url))
        self.current_event = self.events.pop(-1)
        self.records = sorted([(event.total, event.short_name.upper()) for event in self.events])

    def refresh_all(self):
        self.schedules = [gdq_api.get_runs(self.url, self.current_event.event_id)]
        self.read_incentives()

    def read_incentives(self) -> None:
        incentives = {}
        incentives.update(
            gdq_tracker.read_incentives(
                self.url,
                self.current_event.short_name,
            )
        )
        self.incentives = incentives


class HoraroSchedule(MarathonBase):
    # horaro.org keys
    event = ""
    stream_ids = []

    def refresh_all(self):
        self.schedules = [
            horaro.read_schedule(self.event, stream_id, self.parse_data)
            for stream_id in self.stream_ids
        ]

    @abstractmethod
    @staticmethod
    def parse_data(keys, schedule, timezone="UTC"):
        raise NotImplementedError
