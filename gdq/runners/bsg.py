from datetime import datetime
from typing import Optional, Tuple

from gdq.events.bsg import BSGTracker
from gdq.runners.gdq import Runner as GDQRunner


class Runner(GDQRunner):
    def get_marathon(self) -> BSGTracker:
        if "url" not in self.event_config:
            raise KeyError("`url` key missing from configuration")

        record_offsets = {}
        if "offsets" in self.event_config:
            record_offsets = self.event_config["offsets"]

        return BSGTracker(
            url=self.event_config["url"],
            stream_index=-self.args.stream_index,
            offset=self.args.delta_total,
            record_offsets=record_offsets,
        )

    def get_times(self) -> Tuple[datetime, Optional[datetime]]:
        event = self.get_marathon()
        event.refresh_all()

        start = event.schedules[0][0].start
        end = event.schedules[0][-1].start
        return (start, end)
