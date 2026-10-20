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
        if event.supersedes is not None:
            target = self._events.get(event.supersedes)
            if target is None:
                raise ValueError("correction target must already exist")
            if (target.tenant, target.subject, target.key) != (event.tenant, event.subject, event.key):
                raise ValueError("correction must share target scope")
            if event.at <= target.at:
                raise ValueError("correction must be later than target")
        self._events[event.event_id] = event

    def retrieve(self, query: Query) -> list[Memory]:
        candidates = [event for event in self._events.values()
                      if event.tenant == query.tenant and event.key == query.key
                      and event.subject == query.subject
                      and event.at <= query.as_of]
        if not candidates:
            return []
        event = max(candidates, key=lambda item: (item.at, item.event_id))
        return [Memory(event.tenant, event.key, event.value, event.event_id,
                       event.at, event.source, event.subject)]

    def close(self) -> None:
        pass


class ScopedAdapter:
    """Application boundary that rejects a caller changing their assigned scope."""

    def __init__(self, inner: Adapter, tenant: str, subject: str):
        Query(tenant, "scope-validation", 0, subject)
        self.inner, self.tenant, self.subject = inner, tenant, subject

    def _check(self, value):
        if (value.tenant, value.subject) != (self.tenant, self.subject):
            raise PermissionError("request outside assigned tenant/subject")

    def ingest(self, event: Event) -> None:
        self._check(event)
        self.inner.ingest(event)

    def retrieve(self, query: Query) -> list[Memory]:
        self._check(query)
        return self.inner.retrieve(query)

    def close(self) -> None:
        self.inner.close()
