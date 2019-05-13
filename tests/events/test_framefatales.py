from datetime import datetime
import json
import unittest

from dateutil import tz

from gdq.events import framefatales
from gdq.models import Run


class TestFrameFatales(unittest.TestCase):
    keys = ["Description"]

    def test_parse_data(self):
        expected_run = Run(
            game = "Community Spotlight: Metroid Prime 2 Edition",
            platform = "",
            category = "",
            runner = "",
            start = datetime(2019, 5, 14, 0, 45, tzinfo=tz.gettz("UTC")),
            estimate = 5400,
        )
        fixture = '{"length":"PT1H30M","length_t":5400,"scheduled":"2019-05-13T20:45:00-04:00","scheduled_t":1557794700,"data":["Community Spotlight: Metroid Prime 2 Edition"]}'
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])

    def test_parse_data_with_category(self):
        expected_run = Run(
            game = "Bioshock Infifnite",
            platform = "",
            category = "any%HRH mod",
            runner = "Katlink",
            start = datetime(2019, 5, 14, 4, 53, tzinfo=tz.gettz("UTC")),
            estimate = 7200,
        )
        fixture = '{"length":"PT2H","length_t":7200,"scheduled":"2019-05-14T00:53:00-04:00","scheduled_t":1557809580,"data":["Bioshock Infifnite any%HRH mod by Katlink"]}'
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])

    def test_parse_data_race(self):
        expected_run = Run(
            game = "Final Fantasy IV Free Enterprise (League Forge) Race",
            platform = "",
            category = "",
            runner = "Netara, Demerine",
            start = datetime(2019, 5, 14, 20, 50, tzinfo=tz.gettz("UTC")),
            estimate = 7500,
        )
        fixture = '{"length":"PT2H05M","length_t":7500,"scheduled":"2019-05-14T16:50:00-04:00","scheduled_t":1557867000,"data":["Final Fantasy IV Free Enterprise (League Forge) Race of Netara v Demerine"]}'
        data = [
            json.loads(fixture)
        ]
        runs = list(framefatales.parse_data(self.keys, data))
        self.assertEqual(runs, [expected_run])
