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
        if hasattr(incentive, 'total'):
            display_incentive(incentive, width)
        elif hasattr(incentive, 'options'):
            display_option(incentive, width)


def display_incentive(incentive, width):
    progress_bar = show_progress(incentive.percent, width - 50)
    print(f'{PREFIX}├┬{incentive.short_desc:<39s} {progress_bar}{incentive.pretty_total: >7s}')
    print(f'{PREFIX}│└▶{incentive.description}')


def display_option(incentive, width):
    print(f'{PREFIX}├┬{incentive.short_desc:<22s} {incentive.description}')

    for index, option in enumerate(incentive.options):
        try:
            percent = option.total / incentive.current * 100
        except ZeroDivisionError:
            percent = 0

        progress_bar = show_progress(percent, width - 32)

        leg = '├'
        if index == len(incentive.options) - 1:
            leg = '└'

        print(f'{PREFIX}│{leg}▶{option.name:<20s} {progress_bar}{option.pretty_total: >7s}')
        if option.description:
            print(f'{PREFIX}│  └▶{option.description}')


if __name__ == '__main__':
    import sys
    print(show_progress(float(sys.argv[1])))
