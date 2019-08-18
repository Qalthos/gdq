from typing import List

import pyplugs

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import gdq_api


@pyplugs.register
class GamesDoneQuick(MarathonBase):
    url = 'https://gamesdonequick.com/tracker'
    event = 'GDQX'
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
        (2425790, "AGDQ 2019"),

        # SGDQ
        (21397, "SGDQ 2011"),
        (46279, "SGDQ 2012"),
        (257181, "SGDQ 2013"),
        (718235, "SGDQ 2014"),
        (1215601, "SGDQ 2015"),
        (1294139, "SGDQ 2016"),
        (1792342, "SGDQ 2017"),
        (2168913, "SGDQ 2018"),
        (3005839, "SGDQ 2019"),

        # Other
        (139879, "GDQx 2018"),
    ])

    def _read_schedule(self, stream_id: str) -> List[Run]:
        return gdq_api.read_schedule(self.url, self.event + stream_id)
