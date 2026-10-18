"""Independent oracle scoring; adapters never supply expected identities or values."""

from collections import Counter
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from .models import Memory


@dataclass(frozen=True)
class Metric:
    numerator: int
    denominator: int

    @property
    def value(self):
        return self.numerator / self.denominator if self.denominator else None

    def to_dict(self):
        return asdict(self) | {"value": self.value}


@dataclass
class Result:
    adapter: str
    seed: int
    outcomes: list[dict]
    metrics: dict[str, Metric]
    retrieval_ns: list[int]

    @property
    def passed(self):
        return bool(self.outcomes) and all(outcome["passed"] for outcome in self.outcomes)

    def to_dict(self):
        return {"schema_version": 1, "adapter": self.adapter, "seed": self.seed,
                "passed": self.passed, "outcomes": self.outcomes,
                "metrics": {key: metric.to_dict() for key, metric in self.metrics.items()},
                "retrieval_ns": self.retrieval_ns}


def _signature(memory):
    return (memory.tenant, memory.subject, memory.key, memory.value,
            memory.event_id, memory.at, memory.source)


def _canonical(event):
    return Memory(event.tenant, event.key, event.value, event.event_id,
                  event.at, event.source, event.subject)


def evaluate(cases, factory, name="reference", seed=7):
    outcomes, durations = [], []
    counts = Counter()
    for case in cases:
        # One fresh instance per probe also tests replay and avoids probe-order effects.
        for index, probe in enumerate(case.probes):
            expected_events = {event.event_id: event for event in case.events[:probe.after]}
            expected = [_canonical(expected_events[event_id]) for event_id in probe.expected_ids]
            error, actual, adapter = None, [], None
            try:
                adapter = factory()
                for event in case.events[:probe.after]:
                    adapter.ingest(event)
                start = perf_counter_ns()
                actual = adapter.retrieve(probe.query)
                durations.append(perf_counter_ns() - start)
                if not isinstance(actual, list) or any(not isinstance(item, Memory) for item in actual):
                    raise ValueError("adapter must return list[Memory]")
            except Exception as exc:
                # Reports retain type, not exception text that may include user payloads.
                error, actual = type(exc).__name__, []
            finally:
                if adapter is not None:
                    try:
                        adapter.close()
                    except Exception as exc:
                        error = type(exc).__name__
            exact = Counter(map(_signature, expected))
            returned = Counter(map(_signature, actual))
            correct = sum((exact & returned).values())
            passed = exact == returned and error is None
            foreign = stale = unverifiable = 0
            for item in actual:
                canonical = expected_events.get(item.event_id)
                requested_scope = (probe.query.tenant, probe.query.subject, probe.query.key)
                claimed_scope = (item.tenant, item.subject, item.key)
                canonical_scope = ((canonical.tenant, canonical.subject, canonical.key)
                                   if canonical else None)
                # Resolve canonical source scope so forged return labels cannot hide leakage.
                foreign += int(claimed_scope != requested_scope or
                               (canonical is not None and canonical_scope != requested_scope))
                unverifiable += int(canonical is None or
                                    (canonical is not None and _signature(item) != _signature(_canonical(canonical))))
                if canonical and canonical_scope == requested_scope and canonical.event_id not in probe.expected_ids:
                    latest_expected = max((event.at for event in expected_events.values()
                                           if event.event_id in probe.expected_ids), default=probe.query.as_of + 1)
                    stale += int(canonical.at < latest_expected and canonical.at <= probe.query.as_of)
            counts["correct"] += correct
            counts["returned"] += len(actual)
            counts["expected"] += len(expected)
            counts["stale"] += stale
            counts[f"{probe.category}_total"] += 1
            counts[f"{probe.category}_pass"] += int(passed)
            if probe.category == "isolation":
                counts["isolation_safe"] += int(foreign == 0 and unverifiable == 0 and error is None)
            outcomes.append({"case": case.case_id, "probe": index, "category": probe.category,
                             "query": asdict(probe.query), "passed": passed, "error": error,
                             "expected": [asdict(item) for item in expected],
                             "actual": [asdict(item) for item in actual], "foreign_records": foreign,
                             "unverifiable_records": unverifiable})
    metrics = {"precision": Metric(counts["correct"], counts["returned"]),
               "recall": Metric(counts["correct"], counts["expected"]),
               "stale_rate": Metric(counts["stale"], counts["returned"])}
    for name_key, category in (("temporal_correctness", "temporal"),
                               ("deletion_compliance", "deletion"),
                               ("poisoning_resistance", "poisoning")):
        metrics[name_key] = Metric(counts[f"{category}_pass"], counts[f"{category}_total"])
    metrics["isolation_compliance"] = Metric(counts["isolation_safe"], counts["isolation_total"])
    return Result(name, seed, outcomes, metrics, durations)
