from bs4 import BeautifulSoup
from dateutil import parser

from scrapers import MarathonBase
from utils import NOW, Run

EVENT = 'esaw2019s'
URL = 'https://donations.esamarathon.com'
RECORDS = sorted([
    (22611.53, "ESA Winter 2018"),
    (62783.69 + 8814.65, "ESA 2018"),
    (7199.62, "ESA Movember 2018"),

    (680.49, "UKSG Fall 2018"),
    (1348.59, "UKSG Winter 2019"),
])


class ESAMarathon(MarathonBase):
    index_url = f'{URL}/index/{EVENT}' + '{stream_index}'
    schedule_url = 'https://esamarathon.com/schedule'
    incentive_url = f'{URL}/bids/{EVENT}' + '{stream_index}'

    def read_total(self, streams):
        total = 0
        for stream in streams:
            full_url = self.index_url.format(stream_index=stream)
            source = self.session.get(full_url).text
            soup = BeautifulSoup(source, 'html.parser')

            total_str = soup.find('h3').small.string
            total += float(total_str.split()[2].split(' (')[0].replace(',', '')[1:])

        return total

    def read_schedules(self):
        source = self.session.get(self.schedule_url).text
        soup = BeautifulSoup(source, 'html.parser')

        schedules = soup.find_all('section', class_='schedule')
        return [_read_schedule(schedule) for schedule in schedules]

    def read_schedule(self, stream_index):
        source = self.session.get(self.schedule_url).text
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
            return [_parse_run(td.parent.parent) for td in run_starts[start:]]

    print("Nothing running right now ):")
    return []


def _parse_run(row):
    """Parse run metadata from schedule row."""

    time = parser.parse(row.td.time.attrs['datetime'])
    try:
        runner = ''.join(row.contents[3].p.strings)
        platform = row.contents[4].string.strip()
        category = row.contents[5].string.strip()
    except AttributeError:
        # Assume offline block
        runner = ''
        platform = ''
        category = ''
    run = Run(
        game=row.contents[1].p.string, platform=platform, category=category,
        runner=runner, start=time, str_estimate=row.contents[2].string,
    )

    return run
