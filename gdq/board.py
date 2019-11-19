#!/usr/bin/env python3
import argparse
import configparser
from datetime import datetime, timezone
from pathlib import Path
import sys

import xdg

from gdq import events, display
from gdq import utils


def refresh_event(marathon, args) -> None:
    # Update current time for display.
    utils.NOW = datetime.now(timezone.utc)

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

    config = configparser.ConfigParser()
    config_path = Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.ini"
    config.read(config_path)
    if config.has_section(args.stream_name):
        if config.has_option(args.stream_name, "url"):
            url = config[args.stream_name]["url"]
            stream_count = int(config[args.stream_name].get("concurrent_streams", 1))
            marathon = events.GDQTracker(url=url, streams=stream_count)
        else:
            print(f"Config for {args.stream_name} is missing 'url' key")
            sys.exit(1)
    elif args.stream_name in events.names():
        marathon = events.marathon(args.stream_name)
    else:
        print(f"Marathon plugin {args.stream_name} not found.")
        sys.exit(1)

    streams = range(1, len(marathon.current_events) + 1)
    if args.stream_index in streams:
        # Select only requested stream
        marathon.current_events = (marathon.current_events[args.stream_index - 1],)

    while True:
        try:
            refresh_event(marathon, args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
