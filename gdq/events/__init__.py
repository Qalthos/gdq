from abc import ABC, abstractmethod
import re
from typing import Dict, List

import pyplugs
import requests

from gdq.models import Incentive, Run
from gdq.parsers import gdq_tracker
from gdq import utils

IncentiveDict = Dict[str, Incentive]
names = pyplugs.names_factory(__package__)
marathon = pyplugs.call_factory(__package__)


class MarathonBase(ABC):
    donation_re = re.compile(fr'Donation Total:\s+\$([\d,]+.[0-9]+)')

    # Tracker base URL
    url = ""

    # Disables total and incentives when true
    schedule_only = False

    # horaro.org keys
    event = ""
    stream_ids = []

    # Historical donation records
    records = []

    # Cached live data
    total = 0
    incentives = {}
    schedules = [[]]

    def refresh_all(self):
        try:
            self.read_schedules()
            if not self.schedule_only:
                self.read_total()
                self.read_incentives()
        except requests.exceptions.ConnectionError:
            # Hopefully temporary, just use cached values.
            pass

    def read_total(self) -> None:
        total = 0
        for stream_id in self.stream_ids:
            full_url = "{}/index/{}{}".format(self.url, self.event, stream_id)
            soup = utils.url_to_soup(full_url)
            total += gdq_tracker.read_total(soup, donation_re=self.donation_re, atof=self._atof)
        self.total = total

    def read_incentives(self) -> None:
        incentives = {}
        for stream_id in self.stream_ids:
            incentives.update(
                gdq_tracker.read_incentives(
                    self.url,
                    self.event + stream_id,
                    self._money_parser,
                )
            )
        self.incentives = incentives

    def read_schedules(self) -> None:
        self.schedules = [self._read_schedule(stream_id) for stream_id in self.stream_ids]

    @abstractmethod
    def _read_schedule(self, stream_id) -> List[Run]:
        pass

    @staticmethod
    def _atof(string: str) -> float:
        return float(string.replace(",", ""))

    @staticmethod
    def _money_parser(string: str) -> float:
        return float(gdq_tracker.MONEY_DOLLAR.sub("", string))


class MarathonBaseEuro(MarathonBase, ABC):
    donation_re = re.compile(fr'Donation Total:\s+€ ([\d ]+,[0-9]+)')

    @staticmethod
    def _atof(string):
        return float(string.replace(" ", "").replace(",", "."))

    @staticmethod
    def _money_parser(string):
        return MarathonBaseEuro._atof(gdq_tracker.MONEY_EURO.sub("", string))
