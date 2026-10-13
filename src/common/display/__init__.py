# Copyright 2026
# SPDX-License-Identifier: MIT
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


type String = str | SquishableString


class SquishableString[T]:
    _data: T
    _render_func: Callable[[T, int], str]

    def __init__(self, data: T, func: Callable) -> None:
        self._data = data
        self._render_func = func

    def render(self, width: int) -> str:
        return self._render_func(self._data, width)


class Display(ABC):
    term_w: int
    term_h: int

    @abstractmethod
    def refresh_terminal(self) -> None: ...

    @abstractmethod
    def update_header(self, lines: Sequence[String]) -> None: ...

    @abstractmethod
    def update_body(self, lines: Iterable[String]) -> None: ...

    @abstractmethod
    def update_footer(self, lines: Sequence[String]) -> None: ...
