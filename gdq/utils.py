import shutil
import time
from datetime import datetime, timezone
from typing import Collection, Iterable

now: datetime = datetime.now(timezone.utc)
term_width, term_height = shutil.get_terminal_size()


def flatten(string: str) -> str:
    translation = str.maketrans("┼╫┤", "┬╥┐")
    return string.translate(translation)


def join_char(left: str, right: str) -> str:
    choices = "║╟╢╫"
    pick = 0
    if left in "─┐┘┤":
        pick += 0b10
    if right == "─":
        pick += 0b01

    return choices[pick]


def progress_bar(start: float, current: float, end: float, width: int = term_width) -> str:
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


def slow_refresh_with_progress(interval: int = 30) -> Iterable:
    resolution = 0.10
    ticks = int(interval / resolution)

    # Don't bother updating the progress bar more often than necessary
    if ticks > term_width * 8:
        ticks = term_width * 8
        resolution = interval / ticks

    for i in range(ticks):
        # Get new terminal size
        terminal_refresh()
        repaint_progress = progress_bar(0, i, ticks, width=term_width)
        print(f"\x1b[{term_height}H{repaint_progress}", end="", flush=True)
        yield i
        time.sleep(resolution)


def show_iterable_progress(iterable: Collection) -> Iterable:
    for i, item in enumerate(iterable):
        print(f"\x1b[{term_width}H{progress_bar(0, i + 1, len(iterable))}", end="", flush=True)
        yield item


def terminal_refresh() -> None:
    """Refresh terminal geometry."""
    global term_width, term_height
    geom = shutil.get_terminal_size()
    if geom != (term_width, term_height):
        term_width, term_height = geom


def update_now() -> datetime:
    global now
    now = datetime.now(timezone.utc)
    return now
