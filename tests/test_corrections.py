import unittest

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.models import Event, Query


class CorrectionTests(unittest.TestCase):
    def test_correction_preserves_history(self):
        store = InMemoryAdapter()
        store.ingest(Event("a", "t", "city", "Rome", 1))
        store.ingest(Event("b", "t", "city", "Milan", 2, supersedes="a"))
        self.assertEqual("Rome", store.retrieve(Query("t", "city", 1))[0].value)
        self.assertEqual("Milan", store.retrieve(Query("t", "city", 2))[0].value)

    def test_invalid_target_scope_and_time(self):
        store = InMemoryAdapter()
        store.ingest(Event("a", "t", "city", "Rome", 1))
        for tenant, at, target in (("other", 2, "a"), ("t", 1, "a"), ("t", 2, "missing")):
            with self.subTest(tenant=tenant, at=at), self.assertRaises(ValueError):
                store.ingest(Event("b", tenant, "city", "Milan", at, supersedes=target))
