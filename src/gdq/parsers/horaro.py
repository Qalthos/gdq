from datetime import datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

import requests

from gdq.models import Event, Run, Runner
from gdq.parsers import Parser


def _munge_data(columns: list[str], data: list[str | None], key: dict[str, str]) -> dict[str, str]:
    return {k: data[columns.index(v)] or "" for k, v in key}


class Horaro(Parser):
    base_url = "https://horaro.net/-/api/v1/"
    key_map: dict[str, str]

    def __init__(self, *, key_map: dict[str, str]) -> None:
        self.key_map = key_map

    def _get_resource(
        self,
        resource: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if headers is None:
            headers = {}

        resp = requests.get(self.base_url + resource, headers=headers, timeout=5)

        return resp.json()["data"]

    def get_events(self, event_name: str) -> list[Event]:
        schedules = cast("list[dict[str, Any]]", self._get_resource(f"events/{event_name}"))

        events = []
        for schedule in schedules:
            start = datetime.fromisoformat(schedule["start"]).astimezone(ZoneInfo(schedule["timezone"]))
            event = Event(
                id=schedule["id"],
                name=schedule["name"],
                short=schedule["slug"],
                receiver="",
                start_time=start,
                total=self.currency(),
            )
            events.append(event)

        return events

    def get_runs(self) -> list[Run]:
        schedule = cast("dict[str, Any]", self._get_resource(f"schedules/{self.event_id}"))
        timezone = ZoneInfo(schedule["timezone"])

        runs = []
        for run in schedule["items"]:
            extra = _munge_data(schedule["columns"], run, self.key_map)
            runners = [
                Runner(*args)
                for args in zip(
                    *[extra.pop(key).split(", ") for key in ("runner_ids", "runners")],
                    strict=True,
                )
            ]
            runs.append(
                Run(
                    run_id=int(extra.pop("id")),
                    start=datetime.fromtimestamp(run["scheduled_t"]).astimezone(timezone),
                    estimate=run["length_t"],
                    runners=runners,
                    incentives=[],
                    **extra,
                ),
            )

        return runs
