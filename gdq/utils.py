from datetime import datetime, timezone
import shutil
import time


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
        blocks, fraction = divmod(percent * width, 100)
        blocks = int(blocks)
        fraction = int(fraction // (100 / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1
    remainder = (width - blocks - 1)
    return f"{chars[-1] * blocks}{chars[fraction]}{' ' * remainder}"


def progress_bar_decorated(start: float, current: float, end: float, width: int = term_width) -> str:
    if end - start > 0:
        percent = ((current - start) / (end - start) * 100)
    else:
        percent = 0

    width -= 7
    chars = " ▏▎▍▌▋▊▉█"

    if start:
        width -= 5

    if current >= end:
        bar = progress_bar(start, current, end, width)
    else:
        blocks, fraction = 0, 0
        if percent:
            blocks, fraction = divmod(percent * width, 100)
            blocks = int(blocks)
            fraction = int(fraction // (100 / len(chars)))

        if blocks >= width:
            blocks = width - 1
            fraction = -1
        remainder = (width - blocks - 1)

        current = short_number(current)
        if remainder > blocks:
            suffix = " " * (remainder - len(current))
            bar = f"{chars[-1] * blocks}{chars[fraction]}{current}{suffix}"
        else:
            prefix = chars[-1] * (blocks - len(current))
            bar = f"{prefix}\x1b[7m{current}\x1b[m{chars[fraction]}{' ' * remainder}"

    if start:
        return f"{short_number(start): <5s}▕{bar}▏{short_number(end): >5s}"
    return f"▕{bar}▏{short_number(end): >5s}"


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


def slow_progress_bar(interval=30):
    resolution = 0.10
    ticks = int(interval / resolution)

    # Don't bother updating the progress bar more often than necessary
    if ticks > term_width * 8:
        ticks = term_width * 8
        resolution = interval / ticks

    for i in range(ticks):
        if terminal_refresh():
            # Terminal shape has changed, skip the countdown and repaint early.
            break

        repaint_progress = progress_bar(0, i, ticks, width=term_width)
        print(f"\x1b[{term_height}H{repaint_progress}", end="", flush=True)
        time.sleep(resolution)


def terminal_refresh() -> bool:
    """Refresh terminal geometry

    Returns True if geometry has changed, False otherwise.
    """
    global term_width, term_height
    geom = shutil.get_terminal_size()
    if geom != (term_width, term_height):
        term_width, term_height = geom
        return True
    return False


def update_now() -> datetime:
    global now
    now = datetime.now(timezone.utc)
    return now
