from datetime import datetime
from typing import List

import pyplugs

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import gdq_api


@pyplugs.register
class ESAMarathon(MarathonBase):
    url = 'https://donations.esamarathon.com'
    event = 'esa'
    stream_ids = ('2019s1', '2019s2')
    records = sorted([
        # Original
        (58626, "ESA 2017"),
        (62783.69 + 8814.65, "ESA 2018"),
        (78255.44 + 6880.43, "ESA 2019"),

        # Winter
        (22611.53, "ESA Winter 2018"),
        (27574.68 + 2501.00, "ESA Winter 2019"),

        # UKSG
        (680.49, "UKSG Fall 2018"),
        (1348.59, "UKSG Winter 2019"),

        # Other
        (7199.62, "ESA Movember 2018"),
        (6175.67, "Twitchcon Europe 2019")
    ])

    def _read_schedule(self, stream_id: str) -> List[Run]:
        return gdq_api.read_schedule(self.url, self.event + stream_id)
