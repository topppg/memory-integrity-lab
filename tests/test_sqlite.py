import tempfile
import unittest
from pathlib import Path

from memory_integrity_lab.models import Event, Query
from memory_integrity_lab.sqlite_adapter import SQLiteAdapter


class SQLiteTests(unittest.TestCase):
    def test_separate_connections_restart_and_tombstone(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.sqlite3"
            writer, reader = SQLiteAdapter(path), SQLiteAdapter(path)
            writer.ingest(Event("a", "t", "city", "Rome", 1))
            self.assertEqual("Rome", reader.retrieve(Query("t", "city", 1))[0].value)
            writer.ingest(Event("d", "t", "city", "", 2, operation="delete"))
            writer.close()
            reader.close()
            reopened = SQLiteAdapter(path)
            reopened.ingest(Event("late", "t", "city", "Rome", 1))
            self.assertEqual([], reopened.retrieve(Query("t", "city", 20)))
            with self.assertRaises(ValueError):
                reopened.ingest(Event("a", "t", "city", "changed", 1))
            self.assertEqual([], reopened.retrieve(Query("t", "city", 20)))
            reopened.close()
