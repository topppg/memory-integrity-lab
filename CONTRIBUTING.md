# Contributing

Use Python 3.11 or later. Runtime and tests use the standard library only.

```sh
python -m unittest discover -v
python -m memory_integrity_lab validate
python -m memory_integrity_lab compare --adapter memory --output reports/memory
python -m memory_integrity_lab compare --adapter sqlite --output reports/sqlite
```

Add an explicit expected event ID to each probe, with the case's requested
tenant, subject, key, and logical time. Do not generate expected output using
the adapter under evaluation. Include a failing control for each new property.
Keep all fixtures synthetic; do not submit production traces, personal data,
credentials, or employer code. Distinguish source-label policy tests from model
behavior tests. Updates to metric definitions must explain the denominator.

CLI exit codes: 0 candidate passed or suite validated; 1 candidate failed;
2 invalid input/configuration. The naive comparison control is expected to fail.

The fifteen local feature branches are ordered. Publish them in order and use
regular merge commits so later branch ancestry remains valid. Never squash or
rebase these staged branches while other local stages depend on them.
