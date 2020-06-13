from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar

from gdq import utils

M = TypeVar("M", bound="Money")


def progress_bar_money(start: M, current: M, end: M, width: int = utils.term_width) -> str:
    width -= 8

    if start:
        width -= 6

    if current >= end:
        prog_bar = utils.progress_bar(start.to_float(), current.to_float(), end.to_float(), width)
    else:
        chars = " ▏▎▍▌▋▊▉█"

        if (end - start).to_float() > 0:
            percent = ((current - start) / (end - start) * 100)
        else:
            percent = 0

        blocks, fraction = 0, 0
        if percent:
            divparts = divmod(percent * width, 100)
            blocks = int(divparts[0])
            fraction = int(divparts[1] // (100 / len(chars)))

        if blocks >= width:
            blocks = width - 1
            fraction = -1
        remainder = (width - blocks - 1)

        current_str = current.short
        if remainder > blocks:
            suffix = " " * (remainder - len(current_str))
            prog_bar = f"{chars[-1] * blocks}{chars[fraction]}{current_str}{suffix}"
        else:
            prefix = chars[-1] * (blocks - len(current_str))
            prog_bar = f"{prefix}\x1b[7m{current_str}\x1b[m{chars[fraction]}{' ' * remainder}"

    if start:
        return f"{start.short: <6s}▕{prog_bar}▏{end.short: >6s}"
    return f"▕{prog_bar}▏{end.short: >6s}"


class Money(ABC):
    _value: int

    def __init__(self, value: float):
        self._value = int(value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_float()})"

    def __bool__(self):
        return bool(self._value)

    def __len__(self) -> int:
        return len(str(self))

    @property
    @abstractmethod
    def symbol(self):
        ...

    # Operator methods
    def __add__(self: M, other: M) -> M:
        self._validate(other)

        result = type(self)(0)
        result._value = self._value + other._value
        return result

    def __sub__(self: M, other: M) -> M:
        self._validate(other)

        result = type(self)(0)
        result._value = self._value - other._value
        return result

    def __mul__(self: M, other: float) -> M:
        result = type(self)(0)
        result._value = round(self._value * other)
        return result

    def __truediv__(self: M, other: M) -> float:
        self._validate(other)

        return self._value / other._value

    # Ordering methods
    def __eq__(self, other) -> bool:
        self._validate(other)
        return self._value == other._value

    def __lt__(self: M, other: M) -> bool:
        self._validate(other)
        return self._value < other._value

    def __ge__(self: M, other: M) -> bool:
        self._validate(other)
        return self._value >= other._value

    # Casting methods
    def __str__(self) -> str:
        return f"{self.symbol}{self._value}"

    def to_float(self) -> float:
        return float(self._value)

    @property
    @abstractmethod
    def short(self):
        return NotImplementedError

    # Type validation check
    def _validate(self: M, other: M) -> None:
        if not isinstance(other, type(self)):
            raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")


class DecimalMoney(Money):
    def __init__(self, value: float):
        self._value = round(value * 100)

    def __str__(self) -> str:
        return f"{self.symbol}{self.to_float():,.02f}"

    def to_float(self) -> float:
        return self._value / 100

    @property
    def short(self):
        return f"{self.symbol}{utils.short_number(self.to_float())}"


class Dollar(DecimalMoney):
    symbol = "$"


class Euro(DecimalMoney):
    symbol = "€"


CURRENCIES: Dict[str, Type[Money]] = {
    "EUR": Euro,
    "USD": Dollar,
}
