# Copyright 2022
# SPDX-License-Identifier: MIT
from __future__ import annotations

from abc import ABC
from functools import total_ordering
from typing import Self

from common.number import short_number


@total_ordering
class Money(ABC):  # noqa: PLW1641
    _value: int
    _symbol: str
    _exponent: int = 0

    def __init__(self, value: float = 0):
        self._value = round(value * (10**self._exponent))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_float()})"

    def __bool__(self) -> bool:
        return bool(self._value)

    def __len__(self) -> int:
        return len(str(self))

    @property
    def symbol(self) -> str:
        return self._symbol

    # Operator methods
    def __neg__(self: Self) -> Self:
        result = type(self)()
        result._value = -self._value  # noqa: SLF001
        return result

    def __add__(self: Self, other: Self) -> Self:
        result = type(self)()
        result._value = self._value + other._value
        return result

    def __sub__(self: Self, other: Self) -> Self:
        result = type(self)()
        result._value = self._value - other._value
        return result

    def __mul__(self: Self, other: float) -> Self:
        result = type(self)()
        result._value = round(self._value * other)
        return result

    def __truediv__(self: Self, other: Self) -> float:
        return self._value / other._value

    # Ordering methods
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            err = f"unsupported operand type(s) for ==: '{type(self).__name__}' and '{type(other).__name__}'"
            raise TypeError(err)
        return bool(self._value == other._value)

    def __lt__(self: Self, other: Self) -> bool:
        return self._value < other._value

    # Casting methods
    def __str__(self) -> str:
        return f"{self.symbol}{self.to_float():,.0{self._exponent}f}"

    def to_float(self) -> float:
        return float(self._value / (10**self._exponent))

    @property
    def short(self) -> str:
        return f"{self.symbol}{short_number(self.to_float())}"


class Dollar(Money):
    _symbol = "$"
    _exponent = 2


class CanadianDollar(Dollar):
    _symbol = "C$"


class Euro(Money):
    _symbol = "€"
    _exponent = 2


CURRENCIES: dict[str, type[Money]] = {
    "CAD": CanadianDollar,
    "EUR": Euro,
    "USD": Dollar,
}
