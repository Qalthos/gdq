import re
from typing import Callable, Pattern

from bs4 import BeautifulSoup
import requests

from gdq.models import ChoiceIncentive, Choice, DonationIncentive


def read_incentives(base_url: str, event: dict, money_parser: Callable):
    """Scrapes GDQ-derived donation trackers for incentives."""
    source = requests.get("{}/bids/{}".format(base_url, event)).text
    soup = BeautifulSoup(source, 'html.parser')

    incentives = {}

    for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
        game = bid.contents[3].string.strip()

        short_desc = bid.contents[1].a.string.strip()
        description = bid.contents[7].string.strip()
        current = money_parser(bid.contents[9].string)
        try:
            total = money_parser(bid.contents[11].string)
            # noinspection PyArgumentList
            incentive = DonationIncentive(
                description=description, short_desc=short_desc,
                current=current, numeric_total=total,
            )
        except ValueError:
            # Assume bid war
            try:
                option_list = bid.find_next_sibling('tr').find('tbody').find_all('tr')
            except AttributeError:
                # bid war with no options (e.g. filename with no bids yet)
                option_list = []

            options = [
                Choice(
                    name=option.contents[1].a.string.strip(),
                    description=option.contents[7].string.strip(),
                    numeric_total=money_parser(option.contents[9].string),
                )
                for option in option_list
            ]

            # noinspection PyArgumentList
            incentive = ChoiceIncentive(
                description=description, short_desc=short_desc,
                current=current, options=options,
            )

        incentives.setdefault(game, []).append(incentive)

    return incentives
