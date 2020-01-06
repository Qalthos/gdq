from typing import Final, Generator, List

from gdq import utils
from gdq.events import MarathonBase
from gdq.models import PREFIX, Event, SingleEvent, Run
from gdq.parsers import gdq_api


MIN_OFFSET: Final[int] = 20


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

        self.runners = {}
        for event in self.current_events:
            self.runners.update(gdq_api.get_runners_for_event(self.url, event.event_id))

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
        self.schedules = [gdq_api.get_runs(self.url, event.event_id) for event in self.current_events]
        self.read_incentives()

    def read_events(self) -> None:
        events = list(gdq_api.get_events(self.url))
        self.current_event = events.pop(-1)

        self.records = sorted([(event.total, event.short_name.upper()) for event in events])

    def read_incentives(self) -> None:
        incentives = {}
        for event in self.current_events:
            incentives.update(gdq_api.get_incentives_for_event(self.url, event.event_id))
        self.incentives = incentives

    def display(self, args, row_index=1) -> bool:
        row_index += self.display_milestone()
        return super().display(args, row_index)

    def display_milestone(self) -> int:
        extra_lines = 1

        last_record = (0, "")
        for record in self.records:
            if record[0] > self.total:
                relative_percent = (self.total - last_record[0]) / (record[0] - last_record[0]) * 100
                bar = utils.show_progress(relative_percent, width=(utils.term_width - 12))
                print(f"\x1b[2H{utils.short_number(last_record[0]): <5s}▕{bar}▏{utils.short_number(record[0]): >5s}")
                extra_lines += 1
                break
            last_record = record
        else:
            record = (0, "NEW HIGH SCORE!")

        max_len = max((len(last_record[1]), len(record[1])))
        dollar_total = f"${self.total:,.2f}"
        dollar_total = f"{dollar_total: ^{utils.term_width - (2 * max_len)}s}"
        print(f"\x1b[H{last_record[1]: <{max_len}s}{dollar_total}{record[1]: >{max_len}s}")

        return extra_lines

    def format_run(self, run: Run, width: int = 80, args=None) -> Generator[str, None, None]:
        width -= len(PREFIX) + 1
        run_desc = list(super().format_run(run, width))

        if not run_desc:
            return
        for line in run_desc:
            yield line

        incentives = self.incentives.get(run.game, [])
        if incentives:
            align_width = max(MIN_OFFSET, *(len(incentive) for incentive in incentives))
            # Handle incentives
            for incentive in incentives:
                yield from incentive.render(width, align_width, args)
