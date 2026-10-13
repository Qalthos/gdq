# Copyright 2026
# SPDX-License-Identifier: MIT
import pytest

from common.money import Dollar, Euro


def test_money() -> None:
    """Test various properties of Money."""
    dollar = Dollar(5.095)
    assert repr(dollar) == "Dollar(5.1)"
    assert dollar
    assert str(dollar) == "$5.10"
    assert len(dollar) == 5
    assert -dollar == Dollar(-5.1)
    assert dollar * 2 == Dollar(10.2)


def test_zero_money_falsy() -> None:
    dollar = Dollar(0)
    assert not dollar


def test_long_money() -> None:
    dollar = Dollar(1000000)
    assert dollar.short == "$1.00M"


def test_money_incomparable() -> None:
    dollar = Dollar(1)
    euro = Euro(1)

    with pytest.raises(TypeError):
        assert dollar != euro
