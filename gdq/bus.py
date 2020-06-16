#!/usr/bin/env python3
import argparse

from gdq import events, utils
from gdq.events.desert_bus import DesertBus
from gdq.runners import bus


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
    config = {}

    args = bus.get_options()

    marathon = bus.get_marathon(config, args)

    active = True
    while active:
        try:
            active = refresh_event(marathon, args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
