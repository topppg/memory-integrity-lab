import tempfile
import unittest
from pathlib import Path

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.baseline import compare
from memory_integrity_lab.evaluate import evaluate
from memory_integrity_lab.scenarios import synthetic_suite
from memory_integrity_lab.sqlite_adapter import SQLiteAdapter


class ControlTests(unittest.TestCase):
    def test_negative_control_fails_each_intended_category(self):
        good, bad = compare(synthetic_suite(), InMemoryAdapter)
        self.assertTrue(good.passed)
        self.assertFalse(bad.passed)
        for metric in ("precision", "recall", "temporal_correctness", "deletion_compliance",
                       "isolation_compliance", "poisoning_resistance"):
            with self.subTest(metric=metric):
                self.assertLess(bad.metrics[metric].value, 1)
        self.assertGreater(bad.metrics["stale_rate"].value, 0)
        self.assertTrue(any(outcome["passed"] for outcome in bad.outcomes))

    def test_sqlite_matches_reference_over_seed_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            count = 0

            def factory():
                nonlocal count
                count += 1
                return SQLiteAdapter(Path(directory) / f"{count}.sqlite3")

            for seed in (0, 7, 42):
                self.assertTrue(evaluate(synthetic_suite(seed), factory, "sqlite", seed).passed)
