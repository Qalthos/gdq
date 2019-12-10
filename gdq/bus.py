#!/usr/bin/env python3
import argparse

from gdq import utils
from gdq.events.bus import DesertBus


def refresh_bus(marathon: DesertBus, args: argparse.Namespace) -> bool:
    # Update current time for display.
    utils.update_now()

    # Recaclulate terminal size
    utils.terminal_refresh()
    marathon.refresh_all()

    if not marathon.display():
        return False

    utils.slow_progress_bar(args.interval)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--interval", help="time between screen refreshes", type=int, default=60
    )
    args = parser.parse_args()

    marathon = DesertBus()

    active = True
    while active:
        try:
            active = refresh_bus(marathon, args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
