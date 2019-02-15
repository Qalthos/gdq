import re

from bs4 import BeautifulSoup
import requests

from utils import ChoiceIncentive, Choice, DonationIncentive


class MarathonBase():
    incentive_url = ''

    def __init__(self):
        self.session = requests.Session()

    def read_incentives(self, stream=1):
        source = self.session.get(self.incentive_url.format(stream_index=stream)).text
        soup = BeautifulSoup(source, 'html.parser')

        incentives = {}

        money = re.compile('[$,\n]')
        for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
            game = bid.contents[3].string.strip()

            short_desc = bid.contents[1].a.string.strip()
            description = bid.contents[7].string.strip()
            current = float(money.sub('', bid.contents[9].string))
            try:
                total = float(money.sub('', bid.contents[11].string))
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
                    pass
                else:
                    options = [
                        Choice(
                            name=option.contents[1].a.string.strip(),
                            description=option.contents[7].string.strip(),
                            numeric_total=float(money.sub('', option.contents[9].string)),
                        )
                        for option in option_list
                    ]

                incentive = ChoiceIncentive(
                    description=description, short_desc=short_desc,
                    current=current, options=options,
                )

            incentives.setdefault(game, []).append(incentive)

        return incentives
