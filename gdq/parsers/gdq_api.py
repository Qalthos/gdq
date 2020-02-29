from collections import defaultdict
from datetime import datetime, timezone
import json
import re
from typing import Dict, List, Optional

import requests

from gdq.models import Incentive, ChoiceIncentive, Choice, DonationIncentive
from gdq.models import Event, SingleEvent, MultiEvent, Run, Runner


def _get_resource(base_url: str, resource_type: str, **kwargs) -> requests.Response:
    resource_url = f"{base_url}/api/v1/search/"
    return requests.get(resource_url, params={"type": resource_type, **kwargs})


def get_events(base_url: str, event_id: int = None) -> Optional[List[Event]]:
    kwargs = {}
    if event_id:
        kwargs["id"] = event_id

    try:
        events = _get_resource(base_url, "event", **kwargs).json()
    except json.decoder.JSONDecodeError:
        return

    match_multi = re.compile(r"(.*)s\d+$", re.MULTILINE)
    multi_events = {}
    event_objs = []

    for event in events:
        event_id = event["pk"]
        event_data = event["fields"]

        # There are a few keys for tracking the start time of events
        start = None
        for key in ("date", "datetime"):
            if key in event_data:
                try:
                    start = datetime.strptime(event_data[key], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    start = datetime.strptime(event_data[key], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                break

        try:
            event = SingleEvent(
                event_id=event_id,
                name=event_data["name"],
                _start_time=start,
                short_name=event_data["short"],
                _total=float(event_data["amount"]),
                _charity=event_data["receivername"],
                target=float(event_data["targetamount"]),
            )
        except ValueError:
            # 'amount' is None, not a likely candidate
            continue

        match = match_multi.match(event.short_name)
        if match:
            shorter_name = match.group(1)
            if shorter_name not in multi_events:
                mevent = MultiEvent(
                    subevents=[event],
                    name=event.name.split(" Stream")[0],
                    short_name=shorter_name,
                )
                multi_events[shorter_name] = mevent
                event_objs.append(mevent)
            else:
                multi_events[shorter_name].subevents.append(event)
        else:
            event_objs.append(event)

    return event_objs


def get_runs(base_url: str, event_id: int) -> List[Run]:
    runs = _get_resource(base_url, "run", event=event_id).json()
    run_list = []

    runners = get_runners_for_event(base_url, event_id)
    for run in runs:
        run_id = run["pk"]
        run = run["fields"]
        # Best guess how time works: endtime - starttime = run_time + setup_time
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
            start=start_time,
            estimate=int(estimate),
        ))

    return run_list


def get_runners_for_event(base_url: str, event_id: int) -> Dict[int, Runner]:
    runners = _get_resource(base_url, resource_type="runner", event=event_id).json()
    runner_dict = {}

    for runner in runners:
        runner_id = runner["pk"]
        runner = runner["fields"]
        runner_dict[runner_id] = Runner(runner_id=runner_id, name=runner["name"], pronouns=runner.get("pronouns", ""))

    return runner_dict


def get_incentives_for_event(base_url: str, event_id: int) -> Dict[str, Incentive]:
    # FIXME: This stops at 500 results, and doesn't seem to be pageable.
    incentives = _get_resource(base_url, "allbids", event=event_id).json()
    incentive_dict = dict()
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
                numeric_total=float(incentive["total"]),
            )
            choices[parent_id].append(choice)
            continue

        if incentive["istarget"]:
            incentive_obj = DonationIncentive(
                incentive_id=incentive_id,
                description=incentive["description"],
                short_desc=incentive["name"].strip(),
                current=float(incentive["total"]),
                numeric_total=float(incentive["goal"] or 0),
                state=incentive["state"],
            )
        else:
            incentive_obj = ChoiceIncentive(
                incentive_id=incentive_id,
                description=incentive["description"],
                short_desc=incentive["name"],
                current=float(incentive["total"]),
                options=choices[incentive_id],
                state=incentive["state"],
            )
        incentive_dict[game] = incentive_dict.get(game, []) + [incentive_obj]

    return incentive_dict
