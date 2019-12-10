from datetime import timedelta
from itertools import zip_longest
from operator import attrgetter
from textwrap import wrap
from typing import Dict, Iterator

from gdq.events import MarathonBase, GDQTracker
from gdq.models import Run, Incentive, ChoiceIncentive, DonationIncentive
from gdq.utils import short_number, show_progress


PREFIX = " " * 7
MIN_OFFSET = 20


def format_milestone(marathon: GDQTracker, width: int = 80) -> str:
    last_record = (0, "")
    line_two = ""
    for record in marathon.records:
        if record[0] > marathon.total:
            relative_percent = (marathon.total - last_record[0]) / (record[0] - last_record[0]) * 100
            record_bar = show_progress(relative_percent, width=(width - 12))
            line_two = f"\n{short_number(last_record[0]): <5s}▕{record_bar}▏{short_number(record[0]): >5s}"
            break
        last_record = record
    else:
        record = (0, "NEW HIGH SCORE!")

    dollar_total = f"${marathon.total:,.2f}"
    max_len = max((len(last_record[1]), len(record[1])))
    return f"{last_record[1]: <{max_len}s}{dollar_total: ^{width - 2 * max_len}}{record[1]: >{max_len}s}{line_two}"


def display_marathon(width: int, height: int, marathon: MarathonBase, args) -> bool:
    # Terminal lines are apparently 1-indexed.
    row_index = 1
    if isinstance(marathon, GDQTracker):
        print(f"\x1b[H{format_milestone(marathon, width)}")
        row_index += 2

    # Limit schedule display based on args
    schedules = marathon.schedules
    if args.stream_index <= len(schedules):
        schedules = [schedules[args.stream_index - 1]]

    rendered_schedules = []
    column_width = width // len(schedules)
    padding = " " * column_width

    for schedule in schedules:
        schedule_lines = []
        for run in schedule:
            if isinstance(marathon, GDQTracker):
                schedule_lines.extend(_format_run(run, marathon.incentives, column_width, args))
            else:
                schedule_lines.extend(_format_basic_run(run, column_width))
        rendered_schedules.append(schedule_lines)

    first_row = True
    for full_row in zip_longest(*rendered_schedules):
        full_row = [column or padding for column in full_row]
        for i in range(len(full_row) - 1):
            full_row[i] = full_row[i][:-1] + _join_char(
                full_row[i][-1], full_row[i + 1][0]
            )
        full_row = "".join(full_row)
        if first_row:
            full_row = _flatten(full_row)
            first_row = False

        print(f"\x1b[{row_index}H{full_row}", end="")
        row_index += 1
        if row_index == height:
            break
    else:
        if first_row:
            return False
        clear_row = " " * width
        for clear_index in range(row_index, height):
            print(f"\x1b[{clear_index}H{clear_row}", end="")

    return True


def _format_basic_run(run: Run, width: int = 80) -> Iterator[str]:
    # If the estimate has passed, it's probably over.
    if run.remaining < timedelta():
        return

    if not run.runner:
        desc_width = max(len(run.game_desc), len(run.category))
        if desc_width > width:
            # If display too long, truncate run
            run.game = run.game[:width - 1] + "…"
            run.category = run.category[:width - 1] + "…"

        yield "{0}┼{1}┤".format("─" * 7, "─" * (width - 1))
        yield f"{run.delta}│{run.game_desc:<{width - 1}s}│"
        yield f"{run.str_estimate: >7s}│{run.category:<{width - 1}}│"
    else:
        desc_width = max(width - 2 - len(run.runner), len(run.game_desc), len(run.category))

        runner = "│" + run.runner + "│"
        if desc_width + len(runner) > width:
            # Truncate runner display if too long
            runner_width = width - 3 - desc_width
            runner = "│" + run.runner[:runner_width] + "…│"

        if desc_width + len(runner) > width:
            # If display still too long, truncate run
            overrun = desc_width + len(runner) - width
            desc_width -= overrun
            run.game = run.game[: -(overrun + 1)] + "…"

        border = "─" * (len(runner) - 2)
        yield "{0}┼{1}┬{2}┤".format("─" * 7, "─" * desc_width, border)

        yield f"{run.delta}│{run.game_desc:<{desc_width}s}{runner}"
        yield f"{run.str_estimate: >7s}│{run.category:<{desc_width}}└{border}┤"


def _format_run(run: Run, incentives: Dict[str, Incentive], width: int = 80, args=None) -> str:
    width -= len(PREFIX) + 1
    for line in _format_basic_run(run, width):
        yield line

    incentives = incentives.get(run.game, [])
    if incentives:
        align_width = max(MIN_OFFSET, *(len(incentive) for incentive in incentives))
        # Handle incentives
        for incentive in incentives:
            if hasattr(incentive, "total"):
                if incentive.percent < 100 or not args.hide_completed:
                    yield from _render_incentive(incentive, width, align_width)
            elif hasattr(incentive, "options"):
                yield from _render_option(incentive, width, align_width, args)


def _render_incentive(incentive: DonationIncentive, width: int, align: int) -> Iterator[str]:
    # Remove fixed elements
    width -= 4

    lines = wrap(incentive.description, width + 1)
    incentive_bar = show_progress(incentive.percent, width - align - 7)
    if lines:
        yield f"{PREFIX}├┬{lines[0].ljust(width + 2)}│"
        for line in lines[1:]:
            yield f"{PREFIX}││{line.ljust(width + 2)}│"

        progress = "{0}│└▶{1:<" + str(align) + "s}▕{2}▏{3: >6s}│"
    else:
        progress = "{0}├─▶{1:<" + str(align) + "s}▕{2}▏{3: >6s}│"

    yield progress.format(PREFIX, incentive.short_desc, incentive_bar, incentive.total)


def _render_option(incentive: ChoiceIncentive, width: int, align: int, args) -> Iterator[str]:
    # Remove fixed elements
    width -= 4

    desc_size = max(align, len(incentive.short_desc))
    rest_size = width - desc_size
    lines = wrap(incentive.description, rest_size - 1)
    description = "{0}├┬{1:<" + str(desc_size) + "s}  {2: <" + str(rest_size) + "s}│"
    if lines:
        yield description.format(PREFIX, incentive.short_desc, lines[0])
        for line in lines[1:]:
            description = (
                "{0}││{0:<" + str(desc_size) + "s}  {1: <" + str(rest_size) + "s}│"
            )
            yield description.format(PREFIX, line)
    else:
        yield description.format(PREFIX, incentive.short_desc, "")

    max_percent = incentive.max_percent
    sorted_options = sorted(incentive.options, key=attrgetter("numeric_total"), reverse=True)
    for index, option in enumerate(sorted_options):
        try:
            percent = option.numeric_total / incentive.current * 100
        except ZeroDivisionError:
            percent = 0

        if percent < args.min_percent and index >= args.min_options and index != len(incentive.options) - 1:
            remaining = sorted_options[index:]
            total = sum(option.numeric_total for option in remaining)
            try:
                percent = total / incentive.current * 100
            except ZeroDivisionError:
                percent = 0
            description = "And {} more".format(len(remaining))
            incentive_bar = show_progress(percent, width - align - 7, max_percent)
            line_one = "{0}│╵ {1:<" + str(align) + "s}▕{2}▏{3: >6s}│"
            yield line_one.format(PREFIX, description, incentive_bar, short_number(total))
            break

        incentive_bar = show_progress(percent, width - align - 7, max_percent)

        leg = "├│"
        if index == len(incentive.options) - 1:
            leg = "└ "

        line_one = "{0}│{1}▶{2:<" + str(align) + "s}▕{3}▏{4: >6s}│"
        yield line_one.format(PREFIX, leg[0], option.name, incentive_bar, option.total)
        if option.description:
            lines = wrap(option.description, width)
            yield f"{PREFIX}│{leg[1]} └▶{lines[0].ljust(width - 1)}│"
            for line in lines[1:]:
                yield f"{PREFIX}│{leg[1]}   {line.ljust(width - 1)}│"


def _join_char(left: str, right: str) -> str:
    choices = "║╟╢╫"
    pick = 0
    if left in "─┐┘┤":
        pick += 0b10
    if right == "─":
        pick += 0b01

    return choices[pick]


def _flatten(string: str) -> str:
    translation = str.maketrans("┼╫┤", "┬╥┐")
    return string.translate(translation)
