from datetime import datetime, timezone
import shutil
import time


now: datetime = datetime.now(timezone.utc)
term_width, term_height = shutil.get_terminal_size()


def update_now():
    global now
    now = datetime.now(timezone.utc)
    return now


def show_progress(percent: float, width: int = term_width, out_of: float = 100) -> str:
    chars = " ▏▎▍▌▋▊▉█"

    blocks, fraction = 0, 0
    if percent:
        blocks, fraction = divmod(percent * width, out_of)
        blocks = int(blocks)
        fraction = int(fraction // (out_of / len(chars)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1

    return chars[-1] * blocks + chars[fraction] + " " * (width - blocks - 1)


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

        repaint_progress = show_progress(i, term_width, out_of=ticks)
        print(f"\x1b[{term_height}H{repaint_progress}", end="", flush=True)
        time.sleep(resolution)


def short_number(number: float) -> str:
    if number > 1e6:
        return "{0:.2f}M".format(number / 1e6)
    if number > 100e3:
        return "{0:.0f}k".format(number / 1e3)
    if number > 10e3:
        return "{0:.1f}k".format(number / 1e3)
    return f"{number:,.0f}"


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
