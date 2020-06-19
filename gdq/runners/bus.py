import argparse
from typing import Optional

from gdq.events.desert_bus import DesertBus
from gdq.events import MarathonBase


def get_marathon(event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
    if "start" in event_config:
        return DesertBus(event_config["start"])
    else:
        print(f"`start` key missing from {args.stream_name} configuration")

    return None


def get_options(parser: argparse.ArgumentParser) -> argparse.Namespace:
    return parser.parse_args()
