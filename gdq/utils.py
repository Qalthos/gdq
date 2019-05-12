from datetime import datetime
import re

from bs4 import BeautifulSoup
from dateutil import tz
import requests


NOW: datetime = datetime.now(tz.UTC)


def short_number(number: float) -> str:
    if number > 1e6:
        return '{0:.2f}M'.format(number / 1e6)
    if number > 100e3:
        return '{0:.0f}k'.format(number / 1e3)
    if number > 10e3:
        return '{0:.1f}k'.format(number / 1e3)
    return f'{number:,.0f}'


def strip_md(string: str):
    links = re.compile(r'(?:\[(?P<name>[^]]*)]\([^)]+\))')
    return links.sub(r'\g<name>', string)


def url_to_soup(url: str) -> BeautifulSoup:
    source = requests.get(url).text
    return BeautifulSoup(source, 'html.parser')
