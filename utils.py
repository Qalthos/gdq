import re

from bs4 import BeautifulSoup
import requests


def show_progress(percent, width=72):
    chars = " ▏▎▍▌▋▊▉█"

    blocks, fraction = divmod(percent * width, 100)
    blocks = int(blocks)
    fraction = int(fraction // (100 / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1

    return '▕' + chars[-1] * blocks + chars[fraction] + ' ' * (width - blocks - 1) + '▏'


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


def display_run(run, incentive_dict, width=80):
    prefix = '       '
    width -= 8

    if run['delta'] == '  NOW  ':
        run['estimate'] = ''
    else:
        # Cut seconds off of estimate
        run['estimate'] = '+%s' % run['estimate'].rsplit(':', 1)[0]

    game = '{game} ({platform})'.format(**run)
    description = "{0}│{1:<49s} {2: >" + str(width - 50) + "s}"
    print(description.format(run['delta'], game, run['runner']))
    print("{estimate: >7s}│{runtype}".format(**run))

    # Handle incentives
    for incentive in incentive_dict.get(run['game'], []):
        if 'total' in incentive:
            percent = incentive['current'] / incentive['total'] * 100
            progress_bar = show_progress(percent, width - 42)
            total = '${0:,.0f}'.format(incentive['total'])
            print('{3}├┬{0:<31s} {1}{2: >7s}'.format(
                incentive['short_desc'], progress_bar, total, prefix
            ))
            print('{1}│└▶{0}'.format(incentive['description'], prefix))
        elif 'options' in incentive:
            print('{2}├┬{0:<32s} {1}'.format(
                incentive['short_desc'], incentive['description'], prefix
            ))
            for index, option in enumerate(incentive['options']):
                try:
                    percent = option['total'] / incentive['current'] * 100
                except ZeroDivisionError:
                    percent = 0
                progress_bar = show_progress(percent, width - 42)
                total = '${0:,.0f}'.format(option['total'])
                if index == len(incentive['options']) - 1:
                    print('{3}│└▶{0:<30s} {1}{2: >7s}'.format(option['choice'], progress_bar, total, prefix))
                else:
                    print('{3}│├▶{0:<30s} {1}{2: >7s}'.format(option['choice'], progress_bar, total, prefix))
                if option['description']:
                    print('{1}│  └▶{0}'.format(option['description'], prefix))

    print('{0}┼{1}'.format('─' * 7, '─' * (width)))
