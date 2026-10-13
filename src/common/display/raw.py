# Copyright 2022
# SPDX-License-Identifier: MIT
import shutil
from typing import TYPE_CHECKING

from common.display import Display, SquishableString, String

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class RawDisplay(Display):
    _header_size: int = 0
    _footer_size: int = 0

    def __init__(self) -> None:
        self.refresh_terminal()

    def refresh_terminal(self) -> None:
        self.term_w, self.term_h = shutil.get_terminal_size()

    def update_header(self, lines: Sequence[String]) -> None:
        self._header_size = len(lines)
        self._print(lines)

    def update_body(self, lines: Iterable[String]) -> None:
        max_len = self.term_h - self._header_size - self._footer_size - 1
        self._print(lines, self._header_size, max_len)

    def update_footer(self, lines: Sequence[String]) -> None:
        self._footer_size = len(lines)
        footer_start = self.term_h - self._footer_size
        self._print(lines, footer_start)

    def _print(self, lines: Iterable[String], offset: int = 0, max_len: int = 0) -> None:
        for i, line in enumerate(lines):
            line_no = offset + i + 1
            line = line.render(self.term_w) if isinstance(line, SquishableString) else line  # noqa: PLW2901

            print(f"\x1b[{line_no}H{line}", end="\x1b[K")

            if max_len and i >= max_len:
                break
        else:
            if max_len:
                # Clear the rest of the screen
                print("\x1b[J", end="")
        print(flush=True, end="")
