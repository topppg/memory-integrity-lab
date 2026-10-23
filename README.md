# Memory Integrity Lab

**A deterministic, offline regression harness for the integrity of agent memory.**

Evaluate whether a memory adapter retrieves the right fact for the right person,
respects changes over time, suppresses forgotten values during replay, and
preserves verifiable provenance. Every bundled history is synthetic. The runtime
and tests use Python's standard library; there is no model, embedding service,
external account, or API key to configure.

This is an engineering regression suite with explicit expected answers. It is
not a scientific benchmark, production memory service, or security certification.

## What it demonstrates

- Validated event, query, returned-memory, case and probe models.
- Reference in-memory and transactional SQLite adapters with the same semantics.
- Separate tenant and subject namespaces, including people sharing the same key.
- Event-time retrieval, correction links, deterministic equal-time ordering, and
  histories arriving out of order.
- Retroactive logical forgetting that survives replay, delayed old writes, and
  SQLite restart; a later explicit write can create a new memory.
- Source-authority policy that keeps untrusted stored content from replacing
  authenticated user facts. This tests storage policy, not LLM behavior.
- Ordered archive verification against a separately trusted head digest and
  event count, with tamper, reorder, truncation and recomputed-chain controls.
- An independent scenario oracle, explicit metric denominators, an intentionally
  flawed baseline, and reports that preserve probe-level evidence.
- A small plugin adapter contract and JSON/JUnit/self-contained HTML output.

## Run locally

Use Python **3.11 or later** from the repository root:

```sh
python -m unittest discover -v
python -m memory_integrity_lab validate
python -m memory_integrity_lab compare --adapter memory --output reports/memory
python -m memory_integrity_lab compare --adapter sqlite --output reports/sqlite
```

Open `reports/memory/report.html` to inspect a standalone report. Each output
directory also contains `report.json` and `report.xml`. HTML uses escaped dynamic
content and loads no external scripts or assets. Report values remain visible
as evidence; only the bundled synthetic data is intended for public sharing.

An optional installation provides the `memory-integrity` command:

```sh
python -m pip install .
memory-integrity run --adapter memory --output reports/run
```

Package installation needs the setuptools build tool; direct execution and the
regression suite require no dependency installation. CI runs the suite and CLI
from a checkout on Python 3.11 and 3.12 without service calls or package installs.
Provisioning the hosted runner and downloading Actions are outside that offline
evaluation boundary.

## Measured local results

The default seed-7 suite contains **4 histories, 18 probes, and 11 expected
records**. These are measured local results from the commands above:

| Measure | In-memory reference | SQLite reference | Naive control |
| --- | ---: | ---: | ---: |
| Exact probes passed | 18/18 | 18/18 | 6/18 |
| Record precision | 11/11 | 11/11 | 5/17 |
| Record recall | 11/11 | 11/11 | 5/11 |
| Temporal correctness | 4/4 | 4/4 | 1/4 |
| Deletion compliance | 4/4 | 4/4 | 0/4 |
| Isolation compliance | 4/4 | 4/4 | 1/4 |
| Source-authority poisoning probes | 2/2 | 2/2 | 0/2 |
| Stale returned records (lower is better) | 0/11 | 0/11 | 2/17 |

The local test suite currently passes **27 tests on both Python 3.11 and 3.12**.
Tests also evaluate SQLite with seeds 0, 7 and 42, verify separate-connection
persistence, reject malformed inputs, exercise CLI exit codes, block socket
creation during reference evaluation, check report escaping, and detect forged
provenance. Source and wheel distributions build successfully, and the installed
wheel's CLI runs outside the source tree.

These results show that the intended invariants and failing controls execute.
They do not estimate performance on real conversations or prove protection
against arbitrary attacks. A fixed seed reproduces histories, semantic outcomes,
and scores. Nanosecond retrieval timings are recorded separately and vary by host.

## Four synthetic histories

| History | Checks |
| --- | --- |
| Preference history | Earlier preferences, future-as-of exclusion, explicit correction, missing key |
| Forget and late replay | Tombstone, delayed old write, historical query after forgetting, fresh later write |
| Same key, distinct people | Two subjects in one tenant, same subject in another tenant, unknown subject |
| Untrusted content authority | A document containing malicious instructions and an untrusted deletion |

Each probe declares how many events to ingest, its query, and expected event IDs.
The evaluator resolves those IDs from the original scenario rather than asking
the adapter for expected values. Exact matches include value, tenant, subject,
key, event ID, source, and logical time. Duplicate returns count against precision.
Unknown or fabricated provenance cannot receive verified isolation credit.

The naive control selects the latest put globally by key. It ignores scopes,
as-of time, deletion, and source authority. Its failures are intentional and make
the suite's detection behavior observable. Comparison exits successfully when
the candidate passes even though that control fails.

## Custom suites and adapters

```sh
python -m memory_integrity_lab validate --cases examples/custom-suite.json
python -m memory_integrity_lab run --cases examples/custom-suite.json --output reports/custom
python -m memory_integrity_lab run \
  --adapter memory_integrity_lab.adapters:InMemoryAdapter --output reports/plugin
```

`validate` checks a suite's structure and expectation references. It does not
execute an adapter or certify that an authored expectation captures intended
real-world semantics. `run` evaluates one adapter; `compare` adds the naive
control. Exit codes are **0** for a passing candidate/valid suite, **1** for a
failing candidate, and **2** for invalid input or adapter configuration.

A trusted zero-argument plugin factory returns an object with `ingest(Event)`,
`retrieve(Query) -> list[Memory]`, and `close()`. It must start empty: the
evaluator creates a fresh adapter for every probe and replays the declared
history prefix. See [adapter integration and semantics](docs/architecture.md)
for the full contract and anchored archive example.

## Reading the scores

Precision and recall count exact records. Temporal, deletion, source-authority,
and isolation metrics count eligible probes. Zero denominators are `null` in
JSON and `n/a` in HTML, and an empty result is not passing. Returning nothing
can satisfy a privacy check but loses recall; use the metrics together.

Foreign records resolve to a different original scope or claim a different
scope. Unknown IDs or altered provenance are recorded separately as
unverifiable; both prevent isolation compliance. Stale rate counts older
canonical in-scope records rather than future records, which instead fail
temporal checks. [Full metric definitions](docs/metrics.md) specify every
numerator, denominator, and limitation.

## Scope and trust limits

The integrating application must authenticate callers and assign tenant,
subject and source labels. A string such as `source="user"` is not proof of
identity. Stored instructions never acquire authority from their content.

Forgetting suppresses retrieval but retains plaintext in storage and audit
history. It is not physical or backup erasure. All ingested authoritative
tombstones apply even to earlier as-of queries; this deliberately gives
forgetting priority over reconstructing an old answer. An omitted tombstone
cannot be detected by plain replay.

Audit verification detects alterations only with an independently trusted
original count and head digest. If an attacker replaces both archive and
anchor, they can forge a chain. SQLite files are not automatically audited,
encrypted or authenticated. The archive utility does not provide signatures.
Read the [security model](SECURITY.md) before extending an adapter.

The harness does not currently test vector similarity, semantic extraction,
real model responses, prompt-injection behavior in a model, distributed
concurrency, physical erasure, storage growth, or production-scale throughput.
SQLite history reconstruction is intentionally simple reference behavior.

## Development and staged publication

The repository was prepared locally as a bootstrap commit followed by
**15 ordered feature branches**, each with one substantive feature commit.
The [pull request history](https://github.com/topppg/memory-integrity-lab/pulls?q=is%3Apr)
shows publication progress. See the
[release plan](docs/release-plan.md) for all branches, effective PR titles,
stage-specific validation, and merge instructions. Publish stages in order
with regular merge commits to preserve later branch ancestry.

Contributions should add a concrete invariant, an explicit oracle, and a failing
control. See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under
[Apache-2.0](LICENSE). Created by Giorgio Sarno.
