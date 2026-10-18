import unittest

from memory_integrity_lab.models import Event, Query


class ModelTests(unittest.TestCase):
    def test_round_trip(self):
        event = Event("e", "a", "drink", "tea", 1)
        self.assertEqual(event, Event.from_dict(event.to_dict()))

    def test_invalid_inputs(self):
        for changes in ({"at": True}, {"tenant": " "}, {"value": 4},
                        {"operation": "run"}, {"operation": "delete"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Event(**({"event_id": "e", "tenant": "a", "key": "k",
                          "value": "v", "at": 0} | changes))
        with self.assertRaises(ValueError):
            Query("a", "k", -1)
