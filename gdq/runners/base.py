import argparse
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from gdq.events import Marathon


class RunnerBase(ABC):
    args: argparse.Namespace
    event_config: dict[str, Any]

    def __init__(self, event_config: dict[str, Any], event_args: list[str]):
        self.event_config = event_config
        self.set_options(event_args)

    @abstractmethod
    def get_marathon(self) -> Marathon:
        pass

    def get_times(self) -> tuple[datetime, datetime]:
        event = self.get_marathon()
        event.refresh_all()

        return (event.start, event.end)

    def set_options(self, event_args: list[str]) -> None:
        parser = argparse.ArgumentParser()

        self.args = parser.parse_args(event_args)
