from __future__ import annotations


class Dollar:
    _value: int

    def __init__(self, value: float):
        self._value = round(value * 100)

    def __add__(self, other: Dollar) -> Dollar:
        result = Dollar(0)
        result._value = self._value + other._value
        return result

    def __mul__(self, other: float) -> Dollar:
        result = Dollar(0)
        result._value = round(self._value * other)
        return result

    def __truediv__(self, other: Dollar) -> float:
        return self._value / other._value

    def __str__(self) -> str:
        dollars, cents = divmod(self._value, 100)
        return f"${dollars:,d}.{cents:02d}"

    def to_float(self) -> float:
        return self._value / 100
