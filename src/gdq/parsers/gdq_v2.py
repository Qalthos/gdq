# Copyright 2026
# SPDX-License-Identifier: MIT
import operator
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import requests

from common.money import CURRENCIES
from gdq.models import (
    Event as BaseEvent,
)
from gdq.models import (
    Incentive,
    Run,
    Runner,
)
from gdq.models.v2 import (
    Choice,
    ChoiceIncentive,
    DonationIncentive,
    Event,
)
from gdq.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable


class BidType(StrEnum):
    CHALLENGE = "challenge"
    CHOICE = "choice"
    OPTION = "option"


def _hydrate_runner(runner_dict: dict[str, str]) -> Runner:
    return Runner(int(runner_dict["id"]), runner_dict["name"], runner_dict["pronouns"])


def _hms_to_seconds(hms: str) -> int:
    if hms == "0":
        raise ValueError

    run_h, run_m, run_s = (int(i) for i in hms.split(":"))
    return int(timedelta(hours=run_h, minutes=run_m, seconds=run_s).total_seconds())


class GDQV2(Parser):
    def _get_resource(self, resource: str, **kwargs: str) -> Iterable[dict[str, Any]]:
        resource_url = urllib.parse.urljoin(self.base_url, f"api/v2/{resource}")
        resp = requests.get(resource_url, params=kwargs, timeout=5).json()
        yield from resp["results"]
        while resp["next"]:
            resp = requests.get(resp["next"], timeout=5).json()
            yield from resp["results"]

    def get_events(self, event_name: str = "") -> list[BaseEvent]:
        kwargs = {"totals": ""}

        events = self._get_resource("events", **kwargs)

        event_objs: list[Event] = []
        for event in events:
            total = CURRENCIES[event["paypalcurrency"]](float(event["donation_total"]))
            timezone = ZoneInfo(event["timezone"])
            start_dt = datetime.fromisoformat(event["datetime"]).astimezone(timezone)
            event_obj = Event(
                type=event["type"],
                id=int(event["id"]),
                short=event["short"],
                name=event["name"],
                start_time=start_dt,
                receiver=event["receivername"],
                total=total,
            )
            event_objs.append(event_obj)

        return sorted(event_objs, key=lambda x: x.start_time)

    def get_runs(self) -> list[Run]:
        runs = self._get_resource(f"events/{self.event_id}/runs")
        run_list = []

        incentives = self.get_incentives()
        for run in runs:
            start_time = datetime.strptime(run["starttime"], "%Y-%m-%dT%H:%M:%S%z")
            try:
                estimate = _hms_to_seconds(run["run_time"])
            except ValueError:
                continue

            run_obj = Run(
                run_id=int(run["id"]),
                game=run["name"],
                platform=run["console"].strip(),
                category=run["category"],
                runners=[_hydrate_runner(runner) for runner in run["runners"]],
                incentives=sorted(
                    incentives.get(run["name"]) or [],
                    key=operator.attrgetter("incentive_id"),
                ),
                start=start_time,
                estimate=int(estimate),
            )

            run_list.append(run_obj)

        return run_list

    def get_incentives(self) -> dict[int, list[Incentive]]:
        incentives = self._get_resource(f"events/{self.event_id}/bids")

        incentive_dict: dict[int, list[Incentive]] = defaultdict(list)
        choices: dict[int, list[Choice]] = defaultdict(list)

        for incentive in incentives:
            run_id = int(incentive["speedrun"])
            existing = incentive_dict.get(run_id, [])

            common_data: dict[str, int | str] = {
                "incentive_id": int(incentive["id"]),
                "description": incentive["description"],
                "short_desc": incentive["name"].strip(),
                "current": incentive["total"],
            }

            incentive_obj: Incentive
            match incentive["bid_type"]:
                case BidType.CHALLENGE:
                    incentive_obj = DonationIncentive(
                        **common_data,
                        total=incentive["goal"],
                        state=incentive["state"],
                    )
                case BidType.CHOICE:
                    incentive_obj = ChoiceIncentive(
                        **common_data,
                        options=choices[common_data["incentive_id"]],
                        state=incentive["state"],
                    )
                case BidType.OPTION:
                    parent_id = int(incentive["parent"])
                    choice = Choice(
                        **common_data,
                    )
                    choices[parent_id].append(choice)
                    continue
                case other:
                    err = f"Unknown bid type {other}"
                    raise ValueError(err)
            incentive_dict[run_id] = [*existing, incentive_obj]

        return incentive_dict
