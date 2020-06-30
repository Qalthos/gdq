import argparse
from typing import Optional

from gdq.events import MarathonBase
from gdq.events.horarobase import HoraroSchedule


def get_marathon(event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
    try:
        return HoraroSchedule(
            group=event_config["group"],
            event=event_config["event"],
            key_map=event_config["keys"],
        )
    except KeyError:
        print(f"Incomplete configuration for {args.stream_name}")

    return None


def get_options(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument(
        "-i", "--stream_index", type=int, default=1,
        help="follow only a single stream",
    )
    return parser.parse_args()
