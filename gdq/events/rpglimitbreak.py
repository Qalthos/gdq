from datetime import datetime
from typing import Callable, Generator, List

import pyplugs

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import gdq_api


@pyplugs.register
class RPGLimitBreak(MarathonBase):
    url = "https://www.rpglimitbreak.com/tracker"
    event = "rpglb"
    stream_ids = ("2019",)
    records = sorted([
        (46595, "RPGLB 2015"),
        (75194.33, "RPGLB 2016"),
        (111773.56, "RPGLB 2017"),
        (164099.31, "RPGLB 2018"),
        (200339.84, "RPGLB 2019"),
    ])

    def _read_schedule(self, stream_id: str) -> List[Run]:
        return gdq_api.read_schedule(self.url, self.event + stream_id)
