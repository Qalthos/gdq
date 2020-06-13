import operator
from collections import namedtuple
from typing import Dict, Iterable, List, Union

from gdq import money, utils
from gdq.events import MarathonBase
from gdq.models import Event, Incentive, Run, Runner, SingleEvent
from gdq.parsers import gdq_api

FakeRecord = namedtuple("FakeRecord", ["short_name", "total"])


class GDQTracker(MarathonBase):
    # Tracker base URL
    url: str

    # Historical donation records
    records: List[Event] = []

    # Cached live data
    current_event: Event
    runners: Dict[int, Runner] = {}
    incentives: Dict[str, List[Incentive]] = {}

    # Set to account for discrepencies between computed and reported totals.
    offset: float

    def __init__(self, url: str = None, stream_index: int = -1, offset: float = 0) -> None:
        self.url = url or self.url
        self.stream_index = stream_index
        self.offset = offset

    @property
    def total(self) -> money.Money:
        return self.current_event.total - self.offset

    @property
    def current_events(self) -> List[SingleEvent]:
        events = getattr(self.current_event, "subevents", None)
        if not events:
            events = [self.current_event]
        return events

    def refresh_all(self) -> None:
        readers = (self.read_events, self.read_runners, self.read_schedules, self.read_incentives)
        for reader in utils.show_iterable_progress(readers):
            reader()

    def read_events(self) -> None:
        events = gdq_api.get_events(self.url)
        if not events:
            raise IndexError(f"Couldn't find any events at {self.url}")

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
            self.incentives.update(gdq_api.get_incentives_for_event(self.url, event.event_id))

    def display(self, args, row_index=1) -> bool:
        row_index += self.display_milestone(args)

        if args.split_pane:
            return self.display_split(args, row_index)
        return super().display(args, row_index)

    def display_milestone(self, args) -> int:
        extra_lines = 0
        print("\x1b[H", end="")

        if args.extended_header and self.current_event.charity:
            header = self.current_event.name
            if self.current_event.charity:
                header += f" supporting {self.current_event.charity}"
            print(header.center(utils.term_width))
            extra_lines += 1

        last_record: Union[Event, FakeRecord] = FakeRecord(total=type(self.total)(0), short_name="GO!")
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

    def display_split(self, args, row_index):
        column_width = utils.term_width // 2
        height = (utils.term_height - row_index - 1) // len(self.schedules)
        rendered_schedules = [[]]

        args.hide_basic = False
        args.hide_incentives = True
        for schedule in self.schedules:
            schedule_lines = []
            for run in schedule:
                schedule_lines.extend(self.format_run(run, column_width, args))
                if len(schedule_lines) >= height:
                    break
            rendered_schedules[0].extend(schedule_lines)

        schedule_lines = []
        args.hide_basic = True
        args.hide_incentives = False
        combined_schedules = sorted([run for schedule in self.schedules for run in schedule], key=lambda r: r.start)

        for run in combined_schedules:
            schedule_lines.extend(self.format_run(run, column_width, args))
            if len(schedule_lines) >= utils.term_height:
                break
        rendered_schedules.append(schedule_lines)

        padding = " " * column_width
        return self._real_display(rendered_schedules, padding, row_index)

    def format_run(self, run: Run, width: int = 80, args=None) -> Iterable[str]:
        run_desc = list(super().format_run(run, width))
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
