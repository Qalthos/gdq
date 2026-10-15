# Copyright 2026
# SPDX-License-Identifier: MIT
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from common.money import Money
    from gdq.models import Event, Run


class Parser(ABC):
    base_url: str
    currency: type[Money]
    event_id: int = 0

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    @abstractmethod
    def get_events(self, event_name: str) -> list[Event]: ...

    @abstractmethod
    def get_runs(self) -> list[Run]: ...
