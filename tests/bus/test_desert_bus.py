# Copyright 2024
# SPDX-License-Identifier: MIT
from bus.desert_bus import DesertBuck, DesertToonie, fun_numbers, next_hours
from bus.utils import dollars_to_hours
from common.money import Dollar


def test_desert_buck() -> None:
    assert DesertBuck(Dollar(22805)).to_float() == 1


def test_desert_toonie() -> None:
    assert DesertToonie(Dollar(70423.79)).to_float() == 1


def test_next_hours() -> None:
    hours = next_hours(Dollar(0))
    for i in range(1, 48):
        next_hour, _ = next(hours)
        assert i == dollars_to_hours(next_hour.total)


def test_fun_numbers() -> None:
    hours = fun_numbers(Dollar(5500))
    numbers = [6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000, 15000, 20000]
    for number in numbers:
        next_hour, _ = next(hours)
        assert next_hour.total.to_float() == number
