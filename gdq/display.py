from datetime import timedelta
from itertools import zip_longest
from textwrap import wrap
from typing import Generator

from gdq.events import MarathonBase, IncentiveDict
from gdq.models import Run, ChoiceIncentive, DonationIncentive
from gdq.utils import short_number


PREFIX = " " * 7
MIN_OFFSET = 20


def show_progress(percent: float, width: int = 72, out_of: float = 100) -> str:
    chars = " ▏▎▍▌▋▊▉█"

    blocks, fraction = 0, 0
    if percent:
        blocks, fraction = divmod(percent * width, out_of)
        blocks = int(blocks)
        fraction = int(fraction // (out_of / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1

    return chars[-1] * blocks + chars[fraction] + " " * (width - blocks - 1)


def format_milestone(marathon: MarathonBase, width: int = 80) -> str:
    last_record = 0
    for record, name in marathon.records:
        if record < marathon.total:
            last_record = record
            continue

        relative_percent = (marathon.total - last_record) / (record - last_record) * 100
        record_bar = show_progress(relative_percent, width=(width - 7 - len(name)))
        return f"{name}▕{record_bar}▏{short_number(record): >5s}"
    return f"NEW HIGH SCORE!" + " " * (width - 24) + f"{marathon.total:<9,.0f}"


def display_marathon(width: int, height: int, marathon: MarathonBase, args) -> None:
    # Terminal lines are apparently 1-indexed.
    row_index = 1
    if not marathon.schedule_only:
        print(f"\x1b[H{format_milestone(marathon, width)}")
        row_index += 1

    rendered_schedules = []
    column_width = width // len(marathon.schedules)
    padding = " " * column_width

    for schedule in marathon.schedules:
        schedule_lines = []
        for run in schedule:
            schedule_lines.extend(_format_run(run, marathon.incentives, column_width, args))
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
        clear_row = " " * width
        for clear_index in range(row_index, height):
            print(f"\x1b[{clear_index}H{clear_row}", end="")


def _format_run(run: Run, incentives: IncentiveDict, width: int = 80, args=None) -> str:
    # If the estimate has passed, it's probably over.
    if run.remaining < timedelta():
        return

    width -= len(PREFIX) + 1
    if not run.runner:
        desc_width = max(len(run.game_desc), len(run.category))
        if desc_width > width:
            # If display too long, truncate run
            run.game = run.game[:width - 1] + "…"
            run.category = run.category[:width - 1] + "…"

        yield "{0}┼{1}┤".format("─" * 7, "─" * (width - 1))

        line_one = "{0}│{1:<" + str(width - 1) + "s}│"
        yield line_one.format(run.delta, run.game_desc)

        line_two = "{0: >7s}│{1:<" + str(width - 1) + "}│"
        yield line_two.format(run.str_estimate, run.category)
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

        line_one = "{0}│{1:<" + str(desc_width) + "s}{2}"
        yield line_one.format(run.delta, run.game_desc, runner)

        line_two = "{0: >7s}│{1:<" + str(desc_width) + "}└{2}┤"
        yield line_two.format(run.str_estimate, run.category, border)

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


def _render_incentive(incentive: DonationIncentive, width: int, align: int) -> Generator:
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


def _render_option(incentive: ChoiceIncentive, width: int, align: int, args) -> Generator:
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
    for index, option in enumerate(incentive.options):
        try:
            percent = option.numeric_total / incentive.current * 100
        except ZeroDivisionError:
            percent = 0

        if percent < args.min_percent and index >= args.min_options and index != len(incentive.options) - 1:
            remaining = incentive.options[index:]
            total = sum(option.numeric_total for option in remaining)
            percent = total / incentive.current * 100
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


if __name__ == "__main__":
    import sys

    print(show_progress(float(sys.argv[1])))
