"""Test PrefixReplayBackend (RQ3 tách biến): không cần mạng."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from llm import PrefixMismatch, PrefixReplayBackend, ScriptedBackend  # noqa: E402


def _entry(agent, prompt, output):
    return {"agent": agent, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt_chars": len(prompt), "output": output}


class PrefixReplayTest(unittest.TestCase):
    def setUp(self):
        self.trace = [_entry("MetaAgent", "p-meta", "out-meta"),
                      _entry("AnalyzerAgent", "p-a1", "out-a1"),
                      _entry("AnalyzerAgent", "p-a2", "out-a2"),
                      _entry("UnifiedPrunerAgent", "p-pr", "out-pr-cũ")]
        self.live = ScriptedBackend({"UnifiedPrunerAgent": "out-pr-mới"})
        self.live.model = "m"
        self.b = PrefixReplayBackend(self.trace, self.live, ["UnifiedPrunerAgent"])

    def test_replay_in_order_without_cost(self):
        self.assertEqual(self.b.complete("MetaAgent", "p-meta").text, "out-meta")
        self.assertEqual(self.b.complete("AnalyzerAgent", "p-a1").text, "out-a1")
        r = self.b.complete("AnalyzerAgent", "p-a2")
        self.assertEqual((r.text, r.prompt_tokens, r.stop_reason), ("out-a2", 0, "replayed"))
        self.assertEqual(self.live.calls, [])

    def test_live_agent_goes_to_backend(self):
        self.assertEqual(self.b.complete("UnifiedPrunerAgent", "prompt khác").text, "out-pr-mới")
        self.assertEqual(len(self.live.calls), 1)

    def test_prompt_mismatch_raises(self):
        with self.assertRaises(PrefixMismatch):
            self.b.complete("MetaAgent", "p-meta-đã-đổi")

    def test_missing_call_raises(self):
        with self.assertRaises(PrefixMismatch):
            self.b.complete("AggregatorAgent", "x")


if __name__ == "__main__":
    unittest.main()
