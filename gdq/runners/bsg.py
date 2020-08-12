import argparse
from datetime import datetime
from typing import List, Optional, Tuple

from gdq.events.bsg import BSGTracker
from gdq.runners.gdq import Runner as GDQRunner


class Runner(GDQRunner):
    def get_marathon(self) -> BSGTracker:
        try:
            return BSGTracker(
                url=self.event_config["url"],
                event_name=self.event_config["event"],
            )
        except KeyError as exc:
            raise KeyError(f"`{exc!s}` key missing from configuration")

    def get_times(self) -> Tuple[datetime, Optional[datetime]]:
        event = self.get_marathon()
        event.refresh_all()

        start = event.schedules[0][0].start
        end = event.schedules[0][-1].start
        return (start, end)
