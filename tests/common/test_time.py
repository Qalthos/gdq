# Copyright 2026
# SPDX-License-Identifier: MIT
from datetime import timedelta

import pytest

from common.time import timedelta_as_hours


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (timedelta(minutes=3), "0:03"),
        (timedelta(minutes=90), "1:30"),
        (timedelta(hours=90), "90:00"),
        (timedelta(days=9), "216:00"),
    ],
)
def test_timedelta_to_hours(delta: timedelta, expected: str) -> None:
    assert timedelta_as_hours(delta) == expected
