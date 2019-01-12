from bs4 import BeautifulSoup
from dateutil import parser
import requests

from utils import NOW, Run

EVENT = 'agdq2019'
BID_TRACKER = f'https://gamesdonequick.com/tracker/bids/{EVENT}'


def read_schedule(stream_index='1'):
    if stream_index != '1':
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    schedule = 'https://gamesdonequick.com/schedule'
    source = requests.get(schedule).text
    soup = BeautifulSoup(source, 'html.parser')

    schedule = soup.find('table', id='runTable').tbody
    run_starts = schedule.find_all('td', class_='start-time')

    for index, row in enumerate(run_starts):
        time = parser.parse(row.text)
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
    # Strip seconds off estimate
    estimate = estimate.rsplit(':', 1)[0]
    run = Run(
        game=row.contents[3].string, platform=platform, runtype=runtype,
        runner=row.contents[5].string, start=time, str_estimate=estimate,
    )

    return run
