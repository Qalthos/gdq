#!/usr/bin/env python
from datetime import datetime
import re

from bs4 import BeautifulSoup
from dateutil import parser
import pytz
import requests

from utils import read_incentives, display_run

BID_TRACKER = 'https://donations.esamarathon.com/bids/2018s'
SCHEDULE = 'https://esamarathon.com/schedule'
STREAM = '1'


def read_schedule(now, runs, incentive_dict):
    for index in range(5):
        row = runs[index]
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

        display_run(run, incentive_dict)


def main():
    source = requests.get(SCHEDULE).text
    soup = BeautifulSoup(source, 'html.parser')
    now = datetime.now(pytz.utc)

    header = soup.find('h2', class_='schedule-title', string='Stream ' + STREAM)
    schedule = header.find_next('table').tbody
    run_starts = schedule.find_all('time', class_='time-only')
    for index, day_row in enumerate(run_starts):
        time = parser.parse(day_row.attrs['datetime'])
        if time > now:
            incentives = read_incentives(BID_TRACKER + STREAM)
            runs = [td.parent.parent for td in run_starts[index - 1:]]
            read_schedule(now, runs, incentives)
            break
    else:
        print("Nothing running right now ):")


if __name__ == '__main__':
    main()
