#!/usr/bin/env python3
import argparse
import shutil

from display import display_runs, display_milestone
from events.rpglimitbreak import RPGLimitBreak as Marathon


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--stream_index', help="Follow only a single stream", type=int, default=0)
    args = parser.parse_args()

    width, height = shutil.get_terminal_size()

    marathon = Marathon()

    streams = range(1, len(marathon.stream_ids) + 1)
    if args.stream_index in streams:
        # Select only requested stream
        marathon.stream_ids = (marathon.stream_ids[args.stream_index - 1],)

    display_milestone(marathon.read_total(), marathon.records, width)

    schedules = marathon.read_schedules()
    incentives = marathon.read_incentives()
    display_runs(schedules, incentives, width, height - 1)


if __name__ == '__main__':
    main()
