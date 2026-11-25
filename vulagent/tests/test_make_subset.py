#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test make_subset.py (PLAN §0.4 T3) trên dữ liệu giả, không cần repo gốc."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import make_subset  # noqa: E402


def fake_lines(n_pairs, dup_idx=None):
    """Cặp k có idx 10k (vuln) và 10k+1 (fixed); dup_idx={k: idx} ghi đè idx vuln của cặp k."""
    lines = []
    for k in range(n_pairs):
        iv = (dup_idx or {}).get(k, 10 * k)
        lines.append(json.dumps({"idx": iv, "func": "f", "target": 1}).encode() + b"\n")
        lines.append(json.dumps({"idx": 10 * k + 1, "func": "g", "target": 0}).encode() + b"\n")
    return lines


class MakeSubsetTest(unittest.TestCase):
    def test_pairs_by_line_order(self):
        pairs = make_subset.load_pairs(fake_lines(3))
        self.assertEqual([(p["pair"], p["line"], p["idx_vul"], p["idx_fix"]) for p in pairs],
                         [(0, 1, 0, 1), (1, 3, 10, 11), (2, 5, 20, 21)])

    def test_rejects_wrong_target_order_and_odd_lines(self):
        lines = fake_lines(2)
        lines[2], lines[3] = lines[3], lines[2]
        with self.assertRaises(ValueError):
            make_subset.load_pairs(lines)
        with self.assertRaises(ValueError):
            make_subset.load_pairs(fake_lines(2)[:3])

    def test_duplicate_idx_pairs_are_excluded(self):
        # cặp 3 và 7 dùng chung idx vuln 999 → loại cả hai
        pairs = make_subset.load_pairs(fake_lines(20, {3: 999, 7: 999}))
        self.assertEqual(make_subset.duplicate_pairs(pairs), [3, 7])
        chosen, dups = make_subset.select(pairs, 18, seed=521)
        self.assertEqual(dups, [3, 7])
        self.assertEqual(len(chosen), 18)
        self.assertNotIn(3, [p["pair"] for p in chosen])
        with self.assertRaises(ValueError):
            make_subset.select(pairs, 19, seed=521)

    def test_selection_is_deterministic_and_in_source_order(self):
        pairs = make_subset.load_pairs(fake_lines(50))
        a, _ = make_subset.select(pairs, 10, seed=521)
        b, _ = make_subset.select(pairs, 10, seed=521)
        c, _ = make_subset.select(pairs, 10, seed=1)
        ka, kc = [p["pair"] for p in a], [p["pair"] for p in c]
        self.assertEqual(ka, [p["pair"] for p in b])
        self.assertEqual(ka, sorted(ka))
        self.assertNotEqual(ka, kc)


if __name__ == "__main__":
    unittest.main()
