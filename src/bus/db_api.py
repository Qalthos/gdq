# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum, auto
from functools import lru_cache
from typing import TYPE_CHECKING, cast

import requests

from bus.utils import dollars_to_hours
from common.money import CURRENCIES, Dollar, Money

if TYPE_CHECKING:
    from typing import Any, Self

    from bus.types import DocFragment, Image, Person, PrizeMessage, TotalMessage

BASE_URL = "https://desertbus.org/api/"


def _make_link(prize_id: str, text: str) -> str:
    OSC = "\033]8;;"  # noqa: N806
    ST = "\033\\"  # noqa: N806
    return f"{OSC}https://desertbus.org/2026/prize/{prize_id}{ST}{text}{OSC}{ST}"


@dataclass
class Prize:
    id: str
    type: PrizeType
    enabled: bool
    state: PrizeState
    name: str
    description: DocFragment
    description_text: str
    starts_at: datetime
    ends_at: datetime
    updated_at: datetime
    images: list[Image]
    giveaway_amount: str | None
    raised: Money | None
    entrants: str | None
    winners: list[str | None]
    current_high_bid: str | None
    crafter: Person | None
    sponsor: dict[str, Any] | None

    def __str__(self) -> str:
        name = _make_link(self.id, f"\033[{self.color}m{self.name}\033[0m")
        start = self.starts_at.astimezone()
        end = self.ends_at.astimezone()
        date_f = "%a %b %d"
        time_f = "%I:%M %p"

        match self.state:
            case PrizeState.UPCOMING:
                return (
                    f"{name} starts on {start.strftime(date_f)} "
                    f"between {start.strftime(time_f)} and {end.strftime(time_f)}"
                )
            case PrizeState.SOLD:
                return f"{name} sold for {self.raised}"

    @property
    def color(self) -> int:
        match self.type:
            case PrizeType.LIVE:
                # Red
                return 31
            case PrizeType.GIVEAWAY:
                # Yellow
                return 33
            case PrizeType.SILENT:
                # Cyan
                return 36

    @property
    def eta(self) -> timedelta:
        return self.starts_at - datetime.now(UTC)

    @property
    def active(self) -> bool:
        match self.state:
            case PrizeState.UPCOMING:
                match self.type:
                    case PrizeType.GIVEAWAY:
                        lookahead = 6
                    case PrizeType.SILENT:
                        lookahead = 12
                    case PrizeType.LIVE:
                        lookahead = 24
                return self.eta < timedelta(hours=lookahead)
            case PrizeState.SOLD:
                return False

    @classmethod
    def from_json(cls, message: PrizeMessage) -> Self:
        updated: dict[str, Any] = dict(**message)
        for key in ("starts_at", "ends_at", "updated_at"):
            with contextlib.suppress(KeyError):
                updated[key] = datetime.fromisoformat(message[key])
        for key in ("raised",):
            value = message[key]
            if value is None:
                updated[key] = None
            else:
                updated[key] = _money_from_message(value)
        updated["state"] = PrizeState(message["state"])
        updated["type"] = PrizeType(message["type"])

        return cls(**updated)


class PrizeState(StrEnum):
    UPCOMING = auto()
    SOLD = auto()


class PrizeType(StrEnum):
    LIVE = auto()
    GIVEAWAY = auto()
    SILENT = auto()


@dataclass
class Series:
    id: str
    name: str


@dataclass
class Event:
    id: str
    name: str
    url: str  # just year?
    primary: bool  # current event?
    starts_at: datetime
    logo: Image
    total: Dollar
    series: Series

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Self:
        json["total"] = CURRENCIES[json["total"]["currency"]](float(json["total"]["amount"]))
        json["series"] = Series(**json["series"])
        json["starts_at"] = datetime.fromisoformat(json["starts_at"])
        return cls(**json)

    @property
    def hours(self) -> int:
        return dollars_to_hours(self.total)

    def distance(self, current: Dollar) -> str:
        next_level = self.total - current
        if next_level <= Dollar():
            return ""

        return f"{next_level} until {self!s}"


def _money_from_message(message: TotalMessage) -> Money:
    currency = CURRENCIES.get(message["currency"], None)
    if currency is None:
        msg = f"Invalid currency {message['currency']}"
        raise ValueError(msg)
    return currency(message["amount"])


def _request(resource: str, path: str = "", params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Generic request handler wrapper"""
    return requests.get(BASE_URL + path + resource, params, timeout=5).json()[resource]


@lru_cache
def get_events(series_id: str = "") -> list[Event]:
    params = {}
    if series_id:
        params["series"] = series_id
    json = _request("events", params=params)
    return [Event.from_json(item) for item in json]


def get_prizes(event_id: str) -> list[Prize]:
    json = cast("list[PrizeMessage]", _request("prizes", f"events/{event_id}/"))
    return [Prize.from_json(item) for item in json]


@lru_cache
def get_series() -> list[Series]:
    json = _request("series")
    return [Series(**item) for item in json]


@lru_cache
def get_primary() -> Event:
    for event in get_events():
        if event.primary:
            return event
    err = "No primary event found"
    raise RuntimeError(err)


@lru_cache
def get_history() -> list[Event]:
    primary = get_primary()
    events = reversed(get_events(primary.series.id))
    return [event for event in events if not event.primary]


def is_omega() -> bool:
    """Uses the current hour as a cache key for fetching call."""
    current_hour = datetime.now(UTC).hour
    return _omega(current_hour)


@lru_cache(maxsize=10)
def _omega(_: int) -> bool:
    omega = requests.get("https://vst.ninja/Resources/isitomegashift.html", timeout=5).text
    return bool(int(omega))
