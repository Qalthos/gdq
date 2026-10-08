# Copyright 2026
# SPDX-License-Identifier: MIT
from bus.db_api import get_events, get_series


def test_series():
    serieses = get_series()
    assert len(serieses) == 2


def test_events():
    events = get_events()
    assert len(events) > 10
