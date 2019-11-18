from datetime import datetime, timezone
import shutil
import time


NOW: datetime = datetime.now(timezone.utc)


def show_progress(percent: float, width: int = 72, out_of: float = 100) -> str:
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


def slow_progress_bar(terminal, interval=30):
    resolution = 0.10
    ticks = int(interval / resolution)

    # Don't bother updating the progress bar more often than necessary
    if ticks > terminal.width * 8:
        ticks = terminal.width * 8
        resolution = interval / ticks

    for i in range(ticks):
        if terminal.refresh():
            # Terminal shape has changed, skip the countdown and repaint early.
            break

        repaint_progress = show_progress(i, terminal.width, out_of=ticks)
        print(f"\x1b[{terminal.height}H{repaint_progress}", end="", flush=True)
        time.sleep(resolution)


def short_number(number: float) -> str:
    if number > 1e6:
        return "{0:.2f}M".format(number / 1e6)
    if number > 100e3:
        return "{0:.0f}k".format(number / 1e3)
    if number > 10e3:
        return "{0:.1f}k".format(number / 1e3)
    return f"{number:,.0f}"


class Terminal:
    width: int = 0
    height: int = 0

    def __init__(self):
        self.refresh()

    def refresh(self) -> bool:
        """Refresh terminal geometry

        Returns True if geometry has changed, False otherwise.
        """
        geom = shutil.get_terminal_size()
        if geom != (self.width, self.height):
            self.width, self.height = geom
            return True
        return False
