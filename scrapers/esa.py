from bs4 import BeautifulSoup
from dateutil import parser
import requests

from utils import NOW, Run

EVENT = 'ESAW2019s'
URL = 'https://donations.esamarathon.com'
TRACKER = f'{URL}/index/{EVENT}' + '{stream_index}'
BID_TRACKER = f'{URL}/bids/{EVENT}' + '{stream_index}'
SCHEDULE = 'https://esamarathon.com/schedule'
STREAMS = (1, 2)
RECORDS = sorted([
    (22611.53, "ESA Winter 2018"),
    (62783.69 + 8814.65, "ESA 2018"),
    (7199.62, "ESA Movember 2018"),

    (680.49, "UKSG Fall 2018"),
    (1348.59, "UKSG Winter 2019"),
])


def read_total():
    total = 0
    for stream in STREAMS:
        full_url = TRACKER.format(stream_index=stream)
        source = requests.get(full_url).text
        soup = BeautifulSoup(source, 'html.parser')

        total_str = soup.find('h3').small.string
        total += float(total_str.split()[2].split(' (')[0].replace(',', '')[1:])

    return total


def read_schedules():
    source = requests.get(SCHEDULE).text
    soup = BeautifulSoup(source, 'html.parser')

    schedules = soup.find_all('section', class_='schedule')
    return [_read_schedule(schedule) for schedule in schedules]


def read_schedule(stream_index):
    source = requests.get(SCHEDULE).text
    soup = BeautifulSoup(source, 'html.parser')

    schedules = soup.find_all('section', class_='schedule')
    if len(schedules) < stream_index:
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    # Align index to zero start
    stream_index -= 1
    schedule = schedules[stream_index].find_next('table').tbody
    return _read_schedule(schedule)


def _read_schedule(schedule):
    run_starts = schedule.find_all('time', class_='time-only')
    for index, row in enumerate(run_starts):
        time = parser.parse(row.attrs['datetime'])
        if time > NOW:
            # If we havent started yet, index should still be 0
            start = max(index - 1, 0)
            return [parse_run(td.parent.parent) for td in run_starts[start:]]

    print("Nothing running right now ):")
    return []


def parse_run(row):
    """Parse run metadata from schedule row."""

    time = parser.parse(row.td.time.attrs['datetime'])
    try:
        runner = ''.join(row.contents[3].p.strings)
        platform = row.contents[4].string.strip()
        runtype = row.contents[5].string.strip()
    except AttributeError:
        # Assume offline block
        runner = ''
        platform = ''
        runtype = ''
    run = Run(
        game=row.contents[1].p.string, platform=platform, runtype=runtype,
        runner=runner, start=time, str_estimate=row.contents[2].string,
    )

    return run
