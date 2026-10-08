# Copyright 2026
# SPDX-License-Identifier: MIT
import pytest

from common.money import Dollar
from common.progress_bar import _progress_bar, progress_bar, progress_bar_money


def test_handle_zero_div() -> None:
    assert _progress_bar(100, 100, 100, 4) == (0, 0, 3)


def test_handle_overflow() -> None:
    assert _progress_bar(0, 150, 100, 4) == (3, -1, 0)


def test_progress_bar_basic() -> None:
    assert progress_bar(0, 50, 100, 4) == "██  "


@pytest.mark.parametrize(
    ("current_int", "expected"),
    [
        (0, " $0.00              ▏  $100"),
        (25, "█████ $25.00        ▏  $100"),
        (50, "████\x1b[7m$50.00\x1b[m          ▏  $100"),
        (75, "█████████\x1b[7m$75.00\x1b[m     ▏  $100"),
        (100, "████████████████████▏  $100"),
    ],
)
def test_money_bar(current_int: int, expected: str) -> None:
    start, current, end = Dollar(0), Dollar(current_int), Dollar(100)
    bar = progress_bar_money(start, current, end, 27)
    assert bar == expected


@pytest.mark.parametrize(
    ("current_int", "expected"),
    [
        (100, "$100  ▕ $100.00            ▏  $200"),
        (125, "$100  ▕█████ $125.00       ▏  $200"),
        (150, "$100  ▕███\x1b[7m$150.00\x1b[m          ▏  $200"),
        (175, "$100  ▕████████\x1b[7m$175.00\x1b[m     ▏  $200"),
        (200, "$100  ▕████████████████████▏  $200"),
    ],
)
def test_money_bar_start(current_int: int, expected: str) -> None:
    start, current, end = Dollar(100), Dollar(current_int), Dollar(200)
    bar = progress_bar_money(start, current, end, 34)
    assert bar == expected


def test_min_bar_size() -> None:
    start, current, end = Dollar(0), Dollar(5), Dollar(10)
    width = len(current) * 2 + 7
    bar = progress_bar_money(start, current, end, width)
    assert bar == "\x1b[7m$5.00\x1b[m     ▏$10.00"

    width -= 1
    with pytest.raises(RuntimeError, match="Screen too small to fit progress bar"):
        bar = progress_bar_money(start, current, end, width)
