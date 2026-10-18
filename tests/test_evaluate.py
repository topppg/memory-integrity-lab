import unittest

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.evaluate import evaluate
from memory_integrity_lab.models import Event, Memory, Query
from memory_integrity_lab.scenarios import Case, Probe, synthetic_suite


class EvaluationTests(unittest.TestCase):
    def test_reference_passes_explicit_oracle(self):
        result = evaluate(synthetic_suite(), InMemoryAdapter)
        self.assertTrue(result.passed)
        self.assertEqual((11, 11), (result.metrics["recall"].numerator, result.metrics["recall"].denominator))
        self.assertEqual(0, result.metrics["stale_rate"].value)

    def test_empty_metrics_are_not_perfect_scores(self):
        result = evaluate((), InMemoryAdapter)
        self.assertIsNone(result.metrics["precision"].value)
        self.assertIsNone(result.metrics["deletion_compliance"].value)

    def test_forged_scope_label_does_not_hide_foreign_provenance(self):
        class Liar(InMemoryAdapter):
            def retrieve(self, query):
                return [Memory("a", "k", "private", "secret", 1, "user")]
        case = Case("foreign", (Event("secret", "b", "k", "private", 1),),
                    (Probe(1, Query("a", "k", 1), (), "isolation"),))
        result = evaluate((case,), Liar)
        self.assertFalse(result.passed)
        self.assertEqual(0, result.metrics["isolation_compliance"].value)

    def test_duplicate_records_reduce_precision(self):
        class Duplicate(InMemoryAdapter):
            def retrieve(self, query):
                return super().retrieve(query) * 2
        result = evaluate(synthetic_suite(), Duplicate)
        self.assertEqual(0.5, result.metrics["precision"].value)
        self.assertFalse(result.passed)
