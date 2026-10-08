# Copyright 2026
# SPDX-License-Identifier: MIT
from common.money import Money


def progress_bar(start: float, current: float, end: float, width: int) -> str:
    chars = " ▏▎▍▌▋▊▉█"

    try:
        percent = (current - start) / (end - start) * 100
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
    remainder = width - blocks - 1
    return f"{chars[-1] * blocks}{chars[fraction]}{' ' * remainder}"


def progress_bar_money[M: Money](start: M, current: M, end: M, width: int) -> str:
    width -= 8

    if start:
        width -= 6

    if current >= end:
        prog_bar = progress_bar(
            start.to_float(),
            current.to_float(),
            end.to_float(),
            width,
        )
    else:
        chars = " ▏▎▍▌▋▊▉█"

        percent = (current - start) / (end - start) * 100 if (end - start).to_float() > 0 else 0

        blocks, fraction = 0, 0
        if percent:
            divparts = divmod(percent * width, 100)
            blocks = int(divparts[0])
            fraction = int(divparts[1] // (100 / len(chars)))

        if blocks >= width:
            blocks = width - 1
            fraction = -1
        remainder = width - blocks - 1

        if remainder > blocks:
            suffix = " " * (remainder - len(current))
            prog_bar = f"{chars[-1] * blocks}{chars[fraction]}{current}{suffix}"
        else:
            prefix = chars[-1] * (blocks - len(current))
            prog_bar = f"{prefix}\x1b[7m{current}\x1b[m{chars[fraction]}{' ' * remainder}"

    if start:
        return f"{start.short: <6s}▕{prog_bar}▏{end.short: >6s}"
    return f"▕{prog_bar}▏{end.short: >6s}"
