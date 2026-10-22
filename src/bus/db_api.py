# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

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

    from bus.types import PrizeMessage, TotalMessage

BASE_URL = "https://desertbus.org/api/"


@dataclass
class Prize:
    id: str
    type: PrizeType
    enabled: bool
    state: PrizeState
    name: str
    description: dict[str, Any]
    description_text: str
    starts_at: datetime
    ends_at: datetime
    updated_at: datetime
    images: list[Any]
    giveaway_amount: str | None
    raised: Money | None
    entrants: str | None
    winners: list[str | None]
    current_high_bid: str | None
    crafter: dict[str, Any] | None
    sponsor: dict[str, Any] | None

    def __str__(self) -> str:
        match self.state:
            case PrizeState.UPCOMING:
                eta = datetime.now(UTC) - self.starts_at
                return f"{self.name} in {eta}"
            case PrizeState.SOLD:
                return f"{self.name} sold for {self.raised}"

    @property
    def active(self) -> bool:
        match self.state:
            case PrizeState.UPCOMING:
                eta = self.starts_at - datetime.now(UTC).replace(microsecond=0)
                return eta < timedelta(hours=1)
            case PrizeState.SOLD:
                return False

    @classmethod
    def from_json(cls, message: PrizeMessage) -> Self:
        updated: dict[str, Any] = dict(**message)
        for key in ("starts_at", "ends_at", "updated_at"):
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
class Logo:
    url: str
    alt: str | None
    width: int
    height: int


@dataclass
class Event:
    id: str
    name: str
    url: str  # just year?
    primary: bool  # current event?
    starts_at: datetime
    logo: Logo
    total: Dollar
    series: Series

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Self:
        json["logo"] = Logo(**json["logo"])
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
