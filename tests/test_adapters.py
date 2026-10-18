import unittest

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.models import Event, Query


class AdapterTests(unittest.TestCase):
    def test_empty_and_idempotent(self):
        store = InMemoryAdapter()
        self.assertEqual([], store.retrieve(Query("a", "k", 10)))
        event = Event("e", "a", "k", "v", 1)
        store.ingest(event)
        store.ingest(event)
        self.assertEqual(["v"], [m.value for m in store.retrieve(Query("a", "k", 10))])
        with self.assertRaises(ValueError):
            store.ingest(Event("e", "a", "k", "changed", 1))
