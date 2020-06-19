import argparse
import sys
from types import ModuleType
from typing import Dict

from gdq.runners import bus, gdq, horaro


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


def get_runner(config: Dict[str, str]) -> ModuleType:
    handler = config.get("type")
    if handler is None:
        print("Marathon type not set in config")
        sys.exit(1)
    if handler == "bus":
        return bus
    if handler == "gdq":
        return gdq
    if handler == "horaro":
        return horaro
    else:
        print(f"Marathon type {handler} unknown")
        sys.exit(1)
