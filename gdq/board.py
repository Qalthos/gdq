#!/usr/bin/env python3
import argparse
from datetime import datetime
import sys
import time

from dateutil import tz

from gdq import events, display
from gdq import utils


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--stream_index", help="Follow only a single stream", type=int, default=0
    )
    parser.add_argument(
        "-n", "--interval", help="Time between screen refreshes", type=int, default=60
    )
    parser.add_argument(
        "stream_name", nargs="?", help="The event to follow", type=str, default="gdq",
    )
    args = parser.parse_args()

    if args.stream_name not in events.names():
        print(f"Marathon plugin {args.stream_name} not found.")
        sys.exit(1)

    marathon = events.marathon(args.stream_name)

    streams = range(1, len(marathon.stream_ids) + 1)
    if args.stream_index in streams:
        # Select only requested stream
        marathon.stream_ids = (marathon.stream_ids[args.stream_index - 1],)

    terminal = utils.Terminal()
    while True:
        try:
            # Update current time for display.
            utils.NOW = datetime.now(tz.UTC)

            # Recaclulate terminal size
            terminal.refresh()
            display.display_marathon(terminal.width, terminal.height, marathon)

            ticks = args.interval * 2
            for i in range(ticks):
                if terminal.refresh():
                    # Terminal shape has changed, skip the countdown and repaint early.
                    break

                repaint_progress = display.show_progress(i, terminal.width - 2, out_of=ticks)
                print(f"\x1b[{terminal.height}:0f{repaint_progress}", end="", flush=True)
                time.sleep(0.5)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
