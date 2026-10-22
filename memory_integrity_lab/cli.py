import argparse
import importlib
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from .adapters import InMemoryAdapter
from .baseline import NaiveAdapter, compare
from .evaluate import evaluate
from .reports import write_reports
from .scenarios import load_cases, synthetic_suite
from .sqlite_adapter import SQLiteAdapter


def _factory(spec, directory):
    if spec == "memory":
        return InMemoryAdapter
    if spec == "naive":
        return NaiveAdapter
    if spec == "sqlite":
        counter = 0

        def sqlite_factory():
            nonlocal counter
            counter += 1
            return SQLiteAdapter(Path(directory) / f"probe-{counter}.sqlite3")

        return sqlite_factory
    if ":" not in spec:
        raise ValueError("adapter must be memory, sqlite, naive or module:factory")
    module, name = spec.split(":", 1)
    factory = getattr(importlib.import_module(module), name)
    if not callable(factory):
        raise ValueError("adapter factory must be callable")
    return factory


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline synthetic agent-memory integrity evaluation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "compare", "validate"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--seed", type=int, default=7)
        command_parser.add_argument("--cases", type=Path, help="JSON suite; default is built-in synthetic cases")
        if command != "validate":
            command_parser.add_argument("--adapter", default="memory")
            command_parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)
    try:
        cases = (load_cases(json.loads(args.cases.read_text(encoding="utf-8")))
                 if args.cases else synthetic_suite(args.seed))
        # Round-trip through strict wire validation even for builtin fixtures.
        cases = load_cases(json.loads(json.dumps([asdict(case) for case in cases])))
        if args.command == "validate":
            print(json.dumps({"valid": True, "cases": len(cases),
                              "probes": sum(len(case.probes) for case in cases), "seed": args.seed}))
            return 0
        with tempfile.TemporaryDirectory(prefix="memory-integrity-") as directory:
            factory = _factory(args.adapter, directory)
            results = (compare(cases, factory, args.adapter, args.seed) if args.command == "compare"
                       else (evaluate(cases, factory, args.adapter, args.seed),))
            write_reports(results, args.output)
            print(json.dumps({"adapter": args.adapter, "passed": results[0].passed,
                              "probes": len(results[0].outcomes),
                              "metrics": {key: item.to_dict() for key, item in results[0].metrics.items()},
                              "output": str(args.output)}, sort_keys=True))
            # Comparison's intentionally failing baseline is evidence, not candidate failure.
            return 0 if results[0].passed else 1
    except (ValueError, TypeError, OSError, ImportError, AttributeError) as exc:
        parser.error(f"{type(exc).__name__}: invalid suite or adapter configuration")


if __name__ == "__main__":
    raise SystemExit(main())
