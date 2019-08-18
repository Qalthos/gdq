from datetime import datetime
from typing import List

import requests

from gdq.models import Run


def read_schedule(base_url: str, event_id: str) -> List[Run]:
    api_base = "{}/api/v1/search/?type=".format(base_url)
    schedule_url = "{}run&eventshort={}".format(api_base, event_id)

    runs = requests.get(schedule_url).json()
    for run in runs:
        run = run["fields"]
        # TODO: Probably some wrangling needed here.
        # keys available: starttime, endtime, setup_time, run_time
        start_time = datetime.strptime(run["starttime"], "%Y-%m-%dT%H:%M:%S%z")
        end_time = datetime.strptime(run["endtime"], "%Y-%m-%dT%H:%M:%S%z")
        estimate = (end_time - start_time).total_seconds()
        yield Run(
            game=run["name"],
            platform=run["console"],
            category=run["category"],
            # TODO: pull directly
            runner=run["deprecated_runners"],
            start=start_time,
            estimate=estimate,
        )
