#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

import xdg
import toml

from gdq import events, display, utils


def refresh_event(marathon, args) -> None:
    # Update current time for display.
    utils.update_now()

    # Recaclulate terminal size
    utils.terminal_refresh()
    marathon.refresh_all()

    display.display_marathon(utils.term_width, utils.term_height, marathon, args)

    utils.slow_progress_bar(args.interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--stream_index", help="Follow only a single stream", type=int, default=0
    )
    parser.add_argument(
        "-n", "--interval", help="Time between screen refreshes", type=int, default=60
    )
    parser.add_argument(
        "-p", "--min-percent", help="Minimum percent before displaying choice incentive.", type=int, default=5
    )
    parser.add_argument(
        "-o", "--min-options", help="Minimum number of choices before applying percent cutoff.", type=int, default=5
    )
    parser.add_argument(
        "--hide-completed", help="Hide completed donation incentives.", action="store_true"
    )
    parser.add_argument(
        "stream_name", nargs="?", help="The event to follow", type=str, default="gdq",
    )
    args = parser.parse_args()

    with open(Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml") as toml_file:
        config = toml.load(toml_file)

    if stream_options := config.get(args.stream_name):
        if url := stream_options.get("url"):
            marathon = events.GDQTracker(url=url)
        else:
            print(f"Config for {args.stream_name} is missing 'url' key")
            sys.exit(1)
    elif args.stream_name in events.names():
        marathon = events.marathon(args.stream_name)
    else:
        print(f"Marathon plugin {args.stream_name} not found.")
        sys.exit(1)

    while True:
        try:
            refresh_event(marathon, args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
