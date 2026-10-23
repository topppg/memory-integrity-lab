"""Ordered hash-chain verification against a separately trusted count and head.

An attacker controlling both archive and anchor can forge both. This module does
not authenticate sources, encrypt records, or protect the anchor for the caller.
"""

import hashlib
import json
from dataclasses import dataclass

from .models import Event


@dataclass(frozen=True)
class Anchor:
    count: int
    head: str

    def __post_init__(self):
        if type(self.count) is not int or self.count < 0:
            raise ValueError("anchor count must be a nonnegative integer")
        if (not isinstance(self.head, str) or len(self.head) != 64
                or any(character not in "0123456789abcdef" for character in self.head)):
            raise ValueError("anchor head must be a SHA-256 hex digest")


def _digest(previous, event):
    payload = json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((previous + "\n" + payload).encode()).hexdigest()


def seal(events):
    previous, rows = "0" * 64, []
    for index, event in enumerate(events):
        current = _digest(previous, event)
        rows.append({"sequence": index, "event": event.to_dict(), "previous": previous, "hash": current})
        previous = current
    return rows, Anchor(len(rows), previous)


def verify(rows, anchor: Anchor):
    if not isinstance(rows, list) or len(rows) != anchor.count:
        raise ValueError("archive count differs from trusted anchor")
    previous, events, seen = "0" * 64, [], set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"sequence", "event", "previous", "hash"}:
            raise ValueError("invalid archive row")
        event = Event.from_dict(row["event"])
        if event.event_id in seen:
            raise ValueError("duplicate event ID in archive")
        if (type(row["sequence"]) is not int or row["sequence"] != index or row["previous"] != previous
                or row["hash"] != _digest(previous, event)):
            raise ValueError("archive content or ordering was altered")
        seen.add(event.event_id)
        previous = row["hash"]
        events.append(event)
    if previous != anchor.head:
        raise ValueError("archive head differs from trusted anchor")
    return events
