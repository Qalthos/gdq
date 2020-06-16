import argparse
from datetime import timedelta
from typing import Optional

from gdq import utils
from gdq.events.gdqbase import GDQTracker
from gdq.events import MarathonBase


def get_marathon(event_config: dict, args: argparse.Namespace) -> Optional[MarathonBase]:
    if "url" in event_config:
        return GDQTracker(
            url=event_config["url"],
            stream_index=-args.stream_index,
        )
    else:
        print(f"`url` key missing from {args.stream_name} configuration")

    return None


def get_options(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument(
        "-d", "--delta-total", type=float, default=0,
        help="Offset to subtract from event total to reconcile discrepencies",
    )
    parser.add_argument(
        "-i", "--stream_index", type=int, default=1,
        help="follow only a single stream",
    )
    parser.add_argument(
        "-o", "--min-options", type=int, default=5,
        help="Minimum number of choices before applying percent cutoff.",
    )
    parser.add_argument(
        "-p", "--min-percent", type=int, default=5,
        help="Minimum percent before displaying choice incentive.",
    )
    parser.add_argument(
        "-s", "--split-pane", action="store_true",
        help="Display a split view with schedule on the left and incentives on the right",
    )
    parser.add_argument(
        "-w", "--min-width", type=int, default=16,
        help="Minimum width for option description names",
    )
    parser.add_argument(
        "-x", "--extended-header", action="store_true",
        help="Show expanded information in the header",
    )
    parser.add_argument(
        "--hide-completed", action="store_true",
        help="Hide completed donation incentives.",
    )
    parser.add_argument(
        "--hide-basic", action="store_true",
        help="Hide runs with no active incentives",
    )
    parser.add_argument(
        "--hide-incentives", action="store_true",
        help="Hide run incentives",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Show known marathons and status",
    )
    return parser.parse_args()


def list_events(config: dict) -> None:
    for key, marathon in config.items():
        if marathon.get("type") == "gdq" and "url" in marathon:
            marathon = GDQTracker(url=marathon["url"])
            marathon.read_events()
            start = marathon.current_event.start_time
            if start > utils.now:
                print(f"{key} will start in {start - utils.now}")
            elif start > utils.now - timedelta(days=7):
                print(f"{key} is (probably) ongoing")
            else:
                print(f"{key} (probably) finished on {start + timedelta(days=7)}")
