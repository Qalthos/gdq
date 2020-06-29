import shelve
from datetime import datetime
from pathlib import Path
from typing import Dict
from typing import List

import requests
import xdg
from dateutil import tz

from gdq.models import Run


def read_schedule(event: str, stream_id: str, key_map: Dict[str, str]) -> List[Run]:
    shelve_file = Path(xdg.XDG_CACHE_HOME) / "gdq" / f"{event}-{stream_id}.db"
    if not shelve_file.exists():
        shelve_file.parent.mkdir(parents=True, exist_ok=True)
        last_check = None
        runs = []
    else:
        with shelve.open(str(shelve_file)) as shelf:
            last_check = shelf.get('updated')
            runs = shelf.get('runs', [])

    headers = {}
    if last_check:
        headers['If-Modified-Since'] = datetime.strftime(last_check, '%a, %d %b %Y %H:%M:%S GMT')
    data = requests.get(
        f'https://horaro.org/-/api/v1/events/{event}/schedules/{stream_id}', headers=headers
    )

    try:
        data_dict = data.json()['data']
    except ValueError:
        return runs

    updated = datetime.strptime(data_dict['updated'], '%Y-%m-%dT%H:%M:%S%z')
    timezone = tz.gettz(data_dict['timezone'])
    keys = data_dict['columns']
    schedule = data_dict['items']

    runs = []
    attr_to_index = {
        key: keys.index(value) for key, value in key_map.items()
    }
    runners = attr_to_index.pop("runners", "")
    for index, run in enumerate(schedule):
        runs.append(Run(
            run_id=index,
            runners=[run["data"][runners]],
            start=datetime.fromtimestamp(run["scheduled_t"]).astimezone(timezone),
            estimate=run["length_t"],
            **{key: run["data"][value] for key, value in attr_to_index.items()},
        ))

    with shelve.open(str(shelve_file)) as shelf:
        shelf['updated'] = updated
        shelf['runs'] = runs

    return runs
