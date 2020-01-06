import re
from collections import defaultdict
from datetime import datetime
import functools
from typing import Dict, Generator, List

import requests

from gdq.models import Incentive, ChoiceIncentive, Choice, DonationIncentive
from gdq.models import Event, SingleEvent, MultiEvent, Run, Runner


def _get_resource(base_url: str, resource_type: str, **kwargs) -> List[dict]:
    resource_url = f"{base_url}/api/v1/search/"
    return requests.get(resource_url, params={"type": resource_type, **kwargs}).json()


def get_events(base_url: str, event_id: int = None) -> List[Event]:
    kwargs = {}
    if event_id:
        kwargs["id"] = event_id

    events = _get_resource(base_url, "event", **kwargs)
    match_multi = re.compile(r"(.*)s\d+$", re.MULTILINE)
    multi_events = {}
    event_objs = []
    for event in events:
        event_id = event["pk"]
        event_data = event["fields"]
        try:
            event = SingleEvent(
                event_id=event_id,
                name=event_data["name"],
                short_name=event_data["short"],
                _total=float(event_data["amount"]),
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
                    name=event.name,
                    short_name=shorter_name,
                )
                multi_events[shorter_name] = mevent
                event_objs.append(mevent)
            else:
                multi_events[shorter_name].subevents.append(event)
        else:
            event_objs.append(event)

    return event_objs


def get_runs(base_url: str, event_id: int) -> Generator[Run, None, None]:
    runs = _get_resource(base_url, "run", event=event_id)
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

        yield Run(
            run_id=run_id,
            game=run["name"],
            platform=run["console"],
            category=run["category"],
            runners=[runners[runner] for runner in run["runners"]],
            start=start_time,
            estimate=int(estimate),
        )


def get_runners_for_event(base_url: str, event_id: int) -> Dict[int, Runner]:
    runners = _get_resource(base_url, resource_type="runner", event=event_id)
    runner_dict = {}

    for runner in runners:
        runner_id = runner["pk"]
        runner = runner["fields"]
        runner_dict[runner_id] = Runner(runner_id=runner_id, name=runner["name"], pronouns=runner["pronouns"])

    return runner_dict


@functools.lru_cache
def get_runner(base_url: str, runner_id: int) -> Runner:
    runner = _get_resource(base_url, resource_type="runner", id=runner_id)[0]["fields"]
    return Runner(runner_id, runner["name"], runner["pronouns"])


def get_incentives_for_event(base_url: str, event_id: int) -> Dict[str, Incentive]:
    """
    Method to emulate how gdq_tracker requests incentive information.
    """

    incentives = _get_resource(base_url, "allbids", event=event_id, feed="open")
    incentive_dict = dict()
    choices = defaultdict(list)

    for incentive in incentives:
        incentive = incentive["fields"]
        game = incentive["speedrun__name"]

        if incentive.get('parent__name'):
            parent_name = incentive["parent__name"]
            choice = Choice(
                name=incentive["name"],
                description=incentive["description"],
                numeric_total=float(incentive["total"]),
            )
            choices[parent_name].append(choice)
            continue
        elif incentive["istarget"]:
            # noinspection PyArgumentList
            incentive_obj = DonationIncentive(
                description=incentive["description"],
                short_desc=incentive["name"],
                current=float(incentive["total"]),
                numeric_total=float(incentive["goal"]),
            )
        else:
            # noinspection PyArgumentList
            incentive_obj = ChoiceIncentive(
                description=incentive["description"],
                short_desc=incentive["name"],
                current=float(incentive["total"]),
                options=choices[incentive["name"]],
            )
        incentive_dict[game] = incentive_dict.get(game, []) + [incentive_obj]
    return incentive_dict


def get_incentives_for_run(base_url: str, run_id: int) -> List[Incentive]:
    incentives = _get_resource(base_url, "allbids", run=run_id, feed="open")
    incentive_list = []

    for incentive in incentives:
        incentive = incentive["fields"]
        if incentive["istarget"]:
            # noinspection PyArgumentList
            incentive_obj = DonationIncentive(
                description=incentive["description"],
                short_desc=incentive["name"],
                current=float(incentive["total"]),
                numeric_total=float(incentive["goal"]),
            )
        else:
            # noinspection PyArgumentList
            incentive_obj = ChoiceIncentive(
                description=incentive["description"],
                short_desc=incentive["name"],
                current=float(incentive["total"]),
                # TODO: Uhhh...
                options=[],
            )
        incentive_list.append(incentive_obj)
    return incentive_list
