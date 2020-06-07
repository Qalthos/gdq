#!/usr/bin/env python3
import argparse
from datetime import timedelta
from pathlib import Path
import sys
import time

import toml
import xdg

from gdq import events, utils
from gdq.events.gdqbase import GDQTracker


def refresh_event(marathon: events.MarathonBase, args: argparse.Namespace) -> bool:
    marathon.refresh_all()

    resolution = 0.10
    ticks = int(args.interval / resolution)

    # Don't bother updating the progress bar more often than necessary
    if ticks > utils.term_width * 8:
        ticks = utils.term_width * 8
        resolution = args.interval / ticks

    for i in range(ticks):
        utils.terminal_refresh()
        utils.update_now()
        if not marathon.display(args):
            return False
        if args.oneshot:
            return False

        repaint_progress = utils.progress_bar(0, i, ticks, width=utils.term_width)
        print(f"\x1b[{utils.term_height}H{repaint_progress}", end="", flush=True)
        time.sleep(resolution)

    return True


def list_events(config: dict) -> None:
    for key, marathon in config.items():
        if "url" in marathon:
            marathon = GDQTracker(url=marathon["url"])
            marathon.read_events()
            start = marathon.current_event.start_time
            if start > utils.now:
                print(f"{key} will start in {start - utils.now}")
            elif start > utils.now - timedelta(days=7):
                print(f"{key} is (probably) ongoing")
            else:
                print(f"{key} (probably) finished on {start + timedelta(days=7)}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--stream_index", help="follow only a single stream", type=int, default=1
    )
    parser.add_argument(
        "-n", "--interval", help="time between screen refreshes", type=int, default=60
    )
    parser.add_argument(
        "-p", "--min-percent", help="Minimum percent before displaying choice incentive.", type=int, default=5
    )
    parser.add_argument(
        "-o", "--min-options", help="Minimum number of choices before applying percent cutoff.", type=int, default=5
    )
    parser.add_argument(
        "-w", "--min-width", help="Minimum width for option description names", type=int, default=16
    )
    parser.add_argument(
        "-s", "--split-pane", action="store_true",
        help="Display a split view with schedule on the left and incentives on the right"
    )
    parser.add_argument(
        "-x", "--extended-header", action="store_true", help="Show expanded information in the header"
    )
    parser.add_argument(
        "--hide-completed", help="Hide completed donation incentives.", action="store_true"
    )
    parser.add_argument(
        "--hide-basic", help="Hide runs with no active incentives", action="store_true"
    )
    parser.add_argument(
        "--hide-incentives", help="Hide run incentives", action="store_true"
    )
    parser.add_argument(
        "--oneshot", help="Run only once and then exit", action="store_true"
    )
    parser.add_argument(
        "--list", help="Show known marathons and status", action="store_true"
    )
    parser.add_argument(
        "stream_name", nargs="?", help="The event to follow", type=str, default="gdq",
    )
    args = parser.parse_args()

    with open(Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml") as toml_file:
        config = toml.load(toml_file)

    if args.list:
        list_events(config)

    if config.get(args.stream_name):
        if config[args.stream_name].get("url"):
            marathon = GDQTracker(url=config[args.stream_name]["url"], stream_index=-args.stream_index)
        else:
            print(f"Config for {args.stream_name} is missing 'url' key")
            sys.exit(1)
    elif args.stream_name in events.names():
        marathon = events.marathon(args.stream_name)
    else:
        print(f"Marathon plugin {args.stream_name} not found.")
        sys.exit(1)

    active = True
    while active:
        try:
            active = refresh_event(marathon, args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
