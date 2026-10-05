# Copyright 2026
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Self

import requests
from requests import Response

from gdq.money import CURRENCIES, Money

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
    starts_at: str  # datetime
    logo: Logo
    total: Money
    series: Series

    @classmethod
    def from_json(cls, json) -> Self:
        json["logo"] = Logo(**json["logo"])
        json["total"] = CURRENCIES[json["total"]["currency"]](json["total"]["amount"])
        json["series"] = Series(**json["series"])
        return cls(**json)


def _request(path: str, params: dict[str, str] | None = None) -> Response:
    """Generic request handler wrapper"""
    return requests.get(BASE_URL + path, params, timeout=5)


def get_series() -> list[Series]:
    json = _request("series").json()["series"]
    return [Series(**item) for item in json]


def get_events(series: Series) -> list[Event]:
    json = _request("events", {"series": series.id}).json()["events"]
    return [Event.from_json(item) for item in json]
