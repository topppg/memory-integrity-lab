import json
import unittest
import xml.etree.ElementTree as ET

from memory_integrity_lab.adapters import InMemoryAdapter
from memory_integrity_lab.baseline import compare
from memory_integrity_lab.reports import html_report, json_report, junit_report
from memory_integrity_lab.scenarios import synthetic_suite


class ReportTests(unittest.TestCase):
    def test_json_xml_structure_and_html_payload_escaping(self):
        results = compare(synthetic_suite(), InMemoryAdapter)
        self.assertEqual(2, len(json.loads(json_report(results))["results"]))
        root = ET.fromstring(junit_report(results))
        self.assertEqual(36, len(root.findall(".//testcase")))
        self.assertTrue(root.findall(".//failure"))
        page = html_report(results)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)
        self.assertNotIn("https://", page)
