from datetime import datetime
from typing import List

import requests

from gdq.models import ChoiceIncentive, DonationIncentive, Event, Run


def _get_resource(base_url: str, resource_type: str, **kwargs) -> List:
    resource_url = f"{base_url}/api/v1/search/?type={resource_type}"
    for key, value in kwargs.items():
        resource_url += f"&{key}={value}"

    return requests.get(resource_url).json()


def get_events(base_url: str, event_id: int = None) -> List[Event]:
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


def get_runs(base_url: str, event_id: int) -> List[Run]:
    runs = _get_resource(base_url, "run", event=event_id)
    for run in runs:
        run_id = run["pk"]
        run = run["fields"]
        # TODO: Probably some wrangling needed here.
        # keys available: starttime, endtime, setup_time, run_time
        start_time = datetime.strptime(run["starttime"], "%Y-%m-%dT%H:%M:%S%z")
        end_time = datetime.strptime(run["endtime"], "%Y-%m-%dT%H:%M:%S%z")
        estimate = (end_time - start_time).total_seconds()
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


def get_incentives_for_run(base_url: str, run_id: int):
    incentives = _get_resource(base_url, "bid", run=run_id, state="OPENED")
