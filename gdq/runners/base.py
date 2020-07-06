import argparse
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from gdq.events import MarathonBase


class RunnerBase(ABC):
    args: argparse.Namespace
    event_config: dict

    def __init__(self, event_config: Dict[str, str], event_args: List[str]):
        self.event_config = event_config
        self.set_options(event_args)

    @abstractmethod
    def get_marathon(self) -> MarathonBase:
        pass

    @abstractmethod
    def get_times(self) -> Tuple[datetime, Optional[datetime]]:
        pass

    def set_options(self, event_args: List[str]) -> None:
        parser = argparse.ArgumentParser()

        self.args = parser.parse_args(event_args)
