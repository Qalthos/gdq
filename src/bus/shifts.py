# Copyright 2021
# SPDX-License-Identifier: MIT
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Vancouver")


@dataclass
class Shift:
    color: str
    name: str
    start_hour: int

    def is_active(self) -> bool:
        return bool(self.start_hour <= _current_hour() < self.start_hour + 6)

    def __str__(self) -> str:
        boldness = 2
        if self.is_active():
            boldness = 7
        return f"{self.color};{boldness}m{self.name}\x1b[0m"


@dataclass
class Omega:
    color: str
    name: str

    def is_active(self, _: datetime) -> bool:
        return bool(random.getrandbits(1))  # pragma: nocover


def _current_hour() -> int:
    return datetime.now(PACIFIC).hour  # pragma: nocover


SHIFTS = [
    Shift(color="\x1b[33", start_hour=6, name="Dawn Guard"),
    Shift(color="\x1b[31", start_hour=12, name="Alpha Flight"),
    Shift(color="\x1b[34", start_hour=18, name="Night Watch"),
    Shift(color="\x1b[35", start_hour=0, name="Zeta"),
]

OMEGA = [
    Omega(color="\x1b[33", name="O"),
    Omega(color="\x1b[31", name="M"),
    Omega(color="\x1b[39", name="E"),
    Omega(color="\x1b[34", name="G"),
    Omega(color="\x1b[35", name="A"),
]
