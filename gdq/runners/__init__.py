import argparse
import sys
from typing import Dict

from gdq.runners import bus, gdq, horaro
from gdq.runners.base import RunnerBase


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
        "--list", action="store_true",
        help="List all known events instead of tracking one",
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
