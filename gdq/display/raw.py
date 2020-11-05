"""
========header========
| col1 | col2 | col3 |
========footer========
"""
import argparse
import shutil
from collections import namedtuple

from gdq import money, utils
from gdq.models import Event, Run

FakeRecord = namedtuple("FakeRecord", ["short_name", "total"])


class Display:
    _header_size: int = 1
    term_w: int
    term_h: int

    def refresh_terminal(self) -> None:
        self.term_w, self.term_h = shutil.get_terminal_size()

    def update_header(self, event: Event, records: list[Event], args: argparse.Namespace) -> None:
        self.refresh_terminal()
        print("\x1b[H", end="")

        self._header_size = 1
        if args.extended_header and event.charity:
            header = f"{event.name} supporting {event.charity}"
            print(header.center(utils.term_width))
            self._header_size += 1

        last_record = FakeRecord(total=event.currency(), short_name="GO!")
        for record in records:
            if record.total > event.total:
                break
            last_record = record
        else:
            record = event

        trim = len(last_record.short_name) + len(record.short_name) + 2
        bar_width = utils.term_width - trim
        prog_bar = money.progress_bar_money(last_record.total, event.total, record.total, width=bar_width)
        print(f"{last_record.short_name.upper()} {prog_bar} {record.short_name.upper()}")
        self._header_size += 1

    def update_body(self, schedules: list[list[Run]], args: argparse.Namespace) -> None:
        self.refresh_terminal()
        current_line = self._header_size

        # TODO: Do this properly with columns
        schedule = schedules[0]
        for run in schedule:
            for line in run.render(width=self.term_w, args=args):
                if current_line == self.term_h:
                    break
                if current_line == self._header_size:
                    line = utils.flatten(line)
                print(f"\x1b[{current_line}H{line}", end="")
                current_line += 1
        else:
            # Clear the rest of the screen
            print("\x1b[J", end="")
