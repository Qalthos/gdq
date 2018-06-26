#!/usr/bin/env python
from datetime import datetime
import re

from bs4 import BeautifulSoup
import requests

UTCFORMAT = "%Y-%m-%dT%H:%M:%SZ"


def read_schedule(now, runs, incentive_dict):

    for index in range(5):
        row = runs[index]
        row2 = row.find_next_sibling()

        time = datetime.strptime(row.contents[1].string, UTCFORMAT)
        if time > now:
            delta = time - now
            delta = '{0}:{1[0]:02d}:{1[1]:02d}'.format(delta.days, divmod(delta.seconds // 60, 60))
        else:
            delta = '  NOW  '
        game = row.contents[3].string
        runner = row.contents[5].string
        estimate = ''.join(row2.contents[1].stripped_strings)
        runtype, _, platform = row2.contents[3].string.rpartition(' — ')
        details = f"{delta}\t{game} ({platform})\n\t{runtype}\t{runner:<20s}\t{estimate}"
        print(details)
        for incentive in incentive_dict.get(game, []):
            percent = incentive['current'] / incentive['total'] * 100
            print('\t{0:03.2f}%\t{1}\n\t|>{2}'.format(percent, incentive['short_desc'], incentive['description']))


def read_incentives():
    source = requests.get('https://gamesdonequick.com/tracker/bids/sgdq2018').text
    soup = BeautifulSoup(source, 'html.parser')

    incentives = {}

    money = re.compile('[$,\n]')
    bids = soup.find_all('tr', class_='small')
    for bid in bids:
        game = bid.contents[3].string.strip()
        gamedata = dict(
            short_desc=bid.contents[1].a.string.strip(),
            description=bid.contents[7].string.strip(),
        )
        gamedata['current'] = float(money.sub('', bid.contents[9].string))
        try:
            gamedata['total'] = float(money.sub('', bid.contents[11].string))
        except ValueError:
            # Handle bid wars later
            continue

        incentives.setdefault(game, []).append(gamedata)

    return incentives


def main():
    source = requests.get('https://gamesdonequick.com/schedule').text
    soup = BeautifulSoup(source, 'html.parser')
    now = datetime.utcnow()

    schedule = soup.find('table', id='runTable').tbody
    run_starts = schedule.find_all('td', class_='start-time')
    for index, day_row in enumerate(run_starts):
        time = datetime.strptime(day_row.text, UTCFORMAT)
        if time > now:
            incentives = read_incentives()
            runs = [td.parent for td in run_starts[index-1:]]
            read_schedule(now, runs, incentives)
            break
    else:
        print("Nothing running right now ):")


if __name__ == '__main__':
    main()
