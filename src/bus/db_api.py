# Copyright 2026
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import TYPE_CHECKING

import requests
from requests import Response

from bus.utils import dollars_to_hours
from gdq.money import CURRENCIES, Dollar

if TYPE_CHECKING:
    from typing import Any, Self

BASE_URL = "https://desertbus.org/api/"
OMEGA = 0, False


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


def _request(path: str, params: dict[str, str] | None = None) -> Response:
    """Generic request handler wrapper"""
    return requests.get(BASE_URL + path, params, timeout=5)


@lru_cache
def get_series() -> list[Series]:
    json = _request("series").json()["series"]
    return [Series(**item) for item in json]


@lru_cache
def get_events(series_id: str = "") -> list[Event]:
    params = {}
    if series_id:
        params["series"] = series_id
    json = _request("events", params).json()["events"]
    return [Event.from_json(item) for item in json]


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
    global OMEGA  # noqa: PLW0603
    current_hour = datetime.now(UTC).hour
    if current_hour != OMEGA[0]:
        try:
            omega = requests.get("https://vst.ninja/Resources/isitomegashift.html", timeout=5).text
        except requests.exceptions.RequestException:
            pass
        else:
            OMEGA = current_hour, bool(int(omega))

    return OMEGA[1]
