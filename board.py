#!/usr/bin/env python
import shutil
import sys

from display import display_run
from scrapers.gdq import BID_TRACKER, read_schedule
from utils import read_incentives


def main():
    width, height = shutil.get_terminal_size()
    show_count = height // 3 + 1

    stream = '1'
    if len(sys.argv) > 1:
        stream = sys.argv[1]

    runs = read_schedule(stream)
    incentives = read_incentives(BID_TRACKER, stream)

    for run in runs[:show_count]:
        display_run(run, incentives, width)


if __name__ == '__main__':
    main()
