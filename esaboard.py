#!/usr/bin/env python
from datetime import datetime
import re

from bs4 import BeautifulSoup
from dateutil import parser
import pytz
import requests

from utils import read_incentives, show_progress

BID_TRACKER = 'https://donations.esamarathon.com/bids/2018s1'
SCHEDULE = 'https://esamarathon.com/schedule'


def read_schedule(now, runs, incentive_dict):

    for index in range(5):
        row = runs[index]

        time = parser.parse(row.td.time.attrs['datetime'])
        if time > now:
            delta = time - now
            delta = '{0}:{1[0]:02d}:{1[1]:02d}'.format(delta.days, divmod(delta.seconds // 60, 60))
        else:
            delta = '  NOW  '
        game = row.contents[1].p.a.string
        estimate = row.contents[2].string
        runner = row.contents[3].p.a.string
        platform = row.contents[4].string.strip()
        runtype = row.contents[5].string.strip()
        print(f"{delta}\t{game} ({platform})")
        print(f"\t{runtype:<15s} {runner:<15s} {estimate}")
        for incentive in incentive_dict.get(game, []):
            if 'total' in incentive:
                percent = incentive['current'] / incentive['total'] * 100
                progress_bar = show_progress(percent)
                print('\t{0:<35s}\t{1}|${3:,.0f}\n\t  |>{2}'.format(
                    incentive['short_desc'], progress_bar, incentive['description'], incentive['total'],
                ))
            elif 'options' in incentive:
                print('\t{0:<15s}\t{1}'.format(
                    incentive['short_desc'], incentive['description'],
                ))
                for option in incentive['options']:
                    try:
                        percent = option['total'] / incentive['current'] * 100
                    except ZeroDivisionError:
                        percent = 0
                    progress_bar = show_progress(percent)
                    print('\t{0:<35s}\t{1}|${2:,.0f}'.format(option['choice'], progress_bar, option['total']))
                    if option['description']:
                        print('\t  |>{0}'.format(option['description']))


def main():
    source = requests.get(SCHEDULE).text
    soup = BeautifulSoup(source, 'html.parser')
    now = datetime.now(pytz.utc)

    schedule = soup.find('table').tbody
    run_starts = schedule.find_all('time', class_='time-only')
    for index, day_row in enumerate(run_starts):
        time = parser.parse(day_row.attrs['datetime'])
        if time > now:
            incentives = read_incentives(BID_TRACKER)
            runs = [td.parent.parent for td in run_starts[index - 1:]]
            read_schedule(now, runs, incentives)
            break
    else:
        print("Nothing running right now ):")


if __name__ == '__main__':
    main()
