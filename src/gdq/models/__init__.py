# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable

    from common import money


@dataclass
class Incentive(ABC):
    incentive_id: int
    description: str
    short_desc: str
    current: money.Money
    state: str

    @property
    def closed(self) -> bool:
        return self.state == "CLOSED"

    @property
    def currency(self) -> type[money.Money]:
        return type(self.current)

    @abstractmethod
    def render(self, width: int, align: int, args: argparse.Namespace) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError


@dataclass
class Run:
    game: str
    platform: str
    category: str
    runners: list[Runner | str]
    incentives: list[Incentive]

    start: datetime
    estimate: int

    run_id: int

    @property
    def runner_str(self) -> str:
        return ", ".join(str(runner) for runner in self.runners)

    @property
    def delta(self) -> str:
        now = datetime.now()
        if self.start < now:
            return "  NOW  "
        delta = self.start - now
        if delta.days >= 1:
            return f"{delta.days} DAYS"
        hours, minutes = divmod(delta.seconds // 60, 60)
        return f"{delta.days}:{hours:02d}:{minutes:02d}"

    @property
    def end(self) -> datetime:
        return self.start + timedelta(seconds=self.estimate)

    @property
    def remaining(self) -> timedelta:
        now = datetime.now()
        if self.start < now:
            return self.end - now
        return timedelta(seconds=self.estimate)

    @property
    def is_live(self) -> bool:
        return self.remaining > timedelta()

    @property
    def str_estimate(self) -> str:
        hours, minutes = divmod(self.remaining.seconds, 3600)
        minutes //= 60
        return f"+{hours}:{minutes:02d}"

    @property
    def game_desc(self) -> str:
        if self.platform:
            return f"{self.game.strip()} ({self.platform.strip()})"
        return self.game

    def render(self, width: int, args: argparse.Namespace) -> Iterable[str]:
        # If the run is over, skip it
        if not self.is_live:
            return

        width -= 8
        if not any(self.runners):
            desc_width = max(len(self.game_desc), len(self.category))
            if desc_width > width:
                # If display too long, truncate run
                self.game = self.game[: width - 1] + "…"
                self.category = self.category[: width - 1] + "…"

            yield "{}┼{}┤".format("─" * 7, "─" * (width - 1))
            yield f"{self.delta}│{self.game_desc:<{width - 1}s}│"
            yield f"{self.str_estimate: >7s}│{self.category:<{width - 1}}│"

        else:
            desc_width = max(
                width - 2 - len(self.runner_str),
                len(self.game_desc),
                len(self.category),
            )

            runner = "│" + self.runner_str + "│"
            if desc_width + len(runner) > width:
                # Truncate runner display if too long
                runner_width = width - 3 - desc_width
                runner = "│" + self.runner_str[:runner_width] + "…│"

            if desc_width + len(runner) > width:
                # If display still too long, truncate run
                overrun = desc_width + len(runner) - width
                desc_width -= overrun
                self.game = self.game[: -(overrun + 1)] + "…"

            border = "─" * (len(runner) - 2)
            yield f"───────┼{'─' * desc_width}┬{border}┤"
            yield f"{self.delta}│{self.game_desc:<{desc_width}s}{runner}"
            yield f"{self.str_estimate: >7s}│{self.category:<{desc_width}}└{border}┤"

        # Handle incentives
        if self.incentives and not args.hide_incentives:
            align_width = max(
                args.min_width,
                *(len(incentive) for incentive in self.incentives),
            )
            for incentive in self.incentives:
                yield from incentive.render(width, align_width, args)


@dataclass
class Runner:
    runner_id: int
    name: str
    pronouns: str = ""

    def __str__(self) -> str:
        if self.pronouns:
            return f"{self.name}({self.pronouns})"
        return self.name
