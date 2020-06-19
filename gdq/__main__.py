#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

import toml
import xdg

from gdq.events import MarathonBase
from gdq import runners, utils


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


def main():
    with open(Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml") as toml_file:
        config = toml.load(toml_file)

    base_parser = runners.get_base_parser()
    base_args, _extra = base_parser.parse_known_args()

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
