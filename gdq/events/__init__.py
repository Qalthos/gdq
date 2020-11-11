import argparse
import math
from abc import abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Protocol

from gdq.models import Run
from gdq import utils


class Marathon(Protocol):
    @abstractmethod
    def refresh_all(self) -> None:
        ...

    @property
    @abstractmethod
    def start(self) -> datetime:
        ...

    @property
    @abstractmethod
    def end(self) -> datetime:
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
        if args:
            # Reserved for future use
            pass

        start = self.start
        end = self.end
        elapsed = max(utils.now - start, timedelta())
        total = end - start
        remaining = min(start + total - utils.now, total)

        hours_done = f"[{utils.timedelta_as_hours(elapsed)}]"
        hours_left = f"[{utils.timedelta_as_hours(remaining)}]"
        progress_width = width - len(hours_done) - len(hours_left) - 3

        completed_width = math.floor(
            progress_width * elapsed / total
        )
        progress = f"{'─' * completed_width}🎮{' ' * (progress_width - completed_width - 1)}🏁"

        yield f"{hours_done}{progress}{hours_left}"
