#!/usr/bin/env python
import argparse
import shutil
from display import display_run, display_milestone
from scrapers.esa import BID_TRACKER, RECORDS, read_schedule, read_total
from utils import read_incentives


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--stream_index', help="Stream index to follow", type=int, default=1)
    args = parser.parse_args()

    width, height = shutil.get_terminal_size()
    show_count = height // 3 + 1

    runs = read_schedule(args.stream_index)
    incentives = read_incentives(BID_TRACKER, args.stream_index)

    total = read_total()
    display_milestone(total, RECORDS, width)
    for run in runs[:show_count]:
        display_run(run, incentives, width)


if __name__ == '__main__':
    main()
