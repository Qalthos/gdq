# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any, Literal, TypedDict


# API responses
class AuctionMessage(TypedDict):
    prize_id: str
    status: Literal["sold"]
    updated_at: str
    high_bid: TotalMessage | None


class TotalMessage(TypedDict):
    currency: str
    amount: str


class PrizeMessage(TypedDict):
    id: str
    type: Literal["giveaway", "live", "silent"]
    state: Literal["sold", "upcoming"]
    name: str
    description: DocFragment
    description_text: str
    starts_at: str
    ends_at: str
    updated_at: str
    images: list[Image]
    giveaway_amount: str | None
    raised: TotalMessage | None
    entrants: str | None
    winners: list[str | None]
    current_high_bid: str | None
    crafter: dict[str, Any] | None
    sponsor: dict[str, Any] | None


class Person(TypedDict):
    name: str
    pronouns: str
    bio: DocFragment
    bio_text: str
    picture: Image


class Image(TypedDict):
    url: str
    alt: str | None
    width: int
    height: int


class TextFragment(TypedDict):
    type: Literal["text"]
    text: str
    marks: None


class ParagraphFragment(TypedDict):
    type: Literal["paragraph"]
    content: list[TextFragment]


class DocFragment(TypedDict):
    type: Literal["doc"]
    content: list[ParagraphFragment]
