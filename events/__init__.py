from abc import ABC, abstractmethod
from typing import Callable, Dict

from parsers import gdq_tracker

PLUGINS: Dict[str, Callable] = {}


class MarathonBase(ABC):
    url = ""
    event = ""
    stream_ids = []
    records = []

    def read_total(self):
        return sum(
            (
                self._atof(gdq_tracker.read_total(self.url, self.event + stream_id))
                for stream_id in self.stream_ids
            )
        )

    def read_incentives(self):
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
    def _read_schedule(self, stream_id):
        pass

    @staticmethod
    def _atof(string):
        return float(string.replace(",", ""))

    @staticmethod
    def _money_parser(string):
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


def register(func: Callable) -> Callable:
    PLUGINS[func.__name__] = func
    return func


def call(name: str) -> MarathonBase:
    return PLUGINS[name]()
