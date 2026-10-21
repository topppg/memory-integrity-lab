"""Persistent reference adapter; each operation reads current committed history."""

import json
import sqlite3

from .adapters import InMemoryAdapter
from .models import Event, Query


class SQLiteAdapter:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        self.connection.commit()

    def export_events(self):
        events = [Event.from_dict(json.loads(row[0])) for row in
                  self.connection.execute("SELECT payload FROM events")]
        return sorted(events, key=lambda event: (event.at, event.event_id))

    def ingest(self, event: Event):
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            store = InMemoryAdapter.from_events(self.export_events())
            store.ingest(event)
            self.connection.execute("INSERT OR IGNORE INTO events VALUES (?, ?)",
                                    (event.event_id, json.dumps(event.to_dict(), sort_keys=True)))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def retrieve(self, query: Query):
        return InMemoryAdapter.from_events(self.export_events()).retrieve(query)

    def close(self):
        self.connection.close()
