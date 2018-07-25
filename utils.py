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


def display_run(run, incentive_dict):
    print("{delta}\t{game} ({platform})".format(**run))
    print("\t{runtype:<15s} {runner:<15s} {estimate}".format(**run))
    for incentive in incentive_dict.get(run['game'], []):
        if 'total' in incentive:
            percent = incentive['current'] / incentive['total'] * 100
            progress_bar = show_progress(percent)
            print('\t{0:<35s}\t{1}|${3:,.0f}\n\t  |>{2}'.format(
                incentive['short_desc'], progress_bar, incentive['description'], incentive['total'],
            ))
        elif 'options' in incentive:
            print('\t{0:<15s}\t{1}'.format(
                incentive['short_desc'], incentive['description'],
            ))
            for option in incentive['options']:
                try:
                    percent = option['total'] / incentive['current'] * 100
                except ZeroDivisionError:
                    percent = 0
                progress_bar = show_progress(percent)
                print('\t{0:<35s}\t{1}|${2:,.0f}'.format(option['choice'], progress_bar, option['total']))
                if option['description']:
                    print('\t  |>{0}'.format(option['description']))
