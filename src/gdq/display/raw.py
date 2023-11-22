"""
========header========
| col1 | col2 | col3 |
========footer========
"""
import shutil
from collections.abc import Iterable


class Display:
    _header_size: int = 0
    _footer_size: int = 0
    term_w: int
    term_h: int

    def __init__(self):
        self.refresh_terminal()

    def refresh_terminal(self) -> None:
        self.term_w, self.term_h = shutil.get_terminal_size()

    def update_header(self, header: Iterable[str]) -> None:
        print("\x1b[H", end="")

        self._header_size = 0
        for line in header:
            print(line)
            self._header_size += 1

    def update_body(self, body: Iterable[str]) -> None:
        current_line = self._header_size

        for line in body:
            current_line += 1
            print(f"\x1b[{current_line}H{line}", end="\x1b[K")

            if current_line == self.term_h - self._footer_size:
                break
        else:
            # Clear the rest of the screen
            print("\x1b[J", end="")

    def update_footer(self, footer: Iterable[str]) -> None:
        footer = list(footer)

        self._footer_size = len(footer)
        footer_start = self.term_h - self._footer_size + 1
        for index, line in enumerate(footer):
            print(f"\x1b[{footer_start + index}H{line}", end="")
