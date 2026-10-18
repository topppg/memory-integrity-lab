import tempfile
import unittest
from unittest.mock import patch

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.baseline import compare
from memory_integrity_lab.reports import write_reports
from memory_integrity_lab.scenarios import synthetic_suite


class OfflineTests(unittest.TestCase):
    def test_reference_evaluation_and_reports_without_network(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            results = compare(synthetic_suite(), InMemoryAdapter)
            with tempfile.TemporaryDirectory() as folder:
                write_reports(results, folder)
            self.assertTrue(results[0].passed)
