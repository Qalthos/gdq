# Copyright 2026
# SPDX-License-Identifier: MIT
from common.money import Money

CHARS = " ▏▎▍▌▋▊▉█"


def _progress_bar(start: float, current: float, end: float, width: int) -> tuple[int, int, int]:
    """Breaks down a range into consumable blocks.

    Returns:
        blocks: the number of filled blocks
        fraction: the index of CHARS to fill the interstitial block
        remainder: the number of empty blocks following
    """

    try:
        percent = (current - start) / (end - start) * 100
    except ZeroDivisionError:
        percent = 0

    blocks, fraction = 0, 0
    if percent:
        divparts = divmod(percent * width, 100)
        blocks = int(divparts[0])
        fraction = int(divparts[1] // (100 / len(CHARS)))

    if blocks >= width:
        blocks = width - 1
        fraction = -1
    remainder = width - blocks - 1
    return blocks, fraction, remainder


def progress_bar(start: float, current: float, end: float, width: int) -> str:
    blocks, fraction, remainder = _progress_bar(start, current, end, width)
    return f"{CHARS[-1] * blocks}{CHARS[fraction]}{' ' * remainder}"


def progress_bar_money[M: Money](start: M, current: M, end: M, width: int) -> str:
    width -= 7

    if start:
        # start will be printed in the bar later, so reserve that space
        width -= 7

    if width < len(current) * 2:
        err = "Screen too small to fit progress bar"
        raise RuntimeError(err)

    if current >= end:
        # The bar is full, so no printing on the bar
        prog_bar = progress_bar(
            start.to_float(),
            current.to_float(),
            end.to_float(),
            width,
        )
    else:
        blocks, fraction, remainder = _progress_bar(start.to_float(), current.to_float(), end.to_float(), width)

        # Write the current value in the bar. Take from the larger side
        if remainder > blocks:
            remainder -= len(current)
            text = f"{CHARS[fraction]}{current}"
        else:
            blocks -= len(current)
            text = f"\x1b[7m{current}\x1b[m{CHARS[fraction]}"
        prog_bar = f"{CHARS[-1] * blocks}{text}{' ' * remainder}"

    bar = f"{prog_bar}▏{end.short: >6s}"
    if start:
        bar = f"{start.short: <6s}▕{bar}"
    return bar
