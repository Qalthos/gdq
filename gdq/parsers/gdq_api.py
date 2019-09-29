from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Iterator

import requests

from gdq.models import Incentive, ChoiceIncentive, Choice, DonationIncentive, Event, Run


def _get_resource(base_url: str, resource_type: str, **kwargs) -> List[dict]:
    resource_url = f"{base_url}/api/v1/search/?type={resource_type}"
    for key, value in kwargs.items():
        resource_url += f"&{key}={value}"

    return requests.get(resource_url).json()


def get_events(base_url: str, event_id: int = None) -> Iterator[Event]:
    kwargs = {}
    if event_id:
        kwargs["id"] = event_id

    events = _get_resource(base_url, "event", **kwargs)
    for event in events:
        event_id = event["pk"]
        event_data = event["fields"]
        try:
            yield Event(
                event_id=event_id,
                name=event_data["name"],
                short_name=event_data["short"],
                total=float(event_data["amount"]),
                target=float(event_data["targetamount"]),
            )
        except ValueError:
            # 'amount' is None, not a likely candidate
            continue


def get_runs(base_url: str, event_id: int) -> Iterator[Run]:
    runs = _get_resource(base_url, "run", event=event_id)
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
            # TODO: pull directly
            runner=run["deprecated_runners"],
            start=start_time,
            estimate=int(estimate),
        )


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