# Copyright 2026
# SPDX-License-Identifier: MIT
from bus.utils import RATE, dollars_to_hours, hours_to_dollars
from common.money import Dollar


def test_conversion() -> None:
    """Test conversion for rounding errors."""
    total = 0
    for hours in range(1, 50):
        total += RATE ** (hours - 1)

        dollars = Dollar(total)
        assert hours_to_dollars(hours) == dollars
        assert dollars_to_hours(dollars) == hours

        # Also make sure previous cent is previous hour
        assert dollars_to_hours(dollars - Dollar(0.01)) == hours - 1
