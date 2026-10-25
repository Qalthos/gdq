# Copyright 2021
# SPDX-License-Identifier: MIT
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Vancouver")


class BaseShift(ABC):
    color: int
    name: str

    @abstractmethod
    def is_active(self) -> bool: ...

    def __str__(self) -> str:
        return self.name

    def __len__(self) -> int:
        return len(self.name)

    def colorize(self, s: str) -> str:
        boldness = 2
        if self.is_active():
            boldness = 7
        return f"\x1b[{self.color};{boldness}m{s}\x1b[0m"


@dataclass
class Shift(BaseShift):
    color: int
    name: str
    start_hour: int

    def is_active(self) -> bool:
        return bool(self.start_hour <= _current_hour() < self.start_hour + 6)


@dataclass
class Omega(BaseShift):
    color: int
    name: str

    def is_active(self) -> bool:
        return bool(random.getrandbits(1))  # pragma: nocover


def _current_hour() -> int:
    return datetime.now(PACIFIC).hour  # pragma: nocover


SHIFTS = [
    Shift(color=33, start_hour=6, name="Dawn Guard"),
    Shift(color=31, start_hour=12, name="Alpha Flight"),
    Shift(color=34, start_hour=18, name="Night Watch"),
    Shift(color=35, start_hour=0, name="Zeta"),
]

OMEGA = [
    Omega(color=33, name="O"),
    Omega(color=31, name="M"),
    Omega(color=39, name="E"),
    Omega(color=34, name="G"),
    Omega(color=35, name="A"),
]
