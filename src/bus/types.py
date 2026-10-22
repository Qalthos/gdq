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
    type: Literal["giveaway", "live"]
    state: Literal["upcoming"]
    name: str
    description: dict[str, Any]
    description_text: str
    starts_at: str
    ends_at: str
    updated_at: str
    giveaway_amount: str | None
    raised: TotalMessage | None
    entrants: str | None
    winners: list[str | None]
    current_high_bid: str | None
    crafter: dict[str, Any] | None
    sponsor: dict[str, Any] | None
