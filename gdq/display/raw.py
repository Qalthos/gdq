"""
========header========
| col1 | col2 | col3 |
========footer========
"""
import argparse
import shutil
from collections.abc import Iterable

from gdq import money, utils
from gdq.models import Event, Run


class Display:
    _header_size: int = 1
    term_w: int
    term_h: int

    def __init__(self):
        self.refresh_terminal()

    def refresh_terminal(self) -> None:
        self.term_w, self.term_h = shutil.get_terminal_size()

    def update_header(self, header: Iterable[str]) -> None:
        self.refresh_terminal()
        print("\x1b[H", end="")

        self._header_size = 1
        for line in header:
            print(line)
            self._header_size += 1

    def update_body(self, body: Iterable[str]) -> None:
        self.refresh_terminal()
        current_line = self._header_size

        for line in body:
            if current_line == self.term_h:
                break
            print(f"\x1b[{current_line}H{line}", end="")
            current_line += 1
        else:
            # Clear the rest of the screen
            print("\x1b[J", end="")
