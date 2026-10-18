# Fifteen-stage local publication plan

The implementation was prepared as a bootstrap commit followed by fifteen
feature stages. Each branch below adds exactly one substantive commit on its
predecessor. Public `main` advances through regular pull-request merges.
Author identity uses Giorgio Sarno's public GitHub noreply address. Commits use
their actual creation times.

The stage numbering encodes dependency order. The public PR history records
publication times separately from the original development dates.

| Stage / branch | Proposed PR title | Effective capability and validation |
| --- | --- | --- |
| `stage/01-validated-events` | Validate memory events and queries | Immutable validated wire models; round-trip and malformed-input tests (2 tests) |
| `stage/02-reference-adapter` | Add the reference adapter contract | Protocol, empty retrieval, idempotency and collision rejection (3 tests) |
| `stage/03-temporal-retrieval` | Support explicit as-of memory retrieval | Future exclusion and deterministic tie ordering (4 tests) |
| `stage/04-corrections` | Validate correction provenance | Target existence, scope checks and strictly later corrections (6 tests) |
| `stage/05-tenant-isolation` | Isolate tenant and subject memory | Shared keys across people and tenants, scoped access rejection (7 tests) |
| `stage/06-deletion-replay` | Preserve forgetting during history replay | Tombstones, delayed historical writes, historical queries and later new writes (9 tests) |
| `stage/07-provenance-authority` | Separate stored content from authority | Source policy, provenance and untrusted correction/deletion controls (10 tests) |
| `stage/08-sqlite-adapter` | Add persistent SQLite reference adapter | Transactions, independent connections, rollback and restart (11 tests) |
| `stage/09-anchored-audit` | Verify archives against independent anchors | Content, order and completeness attacks plus compromised-anchor negative control (12 tests) |
| `stage/10-synthetic-scenarios` | Add deterministic synthetic memory histories | Case/probe validation and seeded explicit expectation fixtures (14 tests) |
| `stage/11-metric-evaluator` | Score memory integrity against explicit oracles | Exact-record scoring, denominators, duplicate penalty and canonical scope checks (18 tests) |
| `stage/12-baseline-comparison` | Add failing baseline and adapter comparisons | Intended negative-control failures and SQLite seed matrix (20 tests) |
| `stage/13-portable-reports` | Export portable report evidence | JSON, JUnit XML and escaped standalone HTML (21 tests) |
| `stage/14-cli-packaging` | Package the offline CLI and adapter plugins | Run/compare/validate, strict suite parsing, CLI errors and plugin entry point (24 tests) |
| `stage/15-docs-ci-release` | Document measured results and automate offline checks | Professional README, examples, metric/security guides, Python 3.11/3.12 CI, stronger input/provenance controls and anchored deletion replay (27 tests) |

## Per-stage review gate

From each branch, run `python -m unittest discover -v`. This command works at
all stages without dependency installation. From stage 14 onward, also run:

```sh
python -m memory_integrity_lab validate
python -m memory_integrity_lab compare --adapter memory --output reports/memory
python -m memory_integrity_lab compare --adapter sqlite --output reports/sqlite
```

For stage 15, run the same checks on Python 3.11 and 3.12, validate
`examples/custom-suite.json`, build the sdist and wheel (`uv build`), then install
the wheel into a temporary environment and run the CLI outside the checkout.
Build tooling may need an initial download; runtime tests do not.

Final-stage review hardening deliberately adds checks beyond the original
evaluator: unknown/fabricated provenance cannot receive isolation credit, empty
evaluation cannot pass, archive sequence types and anchors validate strictly,
and anchored replay preserves tombstones. Earlier stages expose their incremental
capability rather than claiming the final security model at every stage.

## Publishing after local review

Create the remote only after publication is authorized. Push bootstrap `main`,
then one stage branch and one PR at a time in the table's order. Before each PR,
fetch `origin/main` and verify the branch contributes exactly one unpublished
commit using `git rev-list --count origin/main..STAGE_BRANCH`. Review the effective
diff with `git diff origin/main...STAGE_BRANCH` and check the merge tree for
conflicts. CI must pass, and branch protections must remain enabled.

Use a **regular merge commit** (`gh pr merge --merge`), never a squash or rebase
merge. Later local branches descend from earlier feature commits. Deleting the
merged remote stage branch is safe; retain local stage refs until all dependent
PRs merge. Fetch after each merge and fast-forward local `main` safely.

If a stage needs a correction, keep subsequent unpublished branches consistent
before continuing. Do not push later stages, tags, or archive refs early. PR
titles should describe effective changes at that point. The detailed README
arrives in stage 15; earlier README is a concise project scaffold, so avoid
claiming final features as already available in earlier published stages.
