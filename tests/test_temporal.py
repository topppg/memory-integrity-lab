import unittest

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.models import Event, Query


class TemporalTests(unittest.TestCase):
    def test_as_of_future_and_order_independence(self):
        store = InMemoryAdapter()
        for event in (Event("z", "a", "k", "coffee", 2),
                      Event("a", "a", "k", "tea", 1),
                      Event("b", "a", "k", "water", 2)):
            store.ingest(event)
        self.assertEqual([], store.retrieve(Query("a", "k", 0)))
        self.assertEqual("tea", store.retrieve(Query("a", "k", 1))[0].value)
        self.assertEqual("coffee", store.retrieve(Query("a", "k", 2))[0].value)
