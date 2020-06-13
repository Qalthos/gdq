from __future__ import annotations
from abc import ABC, abstractmethod
import functools
from typing import Dict
from typing import Type
from typing import TypeVar

from gdq import utils


@functools.total_ordering
class Money(ABC):
    _value: int
    _symbol: str = "?"

    def __init__(self, value: float):
        self._value = int(value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_float()})"

    # Operator methods
    def __add__(self, other: Money) -> Money:
        self._validate(other)

        result = type(self)(0)
        result._value = self._value + other._value
        return result

    def __sub__(self, other: Money) -> Money:
        self._validate(other)

        result = type(self)(0)
        result._value = self._value - other._value
        return result

    def __mul__(self, other: float) -> Money:
        result = type(self)(0)
        result._value = round(self._value * other)
        return result

    def __truediv__(self, other: Money) -> float:
        self._validate(other)

        return self._value / other._value

    # Ordering methods
    def __eq__(self, other) -> bool:
        self._validate(other)
        return self._value == other._value

    def __lt__(self, other) -> bool:
        self._validate(other)
        return self._value < other._value

    # Casting methods
    def __str__(self) -> str:
        return f"{self._symbol}{self._value}"

    def to_float(self) -> float:
        return float(self._value)

    @property
    @abstractmethod
    def short(self):
        return NotImplementedError

    # Type validation check
    def _validate(self, other) -> None:
        if not isinstance(other, type(self)):
            raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__class__}'")


class DecimalMoney(Money):
    def __init__(self, value: float):
        self._value = round(value * 100)

    def __str__(self) -> str:
        return f"{self._symbol}{self.to_float():02d}"

    def to_float(self) -> float:
        return self._value / 100

    @property
    def short(self):
        return f"{self._symbol}{utils.short_number(self.to_float())}"


class Dollar(DecimalMoney):
    _symbol = "$"


class Euro(DecimalMoney):
    _symbol = "€"


CURRENCIES: Dict[str, Type[Money]] = {
    "EUR": Euro,
    "USD": Dollar,
}
