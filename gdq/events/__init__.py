from abc import ABC, abstractmethod
from datetime import timedelta
from itertools import zip_longest
import re
from typing import Iterator, List

import pyplugs

from gdq import utils
from gdq.models import PREFIX, Run, Event, SingleEvent
from gdq.parsers import gdq_api, horaro


MIN_OFFSET = 20

names = pyplugs.names_factory(__package__)
marathon = pyplugs.call_factory(__package__)


def money_parser(string: str) -> float:
    return float(re.compile('[$,\n]').sub("", string))


class MarathonBase(ABC):
    # Tracker base URL
    url = ""

    # Cached live data
    display_streams: int
    schedules = [[]]

    @abstractmethod
    def refresh_all(self) -> None:
        raise NotImplementedError

    def display(self, args) -> bool:
        # Terminal lines are apparently 1-indexed.
        row_index = 1
        if isinstance(self, GDQTracker):
            print(f"\x1b[H{self.format_milestone()}")
            row_index += 2

        # Limit schedule display based on args
        schedules = self.schedules
        if args.stream_index <= len(schedules):
            schedules = [schedules[args.stream_index - 1]]

        rendered_schedules = []
        column_width = utils.term_width // len(schedules)
        padding = " " * column_width

        for schedule in schedules:
            schedule_lines = []
            for run in schedule:
                schedule_lines.extend(self.format_run(run, column_width, args))
            rendered_schedules.append(schedule_lines)

        first_row = True
        for full_row in zip_longest(*rendered_schedules):
            full_row = [column or padding for column in full_row]
            for i in range(len(full_row) - 1):
                full_row[i] = full_row[i][:-1] + utils.join_char(
                    full_row[i][-1], full_row[i + 1][0]
                )
            full_row = "".join(full_row)
            if first_row:
                full_row = utils.flatten(full_row)
                first_row = False

            print(f"\x1b[{row_index}H{full_row}", end="")
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

    def format_run(self, run: Run, width: int = 80, args=None) -> Iterator[str]:
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


class GDQTracker(MarathonBase):
    # Historical donation records
    records: list = []

    # Cached live data
    current_event: Event
    incentives: dict = {}

    def __init__(self, url: str = None, streams: int = 1) -> None:
        self.url = url or self.url
        self.display_streams = streams
        self.read_events()

    @property
    def total(self):
        return self.current_event.total

    @property
    def current_events(self) -> List[SingleEvent]:
        events = getattr(self.current_event, "subevents", None)
        if not events:
            events = [self.current_event]
        return events

    def refresh_all(self) -> None:
        self.read_events()
        self.schedules = [gdq_api.get_runs(self.url, event.event_id) for event in self.current_events]
        self.read_incentives()

    def read_events(self) -> None:
        events = list(gdq_api.get_events(self.url))
        self.current_event = events.pop(-1)

        self.records = sorted(
            [(event.total, event.short_name.upper()) for event in events]
        )

    def read_incentives(self) -> None:
        incentives = {}
        for event in self.current_events:
            incentives.update(
                gdq_api.get_incentives_for_event(self.url, event.event_id)
            )
        self.incentives = incentives

    def format_milestone(self) -> str:
        last_record = (0, "")
        line_two = ""
        for record in self.records:
            if record[0] > self.total:
                relative_percent = (self.total - last_record[0]) / (record[0] - last_record[0]) * 100
                record_bar = utils.show_progress(relative_percent, width=(utils.term_width - 12))
                line_two = f"\n{utils.short_number(last_record[0]): <5s}▕{record_bar}▏{utils.short_number(record[0]): >5s}"
                break
            last_record = record
        else:
            record = (0, "NEW HIGH SCORE!")

        dollar_total = f"${self.total:,.2f}"
        max_len = max((len(last_record[1]), len(record[1])))
        return f"{last_record[1]: <{max_len}s}{dollar_total: ^{utils.term_width - 2 * max_len}}{record[1]: >{max_len}s}{line_two}"

    def format_run(self, run: Run, width: int = 80, args=None) -> str:
        width -= len(PREFIX) + 1
        yield from super().format_run(run, width)

        incentives = self.incentives.get(run.game, [])
        if incentives:
            align_width = max(MIN_OFFSET, *(len(incentive) for incentive in incentives))
            # Handle incentives
            for incentive in incentives:
                yield from incentive.render(width, align_width, args)


class HoraroSchedule(MarathonBase):
    # horaro.org keys
    group_name = ""
    current_event: str

    def refresh_all(self) -> None:
        self.schedules = [horaro.read_schedule(self.group_name, self.current_event, self.parse_data)]

    @staticmethod
    @abstractmethod
    def parse_data(keys, schedule, timezone="UTC") -> Iterator[Run]:
        raise NotImplementedError
