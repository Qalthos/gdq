from datetime import timedelta

PREFIX = ' ' * 7


def show_progress(percent, width=72):
    chars = " ▏▎▍▌▋▊▉█"

    blocks, fraction = divmod(percent * width, 100)
    blocks = int(blocks)
    fraction = int(fraction // (100 / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1

    return '▕' + chars[-1] * blocks + chars[fraction] + ' ' * (width - blocks - 1) + '▏'


def display_run(run, incentive_dict, width=80):
    # If the estimate has passed, it's probably over.
    if run.raw_estimate < timedelta():
        return

    width -= len(PREFIX) + 1

    runner = '│' + run.runner + '│'
    print('{0}┼{1}┬{2}┐'.format('─' * 7, '─' * (width - len(runner)), '─' * len(run.runner)))

    line_one = "{0}│{1:<49s} {2: >" + str(width - 50) + "s}"
    print(line_one.format(run.delta, run.game_desc, runner))

    line_two = "{0: >7s}│{1:<" + str(width - len(run.runner) - 2) + "}└{2}┘"
    print(line_two.format(run.estimate, run.runtype, '─' * len(run.runner)))

    # Handle incentives
    for incentive in incentive_dict.get(run.game, []):
        if 'total' in incentive:
            display_incentive(incentive, width)
        elif 'options' in incentive:
            display_option(incentive, width)


def display_incentive(incentive, width):
    percent = incentive['current'] / incentive['total'] * 100
    progress_bar = show_progress(percent, width - 50)
    total = '${0:,.0f}'.format(incentive['total'])
    print('{3}├┬{0:<39s} {1}{2: >7s}'.format(
        incentive['short_desc'], progress_bar, total, PREFIX
    ))
    print('{1}│└▶{0}'.format(incentive['description'], PREFIX))


def display_option(incentive, width):
    print('{2}├┬{0:<32s} {1}'.format(
        incentive['short_desc'], incentive['description'], PREFIX
    ))
    for index, option in enumerate(incentive['options']):
        try:
            percent = option['total'] / incentive['current'] * 100
        except ZeroDivisionError:
            percent = 0
        progress_bar = show_progress(percent, width - 32)
        total = '${0:,.0f}'.format(option['total'])
        if index == len(incentive['options']) - 1:
            print('{3}│└▶{0:<20s} {1}{2: >7s}'.format(option['choice'], progress_bar, total, PREFIX))
        else:
            print('{3}│├▶{0:<20s} {1}{2: >7s}'.format(option['choice'], progress_bar, total, PREFIX))
        if option['description']:
            print('{1}│  └▶{0}'.format(option['description'], PREFIX))


if __name__ == '__main__':
    import sys
    print(show_progress(float(sys.argv[1])))
