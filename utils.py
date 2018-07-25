import re

from bs4 import BeautifulSoup
import requests


def show_progress(percent, width=30):
    chars = " ▏ ▎ ▍ ▌ ▋ ▊ ▉ █"

    blocks = int(percent * width // 100)
    fraction = int(percent * width % 100 // 12.5)
    # print(fraction)

    return chars[-1] * blocks + chars[fraction] + ' ' * (width - blocks - 1)


def read_incentives(incentive_url):
    source = requests.get(incentive_url).text
    soup = BeautifulSoup(source, 'html.parser')

    incentives = {}

    money = re.compile('[$,\n]')
    for bid in soup.find('table').find_all('tr', class_='small', recursive=False):
        game = bid.contents[3].string.strip()
        gamedata = dict(
            short_desc=bid.contents[1].a.string.strip(),
            description=bid.contents[7].string.strip(),
        )
        gamedata['current'] = float(money.sub('', bid.contents[9].string))
        try:
            gamedata['total'] = float(money.sub('', bid.contents[11].string))
        except ValueError:
            # Assume bid war
            try:
                option_list = bid.find_next_sibling('tr').find('tbody').find_all('tr')
            except AttributeError:
                # bid war with no options (e.g. filename with no bids yet)
                pass
            else:
                gamedata['options'] = [
                    dict(
                        choice=option.contents[1].a.string.strip(),
                        description=option.contents[7].string.strip(),
                        total=float(money.sub('', option.contents[9].string)),
                    )
                    for option in option_list
                ]

        incentives.setdefault(game, []).append(gamedata)

    return incentives
