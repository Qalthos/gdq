import argparse
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple

from gdq.events import MarathonBase


class RunnerBase(ABC):
    @abstractmethod
    def get_marathon(self, event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
        pass

    @abstractmethod
    def get_times(self, event_config: dict) -> Tuple[datetime, Optional[datetime]]:
        pass

    def get_options(self, parser: argparse.ArgumentParser) -> argparse.Namespace:
        return parser.parse_args()
