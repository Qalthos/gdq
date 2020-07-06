#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import toml
import xdg
from dateutil import tz

from gdq import runners, utils
from gdq.events import MarathonBase


def refresh_event(marathon: MarathonBase, args: argparse.Namespace) -> bool:
    # Update current time for display.
    utils.update_now()

    # Recaclulate terminal size
    utils.terminal_refresh()
    marathon.refresh_all()

    if args.oneshot or not marathon.display(args):
        return False

    utils.slow_progress_bar(args.interval)
    return True


def list_events(config: dict) -> None:
    event_times: Dict[str, Tuple[datetime, Optional[datetime]]] = {}
    for name, marathon_config in config.items():
        runner = runners.get_runner(marathon_config)
        event_times[name] = runner.get_times(marathon_config)

    for name, (start, end) in sorted(event_times.items(), key=lambda x: x[1]):
        if end is None:
            end = start + timedelta(days=7)

        if utils.now < start:
            print(f"{name} will start in {start - utils.now}")
        elif end < utils.now:
            print(f"{name} (probably) finished on {end.astimezone(tz.gettz())}")
        else:
            print(f"{name} is (probably) ongoing")


def main():
    with open(Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml") as toml_file:
        config = toml.load(toml_file)

    base_parser = runners.get_base_parser()
    base_args, _extra = base_parser.parse_known_args()

    if base_args.list:
        list_events(config)
        sys.exit(0)

    event_config = config.get(base_args.stream_name)
    if event_config is None:
        print(f"No marathon named {base_args.stream_name} found")
        sys.exit(1)

    runner = runners.get_runner(event_config)
    args = runner.get_options(base_parser)

    marathon = runner.get_marathon(event_config, args)
    if marathon is None:
        sys.exit(1)

    active = True
    while active:
        try:
            active = refresh_event(marathon, args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
