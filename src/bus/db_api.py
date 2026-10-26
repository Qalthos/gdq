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

    from bus.types import (
        AuctionBid,
        AuctionMessage,
        Bidder,
        BidMessage,
        DocFragment,
        Image,
        Person,
        PrizeMessage,
        Sponsor,
        TotalMessage,
    )

BASE_URL = "https://desertbus.org/api/"


def _make_link(prize_id: str, text: str) -> str:
    OSC = "\033]8;;"  # noqa: N806
    ST = "\033\\"  # noqa: N806
    return f"{OSC}https://desertbus.org/2026/prize/{prize_id}{ST}{text}{OSC}{ST}"


def _eta(ref: datetime) -> timedelta:
    return ref - datetime.now(UTC).replace(microsecond=0)


@dataclass
class Auction:
    status: AuctionStatus
    updated_at: datetime
    prize_id: str
    high_bid: AuctionBid | None

    def __str__(self) -> str:
        exclamations = list(AuctionStatus).index(self.status)
        prefix = f"{self.status}{'!' * exclamations} " if exclamations > 0 else ""
        if self.high_bid is None:
            return "waiting for bids..."
        return f"{prefix}{self.high_bid['name']} says {self.high_bid['message']}"

    @classmethod
    def from_json(cls, message: AuctionMessage) -> Self:
        return cls(
            status=AuctionStatus(message["status"]),
            updated_at=datetime.fromisoformat(message["updated_at"]),
            prize_id=message["prize_id"],
            high_bid=message["high_bid"],
        )


@dataclass
class Prize:
    id: str
    type: PrizeType
    state: PrizeState
    enabled: bool
    name: str
    description: DocFragment
    description_text: str
    starts_at: datetime
    ends_at: datetime
    updated_at: datetime
    images: list[Image]
    giveaway_amount: Money | None
    raised: Money | None
    entrants: list[str] | None
    winners: list[Bidder] | list[None]
    current_high_bid: Bid | None
    crafter: Person | None
    sponsor: Sponsor | None

    def __str__(self) -> str:
        name = _make_link(self.id, f"\033[{self.color}m{self.name}\033[0m")
        time_f = "%I:%M %p"

        match self.state:
            case PrizeState.UPCOMING:
                output = f"{name} starts on {self.starts_at.strftime('%a %b %d')}"
                match self.type:
                    case PrizeType.GIVEAWAY:
                        detail = f"between {self.starts_at.strftime(time_f)} and {self.ends_at.strftime(time_f)}"
                    case PrizeType.LIVE:
                        detail = f"around {self.starts_at.strftime(time_f)}"
                    case PrizeType.SILENT:
                        detail = f"at {self.starts_at.strftime(time_f)}"
                return f"{output} {detail}"
            case PrizeState.ACTIVE:
                match self.type:
                    case PrizeType.GIVEAWAY:
                        detail = f"{self.giveaway_amount} for {self.eta_end}"
                    case _:
                        if self.current_high_bid is None:
                            detail = "be the first!"
                        else:
                            detail = f"{self.current_high_bid.name} for {self.current_high_bid.amount}"
                return f"{name} - {detail}"
            case PrizeState.SOLD:
                return f"{name} sold for {self.raised}"
            case _:
                return f"{name} {self.type} {self.state}"

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
        return _eta(self.starts_at)

    @property
    def eta_end(self) -> timedelta:
        return _eta(self.ends_at)

    @property
    def active(self) -> bool:
        match self.state:
            case PrizeState.ACTIVE | PrizeState.COOLDOWN | PrizeState.FINALIZING:
                return True
            case _:
                return False

    @property
    def upcoming(self) -> bool:
        match self.state:
            case PrizeState.UPCOMING:
                match self.type:
                    case PrizeType.GIVEAWAY:
                        lookahead = 6
                    case PrizeType.SILENT:
                        lookahead = 12
                    case PrizeType.LIVE:
                        lookahead = 24
                return self.eta_end < timedelta(hours=lookahead)
            case _:
                return False

    @classmethod
    def from_json(cls, message: PrizeMessage) -> Self:
        updated: dict[str, Any] = dict(**message)
        for key in ("starts_at", "ends_at", "updated_at"):
            with contextlib.suppress(KeyError):
                updated[key] = datetime.fromisoformat(message[key]).astimezone()
        for key in ("raised", "giveaway_amount"):
            value = message[key]
            updated[key] = None if value is None else _money_from_message(value)
        for key in ("current_high_bid",):
            value = message[key]
            updated[key] = None if value is None else Bid.from_json(value)
        updated["state"] = PrizeState(message["state"])
        updated["type"] = PrizeType(message["type"])

        return cls(**updated)


@dataclass
class Bid:
    name: str
    amount: Money

    @classmethod
    def from_json(cls, message: BidMessage) -> Self:
        return cls(message["name"], _money_from_message(message["amount"]))


class AuctionStatus(StrEnum):
    STARTED = auto()
    ONCE = auto()
    TWICE = auto()
    SOLD = auto()


class PrizeState(StrEnum):
    UPCOMING = auto()
    ACTIVE = auto()
    COOLDOWN = auto()
    FINALIZING = auto()
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
