"""Intentionally flawed control: global latest-value cache ignoring memory policy."""

from .adapters import InMemoryAdapter
from .models import Memory


class NaiveAdapter(InMemoryAdapter):
    def retrieve(self, query):
        candidates = [event for event in self._events.values()
                      if event.key == query.key and event.operation == "put"]
        if not candidates:
            return []
        event = max(candidates, key=lambda item: (item.at, item.event_id))
        return [Memory(event.tenant, event.key, event.value, event.event_id,
                       event.at, event.source, event.subject)]


def compare(cases, candidate_factory, candidate_name="reference", seed=7):
    from .evaluate import evaluate

    cases = tuple(cases)
    return (evaluate(cases, candidate_factory, candidate_name, seed),
            evaluate(cases, NaiveAdapter, "naive-control", seed))
