#!/usr/bin/env python
from datetime import datetime
import sys

from bs4 import BeautifulSoup
from dateutil import parser
import pytz
import requests

from utils import read_incentives, display_run

BID_TRACKER = 'https://donations.esamarathon.com/bids/2018s'
SCHEDULE = 'https://esamarathon.com/schedule'


def read_schedule(schedule_url, stream_index=1):
    source = requests.get(schedule_url).text
    soup = BeautifulSoup(source, 'html.parser')

    header = soup.find('h2', class_='schedule-title', string='Stream ' + stream)
    if header is None
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    schedule = header.find_next('table').tbody
    run_starts = schedule.find_all('time', class_='time-only')

    now = datetime.now(pytz.utc)
    for index, day_row in enumerate(run_starts):
        time = parser.parse(day_row.attrs['datetime'])
        if time > now:
            return [parse_run(td.parent.parent) for td in run_starts[index - 1:]]
    else:
        print("Nothing running right now ):")
        return []


def parse_run(row):
    """Parse run metadata from schedule row."""

    run = dict(delta='  NOW  ')

    time = parser.parse(row.td.time.attrs['datetime'])
    if time > now:
        delta = time - now
        run['delta'] = '{0}:{1[0]:02d}:{1[1]:02d}'.format(delta.days, divmod(delta.seconds // 60, 60))

    run['game'] = row.contents[1].p.a.string
    run['estimate'] = row.contents[2].string
    try:
        run['runner'] = row.contents[3].p.a.string
        run['platform'] = row.contents[4].string.strip()
        run['runtype'] = row.contents[5].string.strip()
    except AttributeError:
        # Assume offline block
        run['runner'] = ''
        run['platform'] = ''
        run['runtype'] = ''

    return run


def main():
    stream = '1'
    if len(sys.argv) > 1:
        stream = sys.argv[1]

    runs = read_schedule(SCHEDULE, stream)
    incentives = read_incentives(BID_TRACKER)

    for run in runs[:5]:
        display_run(run, incentives)


if __name__ == '__main__':
    main()
