#!/usr/bin/env python
import argparse
import shutil
from display import display_runs, display_milestone
from scrapers.esa import BID_TRACKER, RECORDS, STREAMS, read_schedules, read_total
from utils import read_incentives


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--stream_index', help="Follow only a single stream", type=int, default=0)
    args = parser.parse_args()

    width, height = shutil.get_terminal_size()

    schedules = read_schedules(SCHEDULE)
    streams = range(1, len(schedules) + 1)
    if args.stream_index in streams:
        # Select only requested stream
        schedules = [schedules[args.stream_index - 1]]
        streams = (args.stream_index,)

    incentives = {}
    for stream in streams:
        incentives.update(read_incentives(BID_TRACKER, stream))

    display_milestone(read_total(), RECORDS, width)
    display_runs(schedules, incentives, width, height - 1)


if __name__ == '__main__':
    main()
