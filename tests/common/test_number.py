# Copyright 2026
# SPDX-License-Identifier: MIT
import pytest

from common.number import short_number


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1.234, "1.23"),
        (1234, "1,234"),
        (12340, "12.3k"),
        (123400, "123k"),
        (1234000, "1.23M"),
    ],
)
def test_small(value: float, expected: str) -> None:
    assert short_number(value) == expected
