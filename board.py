#!/usr/bin/env python
import shutil
from display import display_runs, display_milestone
from scrapers.esa import BID_TRACKER, RECORDS, STREAMS, read_schedules, read_total
from utils import read_incentives


def main():
    width, height = shutil.get_terminal_size()

    incentives = {}
    for stream in STREAMS:
        incentives.update(read_incentives(BID_TRACKER, stream))

    display_milestone(read_total(), RECORDS, width)
    display_runs(read_schedules(), incentives, width, height - 1)


if __name__ == '__main__':
    main()
