import csv
import urllib.parse
from datetime import datetime
from typing import List

import requests

from gdq.models import Run


def _get_resource(base_url: str, event_name: str) -> str:
    resource_url = urllib.parse.urljoin(base_url, f"/schema/{event_name}/schedule.csv")
    return requests.get(resource_url).text


def get_runs(base_url: str, event_name: str) -> List[Run]:
    runs = _get_resource(base_url, event_name).splitlines()
    reader = csv.DictReader(runs, delimiter=";")
    run_list: List[Run] = []

    for index, run in enumerate(reader):
        start_time = datetime.strptime(run["Scheduled"], "%a, %d %b %Y %H:%M:%S %z")
        run_h, run_m, run_s = run["Length"].split(":")
        estimate = (int(run_h) * 3600) + (int(run_m) * 60) + int(run_s)

        run_list.append(Run(
            run_id=index,
            game=run["Game"],
            platform=run["Console"],
            category=run["Category"],
            runners=[run["Runners"]],
            start=start_time,
            estimate=estimate,
        ))

    return run_list
