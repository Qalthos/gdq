# Copyright 2026
# SPDX-License-Identifier: MIT
import math

from gdq.money import Dollar

RATE = 1.07


def dollars_to_hours(dollars: Dollar) -> int:
    # NOTE: This is not reflexive with hours_to_dollars
    # Slight correction factor to account for sub-cent losses
    raw_value = dollars.to_float() + 0.005
    value = math.log((RATE - 1) * raw_value + 1) / math.log(RATE)
    return math.floor(value)


def hours_to_dollars(hours: int) -> Dollar:
    value = (RATE**hours - 1) / (RATE - 1)
    return Dollar(value)
