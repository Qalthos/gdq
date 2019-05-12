#!/usr/bin/env python3
import argparse
import shutil
import sys

from gdq import events, display


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--stream_index", help="Follow only a single stream", type=int, default=0
    )
    parser.add_argument(
        "stream_name", nargs="?", help="The event to follow", type=str, default="rpglimitbreak",
    )
    args = parser.parse_args()

    width, height = shutil.get_terminal_size()

    if args.stream_name not in events.names():
        print(f"Marathon plugin {args.stream_name} not found.")
        sys.exit(1)

    marathon = events.marathon(args.stream_name)

    streams = range(1, len(marathon.stream_ids) + 1)
    if args.stream_index in streams:
        # Select only requested stream
        marathon.stream_ids = (marathon.stream_ids[args.stream_index - 1],)

    print(display.format_milestone(marathon, width))

    rendered_text = display.format_runs(marathon, width, height - 1)
    for line in rendered_text:
        print(line)


if __name__ == "__main__":
    main()
