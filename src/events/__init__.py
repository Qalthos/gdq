import pyplugs
from abc import ABC, abstractmethod
from typing import Dict, List

from models import Incentive, Run
from parsers import gdq_tracker

IncentiveDict = Dict[str, Incentive]
names = pyplugs.names_factory(__package__)
marathon = pyplugs.call_factory(__package__)


class MarathonBase(ABC):
    url = ""
    event = ""
    records = []
    stream_ids = []
    _total = None

    @property
    def total(self) -> float:
        if self._total is None:
            self._total = sum(
                (
                    self._atof(gdq_tracker.read_total(self.url, self.event + stream_id))
                    for stream_id in self.stream_ids
                )
            )

        return self._total

    def read_incentives(self) -> IncentiveDict:
        incentives = {}
        for stream_id in self.stream_ids:
            incentives.update(
                gdq_tracker.read_incentives(
                    self.url, self.event + stream_id, self._money_parser
                )
            )
        return incentives

    def read_schedules(self):
        return [self._read_schedule(stream_id) for stream_id in self.stream_ids]

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
    def read_total(self):
        return sum(
            (
                self._atof(
                    gdq_tracker.read_total(
                        self.url,
                        self.event + stream_id,
                        donation_re=gdq_tracker.DONATION_EURO,
                    )
                )
                for stream_id in self.stream_ids
            )
        )

    @staticmethod
    def _atof(string):
        return float(string.replace(".", "").replace(",", "."))

    @staticmethod
    def _money_parser(string):
        return MarathonBaseEuro._atof(gdq_tracker.MONEY_EURO.sub("", string))
