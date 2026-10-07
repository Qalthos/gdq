# Copyright 2024
# SPDX-License-Identifier: MIT
from bus.desert_bus import DesertBuck, DesertToonie, next_hours
from bus.utils import dollars_to_hours
from gdq.money import Dollar


def test_desert_buck():
    assert DesertBuck(Dollar(22805)).to_float() == 1


def test_desert_toonie():
    assert DesertToonie(Dollar(70423.79)).to_float() == 1


def test_next_hours():
    hours = next_hours(Dollar(0))
    for i in range(1, 10):
        next_hour, _ = next(hours)
        assert i == dollars_to_hours(next_hour.total)
