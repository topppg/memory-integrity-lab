import unittest

from memory_integrity_lab.adapters import InMemoryAdapter, ScopedAdapter
from memory_integrity_lab.models import Event, Query


class IsolationTests(unittest.TestCase):
    def test_subjects_and_tenants(self):
        store = InMemoryAdapter()
        for index, (tenant, subject) in enumerate((("t", "alice"), ("t", "bob"), ("u", "alice"))):
            store.ingest(Event(str(index), tenant, "city", str(index), 1, subject=subject))
        for index, (tenant, subject) in enumerate((("t", "alice"), ("t", "bob"), ("u", "alice"))):
            self.assertEqual(str(index), store.retrieve(Query(tenant, "city", 1, subject))[0].value)
        scoped = ScopedAdapter(store, "t", "alice")
        with self.assertRaises(PermissionError):
            scoped.retrieve(Query("t", "city", 1, "bob"))
        with self.assertRaises(PermissionError):
            scoped.ingest(Event("x", "u", "city", "x", 1, subject="alice"))
