from bs4 import BeautifulSoup
from dateutil import parser

from scrapers import MarathonBase
from utils import NOW, Run

EVENT = 'agdq2019'
URL = 'https://gamesdonequick.com/tracker'
RECORDS = sorted([
    # AGDQ
    (10532, "Classic GDQ (2010)"),
    (52520, "AGDQ 2011"),
    (149045, "AGDQ 2012"),
    (448425, "AGDQ 2013"),
    (1031667, "AGDQ 2014"),
    (1576085, "AGDQ 2015"),
    (1216309, "AGDQ 2016"),
    (2222791, "AGDQ 2017"),
    (2295191, "AGDQ 2018"),

    # SGDQ
    (21397, "SGDQ 2011"),
    (46279, "SGDQ 2012"),
    (257181, "SGDQ 2013"),
    (718235, "SGDQ 2014"),
    (1215601, "SGDQ 2015"),
    (1294139, "SGDQ 2016"),
    (1792342, "SGDQ 2017"),
    (2168889, "SGDQ 2018"),

    # Other
    (139879, "GDQx 2018"),
])


class GamesDoneQuick(MarathonBase):
    index_url = f'{URL}/index/{EVENT}'
    schedule_url = 'https://gamesdonequick.com/schedule'
    incentive_url = f'{URL}/bids/{EVENT}'

    def read_schedules(self):
        return [self.read_schedule(1)]

    def read_schedule(self, stream_index):
        if stream_index != 1:
            print("Index {} is not valid for this steam".format(stream_index))
            return []

        source = self.session.get(self.schedule_url).text
        soup = BeautifulSoup(source, 'html.parser')

        schedule = soup.find('table', id='runTable').tbody
        run_starts = schedule.find_all('td', class_='start-time')

        for index, row in enumerate(run_starts):
            time = parser.parse(row.text)
            if time > NOW:
                # If we havent started yet, index should still be 0
                start = max(index - 1, 0)
                return [_parse_run(td.parent) for td in run_starts[start:]]

        print("Nothing running right now ):")
        return []


def _parse_run(row):
    """Parse run metadata from schedule row."""

    row2 = row.find_next_sibling()
    if not row2:
        return None

    time = parser.parse(row.contents[1].string)

    category, _, platform = row2.contents[3].string.rpartition(' — ')
    estimate = ''.join(row2.contents[1].stripped_strings)
    hours, minutes, seconds = estimate.split(':')
    estimate = (int(hours) * 60 + int(minutes)) * 60 + int(seconds)
    run = Run(
        game=row.contents[3].string, platform=platform, category=category,
        runner=row.contents[5].string, start=time, estimate=estimate,
    )

    return run
