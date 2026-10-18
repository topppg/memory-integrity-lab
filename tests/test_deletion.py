import unittest

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.models import Event, Query


class DeletionTests(unittest.TestCase):
    def test_forgetting_survives_replay_and_historical_writes(self):
        store = InMemoryAdapter()
        store.ingest(Event("a", "t", "city", "Rome", 1))
        store.ingest(Event("d", "t", "city", "", 3, operation="delete"))
        store.ingest(Event("late", "t", "city", "Florence", 2))
        for source in (store, InMemoryAdapter.from_events(reversed(store.export_events()))):
            for at in (1, 2, 3, 100):
                self.assertEqual([], source.retrieve(Query("t", "city", at)))
            source.ingest(Event("new", "t", "city", "Milan", 4))
            self.assertEqual("Milan", source.retrieve(Query("t", "city", 4))[0].value)

    def test_delete_is_scoped(self):
        store = InMemoryAdapter()
        store.ingest(Event("a", "t", "k", "v", 1, subject="a"))
        store.ingest(Event("d", "t", "k", "", 2, subject="b", operation="delete"))
        self.assertEqual("v", store.retrieve(Query("t", "k", 2, "a"))[0].value)
