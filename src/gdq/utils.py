import shutil
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypeVar

from common.progress_bar import progress_bar

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

X = TypeVar("X")
now: datetime = datetime.now(UTC)


def flatten(string: str) -> str:
    translation = str.maketrans("┼╫┤", "┬╥┐")
    return string.translate(translation)


def slow_refresh_with_progress(interval: int = 30) -> Iterable[int]:
    resolution = 0.10
    ticks = int(interval / resolution)

    term_width, term_height = shutil.get_terminal_size()
    # Don't bother updating the progress bar more often than necessary
    if ticks > term_width * 8:
        ticks = term_width * 8
        resolution = interval / ticks

    for i in range(ticks):
        # Get new terminal width
        term_width, term_height = shutil.get_terminal_size()
        repaint_progress = progress_bar(0, i, ticks, width=term_width)
        print(f"\x1b[{term_height}H{repaint_progress}", end="", flush=True)
        yield i
        time.sleep(resolution)


def show_iterable_progress(iterable: Collection[X], offset: int = 0) -> Iterable[X]:
    for i, item in enumerate(iterable):
        term_width, term_height = shutil.get_terminal_size()
        print(
            f"\x1b[{term_height - offset}H{progress_bar(0, i + 1, len(iterable), width=term_width)}",
            end="",
            flush=True,
        )
        yield item


def update_now() -> datetime:
    global now
    now = datetime.now(UTC).replace(microsecond=0)
    return now
