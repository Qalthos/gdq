# Copyright 2026
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import requests
from requests import Response

from bus.utils import dollars_to_hours
from gdq.money import CURRENCIES, Dollar

if TYPE_CHECKING:
    from typing import Any, Self

BASE_URL = "https://desertbus.org/api/"


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


def get_series() -> list[Series]:
    json = _request("series").json()["series"]
    return [Series(**item) for item in json]


def get_events(series_id: str = "") -> list[Event]:
    params = {}
    if series_id:
        params["series"] = series_id
    json = _request("events", params).json()["events"]
    return [Event.from_json(item) for item in json]
