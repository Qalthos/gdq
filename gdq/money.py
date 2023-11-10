from __future__ import annotations

from abc import ABC
from typing import Self, TypeVar

from gdq import utils

M = TypeVar("M", bound="Money")


def progress_bar_money(start: M, current: M, end: M, width: int) -> str:
    width -= 8

    if start:
        width -= 6

    if current >= end:
        prog_bar = utils.progress_bar(
            start.to_float(),
            current.to_float(),
            end.to_float(),
            width,
        )
    else:
        chars = " ▏▎▍▌▋▊▉█"

        percent = (
            (current - start) / (end - start) * 100
            if (end - start).to_float() > 0
            else 0
        )

        blocks, fraction = 0, 0
        if percent:
            divparts = divmod(percent * width, 100)
            blocks = int(divparts[0])
            fraction = int(divparts[1] // (100 / len(chars)))

        if blocks >= width:
            blocks = width - 1
            fraction = -1
        remainder = width - blocks - 1

        if remainder > blocks:
            suffix = " " * (remainder - len(current))
            prog_bar = f"{chars[-1] * blocks}{chars[fraction]}{current}{suffix}"
        else:
            prefix = chars[-1] * (blocks - len(current))
            prog_bar = (
                f"{prefix}\x1b[7m{current}\x1b[m{chars[fraction]}{' ' * remainder}"
            )

    if start:
        return f"{start.short: <6s}▕{prog_bar}▏{end.short: >6s}"
    return f"▕{prog_bar}▏{end.short: >6s}"


class Money(ABC):
    value: int
    _symbol: str
    _exponent: int = 0

    def __init__(self: Self, value: float = 0) -> None:
        self.value = round(value * (10**self._exponent))

    def __repr__(self: Self) -> str:
        return f"{type(self).__name__}({self.to_float()})"

    def __bool__(self: Self) -> bool:
        return bool(self.value)

    def __len__(self: Self) -> int:
        return len(str(self))

    @property
    def symbol(self: Self) -> str:
        return self._symbol

    # Operator methods
    def __neg__(self: Self) -> Self:
        result = type(self)()
        result.value = -self.value
        return result

    def __add__(self: Self, other: Self) -> Self:
        result = type(self)()
        result.value = self.value + other.value
        return result

    def __sub__(self: Self, other: Self) -> Self:
        result = type(self)()
        result.value = self.value - other.value
        return result

    def __mul__(self: Self, other: float) -> Self:
        result = type(self)()
        result.value = round(self.value * other)
        return result

    def __truediv__(self: Self, other: Self) -> float:
        return self.value / other.value

    # Ordering methods
    def __eq__(self: Self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return bool(self.value == other.value)

    def __lt__(self: Self, other: Self) -> bool:
        return self.value < other.value

    def __le__(self: Self, other: Self) -> bool:
        return self.value <= other.value

    def __gt__(self: Self, other: Self) -> bool:
        return self.value > other.value

    def __ge__(self: Self, other: Self) -> bool:
        return self.value >= other.value

    # Casting methods
    def __str__(self: Self) -> str:
        return f"{self.symbol}{self.to_float():,.0{self._exponent}f}"

    def to_float(self: Self) -> float:
        return float(self.value / (10**self._exponent))

    @property
    def short(self: Self) -> str:
        return f"{self.symbol}{utils.short_number(self.to_float())}"


class Dollar(Money):
    _symbol = "$"
    _exponent = 2


class Euro(Money):
    _symbol = "€"
    _exponent = 2


CURRENCIES: dict[str, type[Money]] = {
    "EUR": Euro,
    "USD": Dollar,
}
