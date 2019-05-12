from typing import List, Optional

from dateutil import parser
import pyplugs

from gdq.events import MarathonBase
from gdq.parsers import gdq_schedule
from gdq.models import Run


def parse_data(row) -> Optional[Run]:
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


@pyplugs.register
class GamesDoneQuick(MarathonBase):
    url = 'https://gamesdonequick.com/tracker'
    event = 'agdq'
    stream_ids = ('2019',)
    records = sorted([
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
        (2425791, "AGDQ 2019"),

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

    def _read_schedule(self, stream_id: str) -> List[Run]:
        schedule_url = 'https://gamesdonequick.com/schedule'
        return list(gdq_schedule.read_schedule(schedule_url, parse_data))
