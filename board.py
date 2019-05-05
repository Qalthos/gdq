#!/usr/bin/env python3
import argparse
import shutil
from display import display_runs, display_milestone
from scrapers.rpglimitbreak import RPGLimitBreak as Marathon, RECORDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--stream_index', help="Follow only a single stream", type=int, default=0)
    args = parser.parse_args()

    width, height = shutil.get_terminal_size()

    marathon = Marathon()
    schedules = marathon.read_schedules()
    streams = range(1, len(schedules) + 1)

    display_milestone(marathon.read_total(streams), RECORDS, width)

    if args.stream_index in streams:
        # Select only requested stream
        schedules = [schedules[args.stream_index - 1]]
        streams = (args.stream_index,)

    incentives = {}
    for stream in streams:
        incentives.update(marathon.read_incentives(stream))

    display_runs(schedules, incentives, width, height - 1)


if __name__ == '__main__':
    main()
