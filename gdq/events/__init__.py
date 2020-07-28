import argparse
from abc import ABC, abstractmethod
from datetime import timedelta
from itertools import zip_longest
from typing import Iterable, List, Protocol

from gdq import utils
from gdq.models import Run


class MarathonBase(Protocol):
    def refresh_all(self) -> None:
        ...

    def display(self, args: argparse.Namespace) -> bool:
        ...


class TrackerBase(ABC):
    # Cached live data
    schedules: List[List[Run]] = []

    @abstractmethod
    def refresh_all(self) -> None:
        raise NotImplementedError

    def display(self, args: argparse.Namespace) -> bool:
        return self._real_display(args)

    def _real_display(self, args: argparse.Namespace, row_index: int = 1) -> bool:
        # Limit schedule display based on args
        schedules = self.schedules
        if 0 < args.stream_index <= len(schedules):
            schedules = [schedules[args.stream_index - 1]]
        else:
            for schedule in self.schedules:
                # Drop schedules that are over
                if not any(run.is_live for run in schedule):
                    schedules.remove(schedule)

        # If we're out of schedules, we're done
        if not schedules:
            return False

        rendered_schedules = []
        column_width = utils.term_width // len(schedules)

        for schedule in schedules:
            schedule_lines: List[str] = []
            for run in schedule:
                schedule_lines.extend(self.format_run(run, column_width, args))
                if len(schedule_lines) >= utils.term_height:
                    break
            else:
                if schedule_lines:
                    # Add a nice clean end piece
                    schedule_lines.append(f"───────┴{'─' * (column_width - 9)}┘")
            rendered_schedules.append(schedule_lines)

        padding = " " * column_width
        return self._display_schedules(rendered_schedules, padding, row_index)

    def _display_schedules(self, schedules: List[List[str]], padding: str, row_index: int) -> bool:
        first_row = True
        for full_row in zip_longest(*schedules):
            full_row = [column or padding for column in full_row]
            for i in range(len(full_row) - 1):
                full_row[i] = full_row[i][:-1] + utils.join_char(
                    full_row[i][-1], full_row[i + 1][0]
                )
            full_row = "".join(full_row)
            if first_row:
                full_row = utils.flatten(full_row)
                first_row = False

            print(f"\x1b[{row_index}H{full_row}\x1b[K", end="")
            row_index += 1
            if row_index == utils.term_height:
                break
        else:
            if first_row:
                return False
            clear_row = " " * utils.term_width
            for clear_index in range(row_index, utils.term_height):
                print(f"\x1b[{clear_index}H{clear_row}", end="")

        return True

    def format_run(self, run: Run, width: int = 80, args: argparse.Namespace = None) -> Iterable[str]:
        if args:
            # Reserved for future use
            pass

        # If the estimate has passed, it's probably over.
        if run.remaining < timedelta():
            return

        width -= 8
        if not any(run.runners):
            desc_width = max(len(run.game_desc), len(run.category))
            if desc_width > width:
                # If display too long, truncate run
                run.game = run.game[:width - 1] + "…"
                run.category = run.category[:width - 1] + "…"

            yield "{0}┼{1}┤".format("─" * 7, "─" * (width - 1))
            yield f"{run.delta}│{run.game_desc:<{width - 1}s}│"
            yield f"{run.str_estimate: >7s}│{run.category:<{width - 1}}│"

        else:
            desc_width = max(width - 2 - len(run.runner_str), len(run.game_desc), len(run.category))

            runner = "│" + run.runner_str + "│"
            if desc_width + len(runner) > width:
                # Truncate runner display if too long
                runner_width = width - 3 - desc_width
                runner = "│" + run.runner_str[:runner_width] + "…│"

            if desc_width + len(runner) > width:
                # If display still too long, truncate run
                overrun = desc_width + len(runner) - width
                desc_width -= overrun
                run.game = run.game[: -(overrun + 1)] + "…"

            border = "─" * (len(runner) - 2)
            yield f"───────┼{'─' * desc_width}┬{border}┤"
            yield f"{run.delta}│{run.game_desc:<{desc_width}s}{runner}"
            yield f"{run.str_estimate: >7s}│{run.category:<{desc_width}}└{border}┤"
