# Architecture and adapter integration

The standard-library-only runtime has five boundaries:

1. `models.py` validates immutable events, queries and returned memories.
2. `scenarios.py` defines histories and explicit expected IDs for each probe.
3. An adapter ingests a history prefix and retrieves scoped memories.
4. `evaluate.py` compares against the scenario oracle and records evidence.
5. `reports.py` writes JSON, JUnit XML and escaped, standalone HTML.

The evaluator creates and closes a fresh adapter for each probe. Adapters must
start empty. This makes each probe an independent replay from its declared
prefix and avoids hidden dependence on probe order. The bundled SQLite factory
uses a distinct temporary database per probe. Tests separately verify
persistence and tombstones through independent connections and restart.

## Reference semantics

Memory is single-valued per `(tenant, subject, key)`. Event IDs are globally
unique within an adapter; exact duplicate ingestion is idempotent, while an ID
collision with different content is rejected. Logical `at` values are
nonnegative integers. Writes can arrive out of timestamp order. At equal logical
times, lexicographically greater event IDs win, independent of ingestion order.
The reference is not a bitemporal store: `as_of` constrains event time, not the
historical knowledge available at a wall-clock instant. Probe `after` supplies
the explicit ingestion prefix for that purpose.

Only source `user` is authoritative for retrieval and deletion. The embedding
application must assign this label from authenticated context. Source labels
are not parsed from text. Arbitrary other sources are retained as audit data but
cannot replace or delete authoritative memory. A `supersedes` link requires an
already-ingested authoritative target, the same full scope, and a strictly later
timestamp. Corrections keep earlier facts visible to earlier as-of queries until
a deletion suppresses them. They do not implement a general causal graph.

Every ingested authoritative tombstone suppresses every put with `at` less than
or equal to its timestamp, including historical as-of queries. This privacy
policy takes precedence over as-of reconstruction even if the tombstone's
timestamp is later than the query. A later explicit authoritative put may create
a new value. Old writes arriving later cannot revive a forgotten value.

Replay sorts by `(at, event_id)` so corrections follow strictly earlier targets.
Import must include tombstones. Verify archives against an externally trusted
count and head before importing untrusted histories. Raw replay alone cannot
detect an omitted tombstone. `export_events()` retains plaintext and is not an
erasure interface.

## Plugin contract

Supply a trusted Python zero-argument factory as `module:factory`:

```sh
python -m memory_integrity_lab run \
  --adapter memory_integrity_lab.adapters:InMemoryAdapter \
  --output reports/plugin
```

The factory returns an object implementing the `Adapter` protocol:

```python
def ingest(event: Event) -> None: ...
def retrieve(query: Query) -> list[Memory]: ...
def close() -> None: ...
```

Return original, stable event IDs and full provenance. Converting an external
system's records to `Memory` is the adapter author's responsibility. Unknown IDs
cannot pass exact-match or verified isolation checks. Use factory closures for
local configuration. A plugin executes local code; it is not sandboxed. No API
credentials or network access are required for bundled adapters.

## Trusted archive example

```python
from memory_integrity_lab.audit import seal, verify
from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.models import Event

events = [Event("e1", "org", "city", "Rome", 1),
          Event("e2", "org", "city", "", 2, operation="delete")]
rows, anchor = seal(events)
# Keep anchor.count and anchor.head outside the archive's trust boundary.
restored = InMemoryAdapter.from_events(verify(rows, anchor))
```

The anchor is a trust input, not a security guarantee created by hashing. SQLite
stores unencrypted JSON event records and does not automatically seal its file.
The current implementation reconstructs histories on retrieval and favors clear
reference behavior over production-scale indexing or throughput.
