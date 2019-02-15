from bs4 import BeautifulSoup
from dateutil import parser
import requests

from utils import NOW, Run

EVENT = 'rpglb2018'
URL = 'https://www.rpglimitbreak.com/tracker'
TRACKER = f'{URL}/index/{EVENT}'
BID_TRACKER = f'{URL}/bids/{EVENT}'
SCHEDULE = f'{URL}/runs/{EVENT}'
RECORDS = sorted([
    (46595, "RPGLB 2015"),
    (75194.33, "RPGLB 2016"),
    (111773.56, "RPGLB 2017"),
    (164099.31, "RPGLB 2018"),
])


def read_total():
    source = requests.get(TRACKER).text
    soup = BeautifulSoup(source, 'html.parser')

    total = soup.find('h2').small.string
    total = total.split()[2].split(' (')[0].replace(',', '')[1:]

    return float(total)


def read_schedule(stream_index=1):
    if stream_index != 1:
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    source = requests.get(SCHEDULE).text
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
        platform='', category='', start=start, str_estimate=estimate,
    )

    return run
