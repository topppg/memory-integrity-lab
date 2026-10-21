import copy
import unittest

from memory_integrity_lab.audit import seal, verify
from memory_integrity_lab.models import Event


class AuditTests(unittest.TestCase):
    def test_round_trip_and_attack_controls(self):
        events = [Event("a", "t", "k", "tea", 1), Event("b", "t", "k", "coffee", 2)]
        rows, anchor = seal(events)
        self.assertEqual(events, verify(rows, anchor))
        changed = copy.deepcopy(rows)
        changed[0]["event"]["value"] = "poison"
        for attacked in (changed, rows[::-1], rows[:-1], [], rows + [rows[-1]]):
            with self.subTest(attacked=attacked), self.assertRaises(ValueError):
                verify(attacked, anchor)
        forged, _ = seal([Event("a", "t", "k", "forged", 1), events[1]])
        with self.assertRaises(ValueError):
            verify(forged, anchor)
        # Explicit negative control: replacing the anchor defeats this threat model.
        forged, forged_anchor = seal([Event("x", "t", "k", "forged", 1)])
        self.assertEqual("forged", verify(forged, forged_anchor)[0].value)
