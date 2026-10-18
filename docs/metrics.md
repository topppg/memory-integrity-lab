# Metric definitions

Each probe has a requested tenant, subject, key and as-of logical time, an
ingestion-prefix length, and explicit expected event IDs. The evaluator resolves
IDs from the scenario's original events. It never derives the expected answer
from the reference adapter. Exact equality includes tenant, subject, key, value,
event ID, logical time, and source. Duplicates are counted as extra returned
records using multiset comparison, so duplicates cannot increase recall.

| Metric | Numerator | Denominator | Preferred direction |
| --- | --- | --- | --- |
| precision | Exactly correct returned records, capped by expected multiplicity | All returned records | Higher |
| recall | Exactly correct expected records found, capped by expected multiplicity | All expected records | Higher |
| temporal_correctness | Temporal probes with exact output and no adapter error | Temporal probes | Higher |
| stale_rate | Returned records whose canonical event is in requested scope, is not expected, is no later than query time, and is older than the newest expected event; for empty expectations, any such event no later than query time | All returned records | Lower |
| deletion_compliance | Deletion probes with exact output and no adapter error | Deletion probes | Higher |
| isolation_compliance | Isolation probes with no foreign or unverifiable returned records and no adapter error | Isolation probes | Higher |
| poisoning_resistance | Source-authority probes with exact output and no adapter error | Source-authority probes | Higher |

Zero denominators produce JSON `null` / HTML `n/a`, not a perfect score. An
empty result is not passing. CLI rejects empty suites and cases without probes.
The overall result passes only when every probe matches its explicit oracle and
there are no adapter errors. A retrieval exception cannot pass an empty-answer
probe. Reports retain error class names rather than potentially sensitive
exception messages.

Isolation uses the original event ID to resolve scope independently of the
adapter's returned labels. Unknown event IDs or mismatched record content are
`unverifiable_records`; canonical or claimed foreign scope is `foreign_records`.
Both prevent isolation compliance. An empty adapter can pass this safety metric
but loses recall and fails nonempty-answer probes. This is intentional: privacy
and usefulness are separate properties.

The stale metric does not count future records as stale: they fail temporal
correctness/exact-match checks. It does not establish whether natural-language
facts are true. Precision and recall use authored synthetic expectations, not a
semantic judge. Poisoning resistance tests storage source policy only; there is
no language model in this suite and no measured model prompt-injection defense.

`retrieval_ns` records `perf_counter_ns` measurements around retrieval calls.
These are host-dependent, include SQLite history reconstruction when relevant,
and are not a comparative performance benchmark. Semantic outcomes, IDs and
metrics reproduce for a fixed seed; timings do not. The tool does not currently
measure storage growth, embedding quality, token cost, or answer quality.
