from bs4 import BeautifulSoup
from dateutil import parser
import requests

from utils import NOW, Run

EVENT = 'rpglb2018'
BID_TRACKER = f'https://www.rpglimitbreak.com/tracker/bids/{EVENT}'


def read_schedule(stream_index=1):
    if stream_index != 1:
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    schedule = f'https://www.rpglimitbreak.com/tracker/runs/{EVENT}'
    source = requests.get(schedule).text
    soup = BeautifulSoup(source, 'html.parser')

    schedule = soup.find('table')
    run_starts = schedule.find_all('span', class_='datetime')[::2]

    for index, row in enumerate(run_starts):
        time = parser.parse(row.text)
        if time > NOW:
            # If we havent started yet, index should still be 0
            start = max(index - 1, 0)
            return [parse_run(span.parent.parent) for span in run_starts[start:]]

    print("Nothing running right now ):")
    return []


def parse_run(row):
    """Parse run metadata from schedule row."""

    start = parser.parse(row.contents[7].span.string)
    end = parser.parse(row.contents[9].span.string)

    estimate = end - start
    hours, minutes = divmod(estimate.seconds, 3600)
    minutes //= 60
    estimate = f'{hours}:{minutes:02d}'

    run = Run(
        game=row.contents[1].a.string, runner=row.contents[3].string.strip(),
        platform='', runtype='', start=start, str_estimate=estimate,
    )

    return run
