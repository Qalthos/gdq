from typing import Callable, Generator

from bs4 import BeautifulSoup
from dateutil import parser
import requests

from gdq.utils import NOW


def read_schedule(schedule_url: str, parse_run: Callable) -> Generator:
    source = requests.get(schedule_url).text
    soup = BeautifulSoup(source, 'html.parser')

    schedule = soup.find('table', id='runTable').tbody
    run_starts = schedule.find_all('td', class_='start-time')

    for index, row in enumerate(run_starts):
        time = parser.parse(row.text)
        if time > NOW:
            # If we havent started yet, index should still be 0
            start = max(index - 1, 0)
            for td in run_starts[start:]:
                yield parse_run(td.parent)
