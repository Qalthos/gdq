from datetime import timedelta
from textwrap import wrap

from utils import short_number

PREFIX = ' ' * 7
MIN_OFFSET = 20
CHOICE_CUTOFF = -1


def show_progress(percent, width=72, out_of=100):
    chars = " ▏▎▍▌▋▊▉█"

    blocks, fraction = 0, 0
    if percent:
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


def display_runs(schedules, incentives, width=80, height=24):
    """Displays all current and future runs in a chronological list.

    List may be split vertically to account for multiple concurrent streams.
    """
    rendered_schedules = []
    column_width = width // len(schedules)
    for schedule in schedules:
        schedule_lines = []
        for run in schedule:
            schedule_lines.extend(_render_run(run, incentives, column_width))
            if len(schedule_lines) > height:
                break
        padding = [' ' * column_width] * (height - len(schedule_lines))
        rendered_schedules.append(schedule_lines + padding)

    first_row = True
    for full_row in zip(*rendered_schedules):
        full_row = list(full_row)
        for i in range(len(full_row) - 1):
            full_row[i] = full_row[i][:-1] + _join_char(full_row[i][-1], full_row[i + 1][0])
        full_row = ''.join(full_row)
        if first_row:
            full_row = _flatten(full_row)
            first_row = False
        print(full_row)


def display_run(run, incentive_dict, width=80):
    """Old version that prints a single schedule."""
    for row in _render_run(run, incentive_dict, width):
        print(row)


def _render_run(run, incentive_dict, width=80):
    # If the estimate has passed, it's probably over.
    if run.remaining < timedelta():
        return

    width -= len(PREFIX) + 1
    desc_width = max(width - 2 - len(run.runner), len(run.game_desc))

    runner = '│' + run.runner + '│'
    if desc_width + len(runner) > width:
        # Truncate runner display if too long
        runner_width = width - 3 - desc_width
        runner = '│' + run.runner[:runner_width] + '…│'

    if desc_width + len(runner) > width:
        # If display still too long, truncate run
        overrun = desc_width + len(runner) - width
        desc_width -= overrun
        run.game = run.game[:-(overrun + 1)] + '…'

    border = '─' * (len(runner) - 2)
    yield '{0}┼{1}┬{2}┤'.format('─' * 7, '─' * desc_width, border)

    line_one = "{0}│{1:<" + str(desc_width) + "s}{2}"
    yield line_one.format(run.delta, run.game_desc, runner)

    line_two = "{0: >7s}│{1:<" + str(desc_width) + "}└{2}┤"
    yield line_two.format(run.str_estimate, run.category, border)

    incentives = incentive_dict.get(run.game, [])
    if incentives:
        align_width = max(MIN_OFFSET, *(len(incentive) for incentive in incentives))
        # Handle incentives
        for incentive in incentives:
            if hasattr(incentive, 'total'):
                yield from _render_incentive(incentive, width, align_width)
            elif hasattr(incentive, 'options'):
                yield from _render_option(incentive, width, align_width)


def _render_incentive(incentive, width, align):
    # Remove fixed elements
    width -= 4

    lines = wrap(incentive.description, width + 1)
    progress_bar = show_progress(incentive.percent, width - align - 7)
    if lines:
        yield f'{PREFIX}├┬{lines[0].ljust(width + 2)}│'
        for line in lines[1:]:
            yield f'{PREFIX}││{line.ljust(width + 2)}│'

        progress = '{0}│└▶{1:<' + str(align) + 's}{2}{3: >6s}│'
    else:
        progress = '{0}├─▶{1:<' + str(align) + 's}{2}{3: >6s}│'

    yield progress.format(PREFIX, incentive.short_desc, progress_bar, incentive.total)


def _render_option(incentive, width, align):
    # Remove fixed elements
    width -= 4

    desc_size = max(align, len(incentive.short_desc))
    rest_size = width - desc_size
    lines = wrap(incentive.description, rest_size - 1)
    description = '{0}├┬{1:<' + str(desc_size) + 's}  {2: <' + str(rest_size) + 's}│'
    yield description.format(PREFIX, incentive.short_desc, lines[0])
    for line in lines[1:]:
        description = '{0}││{0:<' + str(desc_size) + 's}  {1: <' + str(rest_size) + 's}│'
        yield description.format(PREFIX, line)

    max_percent = incentive.max_percent
    for index, option in enumerate(incentive.options):
        try:
            percent = option.numeric_total / incentive.current * 100
        except ZeroDivisionError:
            percent = 0

        if percent < CHOICE_CUTOFF:
            yield f'{PREFIX}│╵'
            break

        progress_bar = show_progress(percent, width - align - 7, max_percent)

        leg = '├│'
        if index == len(incentive.options) - 1:
            leg = '└ '

        line_one = '{0}│{1}▶{2:<' + str(align) + 's}{3}{4: >6s}│'
        yield line_one.format(PREFIX, leg[0], option.name, progress_bar, option.total)
        if option.description:
            lines = wrap(option.description, width)
            yield f'{PREFIX}│{leg[1]} └▶{lines[0].ljust(width - 1)}│'
            for line in lines[1:]:
                yield f'{PREFIX}│{leg[1]}   {line.ljust(width - 1)}│'


def _join_char(left, right):
    choices = '║╟╢╫'
    pick = 0
    if left in '─┐┘┤':
        pick += 0b10
    if right == '─':
        pick += 0b01

    return choices[pick]


def _flatten(string):
    translation = str.maketrans('┼╫┤', '┬╥┐')
    return string.translate(translation)


if __name__ == '__main__':
    import sys
    print(show_progress(float(sys.argv[1])))
