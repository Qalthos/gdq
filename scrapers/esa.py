from bs4 import BeautifulSoup
from dateutil import parser
import requests

from utils import NOW, Run

EVENT = '2018s'
BID_TRACKER = f'https://donations.esamarathon.com/bids/{EVENT}' + '{stream_index}'
SCHEDULE = 'https://esamarathon.com/schedule'
# BID_TRACKER = 'https://bsgmarathon.com/tracker/bids/BSG2018'
# SCHEDULE = 'https://www.speedrun.com/bsg2018/schedule'


def read_schedule(stream_index=1):
    source = requests.get(SCHEDULE).text
    soup = BeautifulSoup(source, 'html.parser')

    stream_index = int(stream_index)
    schedules = soup.find_all('section', class_='schedule')
    if len(schedules) < stream_index:
        print("Index {} is not valid for this steam".format(stream_index))
        return []

    # Align index to zero start
    stream_index -= 1
    schedule = schedules[stream_index].find_next('table').tbody
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
        runner = row.contents[3].p.string
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
