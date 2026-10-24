# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Literal, TypedDict


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
    state: Literal["active", "sold", "cooldown", "finalizing", "upcoming"]
    name: str
    description: DocFragment
    description_text: str
    starts_at: str
    ends_at: str
    updated_at: str
    images: list[Image]
    giveaway_amount: TotalMessage | None
    raised: TotalMessage | None
    entrants: str | None
    winners: list[Bidder] | list[None]
    current_high_bid: BidMessage | None
    crafter: Person | None
    sponsor: Sponsor | None


class Bidder(TypedDict):
    display_name: str
    pronouns: str


class Sponsor(TypedDict):
    name: str
    bio: DocFragment
    bio_text: str
    picture: Image


class Person(Sponsor):
    pronouns: str


class BidMessage(TypedDict):
    name: str
    amount: TotalMessage


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
