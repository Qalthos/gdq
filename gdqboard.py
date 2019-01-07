#!/usr/bin/env python
import shutil

from bs4 import BeautifulSoup
from dateutil import parser
import requests

from utils import NOW, Run, read_incentives, display_run

BID_TRACKER = 'https://gamesdonequick.com/tracker/bids/agdq2019'
SCHEDULE = 'https://gamesdonequick.com/schedule'


def read_schedule(schedule_url, stream_index=1):
    if stream_index != 1:
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    source = requests.get(schedule_url).text
    soup = BeautifulSoup(source, 'html.parser')

    schedule = soup.find('table', id='runTable').tbody
    run_starts = schedule.find_all('td', class_='start-time')

    for index, day_row in enumerate(run_starts):
        time = parser.parse(day_row.text)
        if time > NOW:
            # If we havent started yet, index should still be 0
            start = max(index - 1, 0)
            return [parse_run(td.parent) for td in run_starts[start:]]

    print("Nothing running right now ):")
    return []


def parse_run(row):
    """Parse run metadata from schedule row."""

    row2 = row.find_next_sibling()
    if not row2:
        return None

    time = parser.parse(row.contents[1].string)

    runtype, _, platform = row2.contents[3].string.rpartition(' — ')
    estimate = ''.join(row2.contents[1].stripped_strings)
    run = Run(
        game=row.contents[3].string, platform=platform, runtype=runtype,
        runner=row.contents[5].string, start=time, str_estimate=estimate,
    )

    return run


def main():
    width, height = shutil.get_terminal_size()
    show_count = height // 3 + 1

    runs = read_schedule(SCHEDULE)
    incentives = read_incentives(BID_TRACKER)

    for run in runs[:show_count]:
        display_run(run, incentives, width)


if __name__ == '__main__':
    main()
