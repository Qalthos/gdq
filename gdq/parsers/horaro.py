from datetime import datetime
import shelve
from typing import Callable, List
from gdq.models import Run

import requests


def read_schedule(event: str, stream_id: str, parse_run: Callable) -> List[Run]:
    shelve_file = f'.{event}-{stream_id}.db'
    with shelve.open(shelve_file) as shelf:
        last_check = shelf.get('updated')
        runs = shelf.get('runs', [])

    headers = {}
    if last_check:
        headers['If-Modified-Since'] = datetime.strftime(last_check, '%a, %d %b %Y %H:%M:%S GMT')
    data = requests.get(f'https://horaro.org/-/api/v1/events/{event}/schedules/{stream_id}', headers=headers)

    try:
        data = data.json()['data']
    except ValueError:
        return runs

    updated = datetime.strptime(data['updated'], '%Y-%m-%dT%H:%M:%S%z')
    timezone = data['timezone']
    keys = data['columns']
    schedule = data['items']

    runs = list(parse_run(keys, schedule, timezone))
    with shelve.open(shelve_file) as shelf:
        shelf['updated'] = updated
        shelf['runs'] = runs

    return runs
