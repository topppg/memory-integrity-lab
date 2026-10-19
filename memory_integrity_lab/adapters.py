"""Small adapter contract for memory systems under evaluation."""

from typing import Protocol

from .models import Event, Memory, Query


class Adapter(Protocol):
    def ingest(self, event: Event) -> None: ...
    def retrieve(self, query: Query) -> list[Memory]: ...
    def close(self) -> None: ...


class InMemoryAdapter:
    """Reference event store. Duplicate IDs are idempotent, never mutable."""

    def __init__(self):
        self._events: dict[str, Event] = {}

    def ingest(self, event: Event) -> None:
        previous = self._events.get(event.event_id)
        if previous is not None and previous != event:
            raise ValueError("event ID collision")
        self._events[event.event_id] = event

    def retrieve(self, query: Query) -> list[Memory]:
        candidates = [event for event in self._events.values()
                      if event.tenant == query.tenant and event.key == query.key]
        if not candidates:
            return []
        event = max(candidates, key=lambda item: (item.at, item.event_id))
        return [Memory(event.tenant, event.key, event.value, event.event_id,
                       event.at, event.source)]

    def close(self) -> None:
        pass
