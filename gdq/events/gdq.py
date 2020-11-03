import argparse
import operator
from collections import namedtuple
from typing import Dict, Iterable, List, Type, Union

from gdq import money, utils
from gdq.events import TrackerBase
from gdq.models import Event, Incentive, MultiEvent, Run, Runner, SingleEvent
from gdq.parsers import gdq_api

FakeRecord = namedtuple("FakeRecord", ["short_name", "total"])


class GDQTracker(TrackerBase):
    # Tracker base URL
    url: str

    # Historical donation records
    records: List[Event]
    record_offsets: Dict[str, float]

    # Cached live data
    current_event: Event
    runners: Dict[int, Runner] = {}
    incentives: Dict[str, List[Incentive]] = {}

    # Set to account for discrepencies between computed and reported totals.
    offset: float
    color: bool

    def __init__(
            self, url: str, color: bool, stream_index: int = -1,
            offset: float = 0, record_offsets: Dict[str, float] = {}):
        # We need to have a trailing '/' for urljoin to work properly
        if url[-1] != "/":
            url += "/"

        self.url = url
        self.stream_index = stream_index
        self.offset = offset
        self.record_offsets = record_offsets
        self.color = color

    @property
    def total(self) -> money.Money:
        return self.current_event.total - self.currency(self.offset)

    @property
    def currency(self) -> Type[money.Money]:
        return type(self.current_event.total)

    @property
    def current_events(self) -> List[SingleEvent]:
        if isinstance(self.current_event, SingleEvent):
            return [self.current_event]
        if isinstance(self.current_event, MultiEvent):
            return self.current_event.subevents
        raise ValueError("Unexpected event type encountered")

    def refresh_all(self) -> None:
        readers = (self.read_events, self.read_runners, self.read_schedules, self.read_incentives)
        for reader in utils.show_iterable_progress(readers, color=self.color):
            reader()

    def read_events(self) -> None:
        events = gdq_api.get_events(self.url)
        if not events:
            raise IndexError(f"Couldn't find any events at {self.url}")

        for event in events:
            if event.short_name in self.record_offsets:
                event.offset = self.record_offsets[event.short_name]

        self.current_event = events.pop(self.stream_index)

        self.records = sorted(events, key=operator.attrgetter("total"))

    def read_runners(self) -> None:
        for event in self.current_events:
            self.runners.update(gdq_api.get_runners_for_event(self.url, event.event_id))

    def read_schedules(self) -> None:
        self.schedules = []
        for event in self.current_events:
            self.schedules.append(gdq_api.get_runs(self.url, event.event_id))

    def read_incentives(self) -> None:
        for event in self.current_events:
            self.incentives.update(gdq_api.get_incentives_for_event(self.url, event.event_id, currency=self.currency))

    def display(self, args: argparse.Namespace) -> bool:
        row_index = 1
        row_index += self.display_milestone(args)

        if args.split_pane:
            return self.display_split(args, row_index)
        return self._real_display(args, row_index)

    def display_milestone(self, args: argparse.Namespace) -> int:
        extra_lines = 0
        print("\x1b[H", end="")

        if args.extended_header and self.current_event.charity:
            header = self.current_event.name
            if self.current_event.charity:
                header += f" supporting {self.current_event.charity}"
            print(header.center(utils.term_width))
            extra_lines += 1

        last_record: Union[Event, FakeRecord] = FakeRecord(total=self.currency(), short_name="GO!")
        for record in self.records:
            if record.total > self.total:
                break
            last_record = record
        else:
            record = self.current_event

        trim = len(last_record.short_name) + len(record.short_name) + 2
        bar_width = utils.term_width - trim
        prog_bar = money.progress_bar_money(last_record.total, self.total, record.total, width=bar_width)
        print(f"{last_record.short_name.upper()} {prog_bar} {record.short_name.upper()}")
        extra_lines += 1

        total = self.total
        for event in self.records:
            total += event.total

        return extra_lines

    def display_split(self, args: argparse.Namespace, row_index: int) -> bool:
        column_width = utils.term_width // 2
        height = (utils.term_height - row_index - 1) // len(self.schedules)
        rendered_schedules: List[List[str]] = [[]]

        args.hide_basic = False
        args.hide_incentives = True
        for schedule in self.schedules:
            schedule_lines: List[str] = []
            for run in schedule:
                schedule_lines.extend(self.format_run(run, args, column_width))
                if len(schedule_lines) >= height:
                    break
            rendered_schedules[0].extend(schedule_lines)

        schedule_lines = []
        args.hide_basic = True
        args.hide_incentives = False
        combined_schedules = sorted([run for schedule in self.schedules for run in schedule], key=lambda r: r.start)

        for run in combined_schedules:
            schedule_lines.extend(self.format_run(run, args, column_width))
            if len(schedule_lines) >= utils.term_height:
                break
        rendered_schedules.append(schedule_lines)

        padding = " " * column_width
        return self._display_schedules(rendered_schedules, padding, row_index)

    def format_run(self, run: Run, args: argparse.Namespace, width: int = 80) -> Iterable[str]:
        run_desc = list(super().format_run(run, args, width))
        incentives = self.incentives.get(run.game, [])

        if args.hide_incentives or not run_desc:
            return run_desc

        width -= 8
        # Handle incentives
        incentive_desc = []
        if incentives:
            align_width = max(args.min_width, *(len(incentive) for incentive in incentives))
            for incentive in sorted(incentives, key=operator.attrgetter("incentive_id")):
                incentive_desc.extend(incentive.render(width, align_width, args))

        if args.hide_basic and not incentive_desc:
            return []

        return run_desc + incentive_desc
