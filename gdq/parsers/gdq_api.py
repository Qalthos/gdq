import json
import operator
import re
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone

import requests

from gdq import money
from gdq.models import (Choice, ChoiceIncentive, DonationIncentive, Event,
                        Incentive, MultiEvent, Run, Runner, SingleEvent)


def _get_resource(base_url: str, resource_type: str, **kwargs: str) -> requests.Response:
    resource_url = urllib.parse.urljoin(base_url, "api/v1/search")
    return requests.get(resource_url, params={"type": resource_type, **kwargs})


def get_events(base_url: str, event_name: str = "") -> list[Event]:
    kwargs = {}
    if event_name:
        kwargs["short"] = str(event_name)

    try:
        events = _get_resource(base_url, "event", **kwargs).json()
    except json.decoder.JSONDecodeError:
        return []

    match_multi = re.compile(r"(.*)s\d+$", re.MULTILINE)
    multi_events = {}
    event_objs: list[Event] = []

    for event in events:
        event_id = event["pk"]
        event_data = event["fields"]

        # There are a few keys for tracking the start time of events
        for key in ("date", "datetime"):
            if key in event_data:
                try:
                    start = datetime.strptime(event_data[key], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    start = datetime.strptime(event_data[key], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                break

        # Set currency from data
        currency_str = event_data.get("paypalcurrency")
        currency = money.CURRENCIES.get(currency_str, money.Dollar)

        try:
            total = float(event_data["amount"])
        except ValueError:
            total = 0

        event = SingleEvent(
            event_id=event_id,
            name=event_data["name"],
            _start_time=start,
            short_name=event_data["short"],
            _total=currency(total),
            _charity=event_data["receivername"],
            target=currency(float(event_data["targetamount"])),
            _offset=currency(),
        )

        match = match_multi.match(event.short_name)
        if match:
            shorter_name = match.group(1)
            if shorter_name not in multi_events:
                mevent = MultiEvent(
                    subevents=[event],
                    name=event.name.split(" Stream")[0],
                    short_name=shorter_name,
                    _offset=currency(),
                )
                multi_events[shorter_name] = mevent
                event_objs.append(mevent)
            else:
                multi_events[shorter_name].subevents.append(event)
        else:
            event_objs.append(event)

    return sorted(event_objs, key=operator.attrgetter("start_time"))


def get_runs(base_url: str, event_id: int, currency: type[money.Money]) -> list[Run]:
    runs = _get_resource(base_url, "run", event=str(event_id)).json()
    run_list = []

    runners = get_runners_for_event(base_url, event_id)
    incentives = get_incentives_for_event(base_url, event_id, currency)
    for run in runs:
        run_id = run["pk"]
        run = run["fields"]
        try:
            start_time = datetime.strptime(run["starttime"], "%Y-%m-%dT%H:%M:%S%z")
            run_h, run_m, run_s = run["run_time"].split(":")
            estimate = (int(run_h) * 3600) + (int(run_m) * 60) + int(run_s)
        except TypeError:
            # No times attached, huh?
            continue

        run_list.append(Run(
            run_id=run_id,
            game=run["name"],
            platform=run["console"].strip(),
            category=run["category"],
            runners=[runners[runner] for runner in run["runners"]],
            incentives=sorted(
                incentives.get(run["name"]) or [],
                key=operator.attrgetter("incentive_id"),
            ),
            start=start_time,
            estimate=int(estimate),
        ))

    return run_list


def get_runners_for_event(base_url: str, event_id: int) -> dict[int, Runner]:
    runners = _get_resource(base_url, resource_type="runner", event=str(event_id)).json()
    runner_dict = {}

    for runner in runners:
        runner_id = runner["pk"]
        runner = runner["fields"]
        runner_dict[runner_id] = Runner(runner_id=runner_id, name=runner["name"], pronouns=runner.get("pronouns", ""))

    return runner_dict


def get_incentives_for_event(
        base_url: str, event_id: int,
        currency: type[money.Money]) -> dict[str, list[Incentive]]:
    # FIXME: This stops at 500 results, and doesn't seem to be pageable.
    incentives = _get_resource(base_url, "allbids", event=str(event_id)).json()
    incentive_dict: dict[str, list[Incentive]] = dict()
    choices = defaultdict(list)

    for incentive in incentives:
        incentive_id = incentive["pk"]
        incentive = incentive["fields"]
        game = incentive.get("speedrun__name")

        if incentive.get('parent'):
            parent_id = incentive["parent"]
            choice = Choice(
                name=incentive["name"],
                description=incentive["description"],
                total=currency(float(incentive["total"])),
            )
            choices[parent_id].append(choice)
            continue

        incentive_obj: Incentive
        if incentive["istarget"]:
            incentive_obj = DonationIncentive(
                incentive_id=incentive_id,
                description=incentive["description"],
                short_desc=incentive["name"].strip(),
                current=currency(float(incentive["total"])),
                total=currency(float(incentive["goal"] or 0)),
                state=incentive["state"],
            )
        else:
            incentive_obj = ChoiceIncentive(
                incentive_id=incentive_id,
                description=incentive["description"],
                short_desc=incentive["name"],
                current=currency(float(incentive["total"])),
                options=choices[incentive_id],
                state=incentive["state"],
            )
        incentive_dict[game] = incentive_dict.get(game, []) + [incentive_obj]

    return incentive_dict
