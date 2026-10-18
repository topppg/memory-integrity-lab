import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, "-m", "memory_integrity_lab", *args],
                              text=True, capture_output=True, check=False)

    def test_validate_and_compare(self):
        result = self.invoke("validate")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(18, json.loads(result.stdout)["probes"])
        with tempfile.TemporaryDirectory() as output:
            result = self.invoke("compare", "--adapter", "sqlite", "--output", output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(3, len(list(Path(output).iterdir())))
            payload = json.loads((Path(output) / "report.json").read_text())
            self.assertTrue(payload["results"][0]["passed"])
            self.assertFalse(payload["results"][1]["passed"])

    def test_plugin_and_failure_exit_status(self):
        with tempfile.TemporaryDirectory() as output:
            result = self.invoke("run", "--adapter", "memory_integrity_lab.adapters:InMemoryAdapter", "--output", output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(1, self.invoke("run", "--adapter", "naive", "--output", output).returncode)
            self.assertEqual(2, self.invoke("run", "--adapter", "unknown", "--output", output).returncode)

    def test_empty_suite_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.json"
            path.write_text("[]")
            self.assertEqual(2, self.invoke("validate", "--cases", str(path)).returncode)
