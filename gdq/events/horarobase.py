from abc import abstractmethod
from typing import Iterator

from gdq.events import MarathonBase
from gdq.models import Run
from gdq.parsers import horaro


class HoraroSchedule(MarathonBase):
    # horaro.org keys
    group_name = ""
    current_event: str

    def refresh_all(self) -> None:
        self.schedules = [horaro.read_schedule(self.group_name, self.current_event, self.parse_data)]

    @staticmethod
    @abstractmethod
    def parse_data(keys, schedule, timezone="UTC") -> Iterator[Run]:
        raise NotImplementedError
