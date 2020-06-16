import argparse

from gdq.events.desert_bus import DesertBus
from gdq.events.marathon import MarathonBase


def get_marathon(config: dict, args: argparse.Namespace) -> MarathonBase:
    return DesertBus()


def get_options() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--interval", type=int, default=60,
        help="time between screen refreshes",
    )
    parser.add_argument(
        "-t", "--test", help="pretend the run started this many hours ago", type=int, default=0
    )
    parser.add_argument(
        "--oneshot", action="store_true",
        help="Run only once and then exit",
    )
    return parser.parse_args()
