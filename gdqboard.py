#!/usr/bin/env python
from datetime import datetime
import re

from bs4 import BeautifulSoup
import requests

from utils import read_incentives, display_run

UTCFORMAT = "%Y-%m-%dT%H:%M:%SZ"
BID_TRACKER = 'https://gamesdonequick.com/tracker/bids/sgdq2018'
SCHEDULE = 'https://gamesdonequick.com/schedule'


def read_schedule(now, runs, incentive_dict):
    for index in range(5):
        row = runs[index]
        row2 = row.find_next_sibling()
        if not row2:
            break
        run = dict(delta='  NOW  ')

        time = datetime.strptime(row.contents[1].string, UTCFORMAT)
        if time > now:
            delta = time - now
            run['delta'] = '{0}:{1[0]:02d}:{1[1]:02d}'.format(delta.days, divmod(delta.seconds // 60, 60))

        run['game'] = row.contents[3].string
        run['runner'] = row.contents[5].string
        run['estimate'] = ''.join(row2.contents[1].stripped_strings)
        run['runtype'], _, run['platform'] = row2.contents[3].string.rpartition(' — ')

        display_run(run, incentive_dict)


def main():
    source = requests.get(SCHEDULE).text
    soup = BeautifulSoup(source, 'html.parser')
    now = datetime.utcnow()

    schedule = soup.find('table', id='runTable').tbody
    run_starts = schedule.find_all('td', class_='start-time')
    for index, day_row in enumerate(run_starts):
        time = datetime.strptime(day_row.text, UTCFORMAT)
        if time > now:
            incentives = read_incentives(BID_TRACKER)
            runs = [td.parent for td in run_starts[index - 1:]]
            read_schedule(now, runs, incentives)
            break
    else:
        print("Nothing running right now ):")


if __name__ == '__main__':
    main()
