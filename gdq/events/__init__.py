import argparse
from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol

from gdq.models import Run


class Marathon(Protocol):
    @abstractmethod
    def refresh_all(self) -> None:
        ...

    @abstractmethod
    def header(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        ...

    @abstractmethod
    def render(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        ...

    @abstractmethod
    def footer(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        ...


class TrackerBase(Marathon, Protocol):
    # Cached live data
    schedules: list[list[Run]] = []
