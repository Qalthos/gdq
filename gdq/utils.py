from datetime import datetime
import re
import shutil

from bs4 import BeautifulSoup
from dateutil import tz
import requests


NOW: datetime = datetime.now(tz.UTC)


def short_number(number: float) -> str:
    if number > 1e6:
        return "{0:.2f}M".format(number / 1e6)
    if number > 100e3:
        return "{0:.0f}k".format(number / 1e3)
    if number > 10e3:
        return "{0:.1f}k".format(number / 1e3)
    return f"{number:,.0f}"


def strip_md(string: str):
    links = re.compile(r"(?:\[(?P<name>[^]]*)]\([^)]+\))")
    return links.sub(r"\g<name>", string)


def url_to_soup(url: str) -> BeautifulSoup:
    source = requests.get(url).text
    return BeautifulSoup(source, "html.parser")


class Terminal:
    width: int = 0
    height: int = 0

    def __init__(self):
        self.refresh()

    def refresh(self) -> bool:
        """Refresh terminal geometry

        Returns True if geometry has changed, False otherwise.
        """
        geom = shutil.get_terminal_size()
        if geom != (self.width, self.height):
            self.width, self.height = geom
            return True
        return False
