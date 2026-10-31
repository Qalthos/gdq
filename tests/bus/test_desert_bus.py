# Copyright 2024
# SPDX-License-Identifier: MIT
from bus import desert_bus
from bus.shifts import Shift
from bus.utils import dollars_to_hours
from common.money import Dollar


def test_desert_buck() -> None:
    assert desert_bus.DesertBuck(Dollar(22805)).to_float() == 1


def test_desert_toonie() -> None:
    assert desert_bus.DesertToonie(Dollar(70423.79)).to_float() == 1


def test_next_hours() -> None:
    hours = desert_bus.next_hours(Dollar(0))
    for i in range(1, 48):
        next_hour, _ = next(hours)
        assert i == dollars_to_hours(next_hour.total)


def test_fun_numbers() -> None:
    hours = desert_bus.fun_numbers(Dollar(5500))
    numbers = [6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000, 15000, 20000]
    for number in numbers:
        next_hour, _ = next(hours)
        assert next_hour.total.to_float() == number


def test_even_banner_short() -> None:
    items = ["a", "betabetab", "c", "d"]
    width = 23

    output = desert_bus.even_banner(items, width)
    assert len(output) == width
    assert output == " a |betabetab| c |  d  "


def test_even_banner_long() -> None:
    items = ["a", "b", "c"]
    width = 10

    output = desert_bus.even_banner(items, width)
    assert len(output) == width
    assert output == " a | b |c "


def test_even_shift_banner() -> None:
    shifts = [Shift(0, "shift 1", -1), Shift(0, "shift 2", -1)]
    width = 19

    output = desert_bus.even_shift_banner(shifts, width)
    assert output == "\x1b[0;2m=shift 1=\x1b[0m|\x1b[0;2m=shift 2=\x1b[0m"
