#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

import toml
import xdg

from gdq import events, utils
from gdq.runners import gdq


def refresh_event(marathon: events.MarathonBase, args: argparse.Namespace) -> bool:
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

    args = gdq.get_options()
    if args.list:
        gdq.list_events(config)
        sys.exit(0)

    marathon = gdq.get_marathon(config, args)
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
