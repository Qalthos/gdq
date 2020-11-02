from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

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

        if remainder > blocks:
            suffix = " " * (remainder - len(current))
            prog_bar = f"{chars[-1] * blocks}{chars[fraction]}{current}{suffix}"
        else:
            prefix = chars[-1] * (blocks - len(current))
            prog_bar = f"{prefix}\x1b[7m{current}\x1b[m{chars[fraction]}{' ' * remainder}"

    if start:
        return f"{start.short: <6s}▕{prog_bar}▏{end.short: >6s}"
    return f"▕{prog_bar}▏{end.short: >6s}"


class Money(ABC):
    _value: int
    _exponent: int = 0

    def __init__(self, value: float = 0):
        self._value = round(value * (10 ** self._exponent))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_float()})"

    def __bool__(self) -> bool:
        return bool(self._value)

    def __len__(self) -> int:
        return len(str(self))

    @property
    @abstractmethod
    def symbol(self) -> str:
        ...

    # Operator methods
    def __neg__(self: M) -> M:
        result = type(self)()
        result._value = -self._value
        return result

    def __add__(self: M, other: M) -> M:
        self._validate(other)

        result = type(self)()
        result._value = self._value + other._value
        return result

    def __sub__(self: M, other: M) -> M:
        self._validate(other)

        result = type(self)()
        result._value = self._value - other._value
        return result

    def __mul__(self: M, other: float) -> M:
        result = type(self)()
        result._value = round(self._value * other)
        return result

    def __truediv__(self: M, other: M) -> float:
        self._validate(other)

        return self._value / other._value

    # Ordering methods
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            raise TypeError(f"unsupported operand type(s) for ==: '{type(self).__name__}' and '{type(other).__name__}'")
        return bool(self._value == other._value)

    def __lt__(self: M, other: M) -> bool:
        self._validate(other)
        return self._value < other._value

    def __ge__(self: M, other: M) -> bool:
        self._validate(other)
        return self._value >= other._value

    # Casting methods
    def __str__(self) -> str:
        return f"{self.symbol}{self.to_float():,.0{self._exponent}f}"

    def to_float(self) -> float:
        return float(self._value / (10 ** self._exponent))

    @property
    def short(self) -> str:
        return f"{self.symbol}{utils.short_number(self.to_float())}"

    # Type validation check
    def _validate(self, other: Any) -> None:
        if not isinstance(other, type(self)):
            raise TypeError(f"unsupported operand type(s): '{type(self).__name__}' and '{type(other).__name__}'")


class Dollar(Money):
    symbol = "$"
    _exponent = 2


class Euro(Money):
    symbol = "€"
    _exponent = 2


CURRENCIES: dict[str, type[Money]] = {
    "EUR": Euro,
    "USD": Dollar,
}
