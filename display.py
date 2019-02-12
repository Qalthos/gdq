from datetime import timedelta
from textwrap import wrap

from utils import short_number

PREFIX = ' ' * 7
MIN_OFFSET = 20
CHOICE_CUTOFF = -1


def show_progress(percent, width=72, out_of=100):
    chars = " ▏▎▍▌▋▊▉█"

    blocks, fraction = divmod(percent * width, out_of)
    blocks = int(blocks)
    fraction = int(fraction // (out_of / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1

    return '▕' + chars[-1] * blocks + chars[fraction] + ' ' * (width - blocks - 1) + '▏'


def display_milestone(total, records, width=80):
    last_record = 0
    for record, name in records:
        if record < total:
            last_record = record
            continue

        relative_percent = (total - last_record) / (record - last_record) * 100
        progress_bar = show_progress(relative_percent, width=(width - 7 - len(name)))
        print('{0}{1}{2: >5s}'.format(
            name, progress_bar, short_number(record),
        ))
        break

    else:
        print(f'{total:<9,.0f} NEW HIGH SCORE!')


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

    incentives = incentive_dict.get(run.game, [])
    if incentives:
        align_width = max(MIN_OFFSET, *(len(incentive) for incentive in incentives))
        # Handle incentives
        for incentive in incentives:
            if hasattr(incentive, 'total'):
                display_incentive(incentive, width, align_width)
            elif hasattr(incentive, 'options'):
                display_option(incentive, width, align_width)


def display_incentive(incentive, width, align):
    # Remove fixed elements
    width -= 3

    lines = wrap(incentive.description, width + 1)
    print(f'{PREFIX}├┬{lines[0]}')
    for line in lines[1:]:
        print(f'{PREFIX}││{line}')

    progress_bar = show_progress(incentive.percent, width - align - 7)
    progress = '{0}│└▶{1:<' + str(align) + 's}{2}{3: >6s}'
    print(progress.format(PREFIX, incentive.short_desc, progress_bar, incentive.total))


def display_option(incentive, width, align):
    # Remove fixed elements
    width -= 3

    desc_size = max(align, len(incentive.short_desc))
    rest_size = width - desc_size
    lines = wrap(incentive.description, rest_size)
    description = '{0}├┬{1:<' + str(desc_size) + 's}  {2}'
    print(description.format(PREFIX, incentive.short_desc, lines[0]))
    for line in lines[1:]:
        description = '{0}││{0:<' + str(desc_size) + 's}  {1}'
        print(description.format(PREFIX, line))

    max_percent = incentive.max_percent
    for index, option in enumerate(incentive.options):
        try:
            percent = option.numeric_total / incentive.current * 100
        except ZeroDivisionError:
            percent = 0

        if percent < CHOICE_CUTOFF:
            print(f'{PREFIX}│╵')
            break

        progress_bar = show_progress(percent, width - align - 7, max_percent)

        leg = '├│'
        if index == len(incentive.options) - 1:
            leg = '└ '

        line_one = '{0}│{1}▶{2:<' + str(align) + 's}{3}{4: >6s}'
        print(line_one.format(PREFIX, leg[0], option.name, progress_bar, option.total))
        if option.description:
            lines = wrap(option.description, width)
            print(f'{PREFIX}│{leg[1]} └▶{lines[0]}')
            for line in lines[1:]:
                print(f'{PREFIX}│{leg[1]}   {line}')


if __name__ == '__main__':
    import sys
    print(show_progress(float(sys.argv[1])))
