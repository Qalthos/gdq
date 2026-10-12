# Copyright 2026
# SPDX-License-Identifier: MIT
from datetime import UTC, datetime

import pytest

from bus.db_api import Event, Logo, Series, get_events, get_series
from common.money import Dollar


@pytest.fixture
def fake_event() -> Event:
    return Event(
        id="NotARealEvent",
        name="FakeBus 2099",
        url="example.com",
        primary=False,
        starts_at=datetime(2000, 1, 1, tzinfo=UTC),
        logo=Logo(url="example.com/logo.png", alt=None, width=0, height=0),
        total=Dollar(20),
        series=Series(id="AlsoFake", name="Totally Fake Events"),
    )


def test_series() -> None:
    serieses = get_series()
    assert len(serieses) == 2


def test_events() -> None:
    events = get_events()
    assert len(events) > 10


def test_event(fake_event: Event) -> None:
    assert str(fake_event) == "FakeBus 2099"
    assert fake_event.hours == 12
    assert fake_event.distance(Dollar(5)) == "$15.00 until FakeBus 2099"
    assert fake_event.distance(Dollar(50)) == ""
