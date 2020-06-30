import argparse
import sys
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import Dict
from typing import Optional

from gdq.events import MarathonBase
from gdq.runners import bus
from gdq.runners import gdq
from gdq.runners import horaro


class RunnerBase(ABC):
    @abstractmethod
    def get_marathon(self, event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
        pass

    @abstractmethod
    def get_start(self, event_config: dict) -> datetime:
        pass

    def get_options(self, parser: argparse.ArgumentParser) -> argparse.Namespace:
        return parser.parse_args()


def get_base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--interval", type=int, default=60,
        help="time between screen refreshes",
    )
    parser.add_argument(
        "--oneshot", action="store_true",
        help="Run only once and then exit",
    )
    parser.add_argument(
        "stream_name", nargs="?", type=str, default="gdq",
        help="The event to follow",
    )
    return parser


def get_runner(config: Dict[str, str]) -> RunnerBase:
    handler = config.get("type")
    if handler is None:
        print("Marathon type not set in config")
        sys.exit(1)
    if handler == "bus":
        return bus.Runner()
    if handler == "gdq":
        return gdq.Runner()
    if handler == "horaro":
        return horaro.Runner()
    else:
        print(f"Marathon type {handler} unknown")
        sys.exit(1)
