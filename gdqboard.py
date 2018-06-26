#!/usr/bin/env python
from datetime import datetime
import re

from bs4 import BeautifulSoup
import requests

UTCFORMAT = "%Y-%m-%dT%H:%M:%SZ"


def read_schedule(now, row, incentive_dict):
    row2 = row.find_next_sibling()

    for _ in range(5):
        delta = datetime.strptime(row.contents[1].string, UTCFORMAT) - now
        delta = '{0}:{1[0]:02d}:{1[1]:02d}'.format(delta.days, divmod(delta.seconds // 60, 60))
        game = row.contents[3].string
        runner = row.contents[5].string
        estimate = row2.contents[1].string
        runtype, _, platform = row2.contents[3].string.rpartition(' — ')
        details = f"{game} ({runtype}) in {delta}\n{platform}\t{runner:<20s}\t{estimate}"
        print(details)
        for incentive in incentive_dict.get(game, []):
            percent = incentive['current'] / incentive['total'] * 100
            print('{0:03.2f}%\t{1}\n|>{2}'.format(percent, incentive['short_desc'], incentive['description']))

        try:
            row, row2 = row2.find_next_siblings()[:2]
        except ValueError:
            break


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
    for day_row in schedule.find_all('td', class_='start-time'):
        time = datetime.strptime(day_row.text, UTCFORMAT)
        if time > now:
            incentives = read_incentives()
            read_schedule(now, day_row.parent, incentives)
            break
    else:
        print("Nothing running right now ):")


if __name__ == '__main__':
    main()
