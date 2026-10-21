import unittest

from memory_integrity_lab.models import Event, Query
from memory_integrity_lab.scenarios import Case, Probe, synthetic_suite


class ScenarioTests(unittest.TestCase):
    def test_seeded_reproducibility(self):
        self.assertEqual(synthetic_suite(7), synthetic_suite(7))
        self.assertNotEqual(synthetic_suite(7), synthetic_suite(8))
        self.assertEqual(18, sum(len(case.probes) for case in synthetic_suite()))

    def test_invalid_oracle_rejected(self):
        with self.assertRaises(ValueError):
            Case("invalid", (Event("e", "a", "k", "v", 2),),
                 (Probe(1, Query("b", "k", 3), ("e",), "recall"),))
