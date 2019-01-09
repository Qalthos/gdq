from datetime import timedelta
from textwrap import wrap

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
    desc_width = max(width - 2 - len(run.runner), len(run.game_desc))

    runner = '│' + run.runner + '│'
    if desc_width + len(runner) > width:
        # Truncate runner display if too long
        runner_width = width - 3 - desc_width
        runner = '│' + run.runner[:runner_width] + '…│'

    border = '─' * (len(runner) - 2)
    print('{0}┼{1}┬{2}┐'.format('─' * 7, '─' * desc_width, border))

    line_one = "{0}│{1:<" + str(desc_width) + "s}{2}"
    print(line_one.format(run.delta, run.game_desc, runner))

    line_two = "{0: >7s}│{1:<" + str(desc_width) + "}└{2}┘"
    print(line_two.format(run.estimate, run.runtype, border))

    # Handle incentives
    for incentive in incentive_dict.get(run.game, []):
        if hasattr(incentive, 'total'):
            display_incentive(incentive, width)
        elif hasattr(incentive, 'options'):
            display_option(incentive, width)


def display_incentive(incentive, width):
    # Remove fixed elements
    width -= 2

    desc_size = max(25, len(incentive.short_desc))
    progress_bar = show_progress(incentive.percent, width - desc_size - 8)

    line_one = '{0}├┬{1:<' + str(desc_size) + 's}{2}{3: >7s}'
    print(line_one.format(PREFIX, incentive.short_desc, progress_bar, incentive.total))

    lines = wrap(incentive.description, width)
    print(f'{PREFIX}│└▶{lines[0]}')
    for line in lines[1:]:
        print(f'{PREFIX}│  {line}')


def display_option(incentive, width):
    short_width = width - 25
    lines = wrap(incentive.description, short_width)
    print(f'{PREFIX}├┬{incentive.short_desc:<22s} {lines[0]}')
    for line in lines[1:]:
        print(f'{PREFIX}││{PREFIX:<22s} {line}')

    for index, option in enumerate(incentive.options):
        try:
            percent = option.numeric_total / incentive.current * 100
        except ZeroDivisionError:
            percent = 0

        progress_bar = show_progress(percent, width - 32)

        leg = '├│'
        if index == len(incentive.options) - 1:
            leg = '└ '

        print(f'{PREFIX}│{leg[0]}▶{option.name:<20s} {progress_bar}{option.total: >7s}')
        if option.description:
            print(f'{PREFIX}│{leg[1]} └▶{option.description}')


if __name__ == '__main__':
    import sys
    print(show_progress(float(sys.argv[1])))
