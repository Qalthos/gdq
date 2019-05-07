#!/usr/bin/env python3
import argparse
import shutil

import display
import events

# Prime the plugin cache for `call()`
from events import rpglimitbreak


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--stream_index", help="Follow only a single stream", type=int, default=0
    )
    args = parser.parse_args()

    width, height = shutil.get_terminal_size()

    marathon = events.call("RPGLimitBreak")

    streams = range(1, len(marathon.stream_ids) + 1)
    if args.stream_index in streams:
        # Select only requested stream
        marathon.stream_ids = (marathon.stream_ids[args.stream_index - 1],)

    print(display.format_milestone(marathon, width))

    # Uhhh, waiting for walrus operator?
    [print(line) for line in display.format_runs(marathon, width, height - 1)]


if __name__ == "__main__":
    main()
