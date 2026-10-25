# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Literal, TypedDict


# API responses
class AuctionMessage(TypedDict):
    prize_id: str
    status: Literal["started", "once", "twice", "sold"]
    updated_at: str
    high_bid: AuctionBid | None


class GuestMessage(TypedDict):
    id: str
    name: str
    pronouns: str
    title: str | None
    description: DocFragment
    description_text: str
    picture: Image
    type: Literal["visitor"]
    dates: list[TimeFragment]


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


# Fragments from other messages
class AuctionBid(TotalMessage):
    message: str
    name: str


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


class TimeFragment(TypedDict):
    starts_at: str
    ends_at: str


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
