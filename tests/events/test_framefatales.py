from datetime import datetime, timezone
import json
import unittest

from gdq.events import framefatales
from gdq.models import Run


class TestFrameFatales(unittest.TestCase):
    keys = ["Description"]

    def test_parse_data(self):
        expected_run = Run(
            game="Community Spotlight: Metroid Prime 2 Edition",
            platform="",
            category="",
            runners=[""],
            start=datetime(2019, 5, 14, 0, 45, tzinfo=timezone.utc),
            estimate=5400,
        )
        fixture = (
            '{"length":"PT1H30M","length_t":5400,"scheduled":"2019-05-13T20:45:00-04:00",'
            '"scheduled_t":1557794700,"data":["Community Spotlight: Metroid Prime 2 Edition"]}'
        )
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.FrameFatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])

    def test_parse_data_with_category(self):
        expected_run = Run(
            game="Bioshock Infifnite",
            platform="",
            category="any%HRH mod",
            runners=["Katlink"],
            start=datetime(2019, 5, 14, 4, 53, tzinfo=timezone.utc),
            estimate=7200,
        )
        fixture = (
            '{"length":"PT2H","length_t":7200,"scheduled":"2019-05-14T00:53:00-04:00",'
            '"scheduled_t":1557809580,"data":["Bioshock Infifnite any%HRH mod by Katlink"]}'
        )
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.FrameFatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])

    def test_parse_data_race(self):
        expected_run = Run(
            game="Final Fantasy IV Free Enterprise (League Forge) Race",
            platform="",
            category="",
            runners=["Netara v Demerine"],
            start=datetime(2019, 5, 14, 20, 50, tzinfo=timezone.utc),
            estimate=7500,
        )
        fixture = (
            '{"length":"PT2H05M","length_t":7500,"scheduled":"2019-05-14T16:50:00-04:00","scheduled_t":1557867000,'
            '"data":["Final Fantasy IV Free Enterprise (League Forge) Race of Netara v Demerine"]}'
        )
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.FrameFatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])

    def test_parse_data_confusing_runners(self):
        expected_run = Run(
            game="The Legend of Zelda: A Link tot he Past",
            platform="",
            category="any%MG, no save+quit Race",
            runners=["EmoSaru and Kelpsey"],
            start=datetime(2019, 8, 20, 18, 39, tzinfo=timezone.utc),
            estimate=5700,
        )
        fixture = (
            '{"length":"PT1H35M","length_t":5700,"scheduled":"2019-08-20T14:39:00-04:00","scheduled_t":1566326340,'
            '"data":["The Legend of Zelda: A Link tot he Past any%MG, no save+quit Race with EmoSaru and Kelpsey"]}'
        )
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.FrameFatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])
