import operator
from collections import namedtuple
from typing import Dict, List

from gdq import utils
from gdq.events import MarathonBase
from gdq.models import Event, SingleEvent, Run, Runner, Incentive
from gdq.parsers import gdq_api


FakeRecord = namedtuple("FakeRecord", ["short_name", "total"])


class GDQTracker(MarathonBase):
    # Historical donation records
    records: List[Event] = []

    # Cached live data
    current_event: Event
    runners: Dict[int, Runner] = {}
    incentives: Dict[str, Incentive] = {}

    def __init__(self, url: str = None, streams: int = 1) -> None:
        self.url = url or self.url
        self.display_streams = streams

    @property
    def total(self) -> float:
        return self.current_event.total

    @property
    def current_events(self) -> List[SingleEvent]:
        events = getattr(self.current_event, "subevents", None)
        if not events:
            events = [self.current_event]
        return events

    def refresh_all(self) -> None:
        self.read_events()
        self.read_runners()
        self.schedules = [gdq_api.get_runs(self.url, event.event_id) for event in self.current_events]
        self.read_incentives()

    def read_events(self) -> None:
        events = gdq_api.get_events(self.url)
        if events is None:
            return

        self.current_event = events.pop(-1)

        self.records = sorted(events, key=operator.attrgetter("total"))

    def read_runners(self) -> None:
        for event in self.current_events:
            self.runners.update(gdq_api.get_runners_for_event(self.url, event.event_id))

    def read_incentives(self) -> None:
        for event in self.current_events:
            self.incentives.update(gdq_api.get_incentives_for_event(self.url, event.event_id))

    def display(self, args, row_index=1) -> bool:
        row_index += self.display_milestone()

        if args.split_pane:
            return self.display_split(args, row_index)
        return super().display(args, row_index)

    def display_milestone(self) -> int:
        extra_lines = 1

        last_record = FakeRecord(total=0, short_name="")
        for record in self.records:
            if record.total > self.total:
                break
            last_record = record
        else:
            record = FakeRecord(total=self.total, short_name="!!!")

        trim = len(last_record.short_name) + len(record.short_name) + 2
        bar = utils.progress_bar_decorated(last_record.total, self.total, record.total, width=(utils.term_width - trim))
        print(f"\x1b[H{last_record.short_name.upper()} {bar} {record.short_name.upper()}")

        return extra_lines

    def display_split(self, args, row_index):
        rendered_schedules = []
        column_width = utils.term_width // 2

        schedule = self.schedules[0]
        schedule_lines = []
        args.hide_basic = False
        args.hide_incentives = True
        for run in schedule:
            schedule_lines.extend(self.format_run(run, column_width, args))
            if len(schedule_lines) >= utils.term_height:
                break
        rendered_schedules.append(schedule_lines)

        schedule_lines = []
        args.hide_basic = True
        args.hide_incentives = False
        for run in schedule:
            schedule_lines.extend(self.format_run(run, column_width, args))
            if len(schedule_lines) >= utils.term_height:
                break
        rendered_schedules.append(schedule_lines)

        padding = " " * column_width
        return self._real_display(rendered_schedules, padding, row_index)

    def format_run(self, run: Run, width: int = 80, args=None) -> List[str]:
        width -= 8
        run_desc = list(super().format_run(run, width))
        incentives = self.incentives.get(run.game, [])

        if args.hide_incentives or not run_desc:
            return run_desc

        # Handle incentives
        incentive_desc = []
        if incentives:
            align_width = max(args.min_width, *(len(incentive) for incentive in incentives))
            for incentive in sorted(incentives, key=operator.attrgetter("incentive_id")):
                incentive_desc.extend(incentive.render(width, align_width, args))

        if args.hide_basic and not incentive_desc:
            return []

        return run_desc + incentive_desc
