import argparse
from abc import ABC, abstractmethod
from itertools import zip_longest
from typing import Protocol

from gdq import utils
from gdq.models import Run


class MarathonBase(Protocol):
    def refresh_all(self) -> None:
        ...

    def display(self, args: argparse.Namespace) -> bool:
        ...


class TrackerBase(ABC):
    # Cached live data
    schedules: list[list[Run]] = []

    @abstractmethod
    def refresh_all(self) -> None:
        raise NotImplementedError
