import shutil
import time
from collections.abc import Collection, Iterable
from datetime import datetime, timedelta, timezone
from typing import TypeVar

X = TypeVar("X")
now: datetime = datetime.now(timezone.utc)


def flatten(string: str) -> str:
    translation = str.maketrans("┼╫┤", "┬╥┐")
    return string.translate(translation)


def progress_bar(start: float, current: float, end: float, width: int) -> str:
    chars = " ▏▎▍▌▋▊▉█"

    try:
        percent = ((current - start) / (end - start) * 100)
    except ZeroDivisionError:
        percent = 0

    blocks, fraction = 0, 0
    if percent:
        divparts = divmod(percent * width, 100)
        blocks = int(divparts[0])
        fraction = int(divparts[1] // (100 / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1
    remainder = (width - blocks - 1)
    return f"{chars[-1] * blocks}{chars[fraction]}{' ' * remainder}"


def short_number(number: float) -> str:
    if number >= 1_000_000:
        number = number // 10_000 / 100
        return f"{number:.2f}M"
    if number >= 100_000:
        number = number // 1_000
        return f"{number:.0f}k"
    if number >= 10_000:
        number = number // 100 / 10
        return f"{number:.1f}k"
    if number < 100:
        return f"{number:.2f}"
    return f"{number:,.0f}"


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
            flush=True
        )
        yield item


def timedelta_as_hours(delta: timedelta) -> str:
    """Format a timedelta in HHH:MM format."""

    minutes = delta.total_seconds() // 60
    hours, minutes = divmod(minutes, 60)

    return f"{hours:.0f}:{minutes:02.0f}"


def update_now() -> datetime:
    global now
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now
