"""Kiểm thử kiểm chứng v2 bằng kết quả mô phỏng, không gọi API."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from llm import LLMError, LLMResult, ScriptedBackend
from pipeline import PRUNER, VALIDATOR, V2_PRUNER_MAX_TOKENS, PromptStore, Sample, verify_candidates


def assessments(*items):
    return json.dumps({"assessments": items})


class VerificationTest(unittest.TestCase):
    sample = Sample(id="1", code="void f(int i) {\n  if (i < 0 || i >= 8) return;\n  a[i] = 0;\n}",
                    context="Fields may contain {function_code}.")
    prompts = PromptStore(ROOT / "prompts_v2")
    candidate = {"cwe": "CWE-787", "code_line": "3",
                 "description": "Nội dung ngoài CWE và vị trí không đi vào v2"}
    rejection = {
        "issue_id": 1, "verdict": "reject", "rejection_basis": "all_paths_guarded",
        "reason": "Điều kiện ở dòng 2 kiểm tra hai biên và trả về trước phép ghi",
        "evidence": {"line": 2, "quote": "if (i < 0 || i >= 8) return;"},
    }

    def run_v2(self, pruned, judged, candidates=None):
        class Backend(ScriptedBackend):
            budgets = []

            def complete(self, agent, prompt, *, max_tokens=None):
                self.budgets.append((agent, max_tokens))
                return super().complete(agent, prompt, max_tokens=max_tokens)

        backend = Backend({PRUNER: pruned, VALIDATOR: judged})
        result = verify_candidates(
            self.sample, backend, self.prompts, [self.candidate] if candidates is None else candidates)
        return result, backend

    def test_guard_with_grounded_evidence_rejects(self):
        rec, backend = self.run_v2(assessments(), assessments(self.rejection))
        self.assertEqual(rec["decision"], "benign")
        self.assertEqual(rec["issues"][0]["verdict"], "no")
        self.assertEqual(backend.budgets, [(PRUNER, V2_PRUNER_MAX_TOKENS), (VALIDATOR, None)])
        self.assertIn(self.sample.context, dict(backend.calls)[PRUNER])
        self.assertNotIn(self.candidate["description"], dict(backend.calls)[PRUNER])

    def test_optional_assumption_or_incorrect_citation_cannot_reject(self):
        for change in ({"rejection_basis": "optional_condition_contradicted"},
                       {"evidence": {"line": 2, "quote": "return 1;"}},
                       {"evidence": None}):
            with self.subTest(change=change):
                rec, _ = self.run_v2(assessments(), assessments({**self.rejection, **change}))
                self.assertEqual(rec["decision"], "vulnerable")
                self.assertEqual(rec["issues"][0]["verdict"], "yes")

    def test_pruner_cannot_delete_original_issue_even_if_truncated(self):
        prune = LLMResult(assessments({"issue_id": 1}), stop_reason="max_tokens")
        rec, backend = self.run_v2(
            prune, assessments(self.rejection, {"issue_id": 2, "verdict": "keep"}),
            [self.candidate, self.candidate])
        self.assertEqual(rec["decision"], "vulnerable")
        self.assertEqual([r["issue_id"] for r in rec["issues"]], [1, 2])
        self.assertEqual(rec["trace"][0]["stop_reason"], "max_tokens")
        prompt = dict(backend.calls)[VALIDATOR]
        self.assertIn('"issue_id": 2', prompt)
        self.assertIn("Advisory Pruner annotations:\n[]", prompt)

    def test_missing_or_duplicate_validator_id_cannot_turn_sample_benign(self):
        for judged in (assessments(), assessments(self.rejection, self.rejection)):
            rec, _ = self.run_v2(assessments(), judged)
            self.assertEqual((rec["decision"], rec["error"]["kind"]), ("unknown", "schema_error"))

    def test_refusal_is_unknown_and_stops_pipeline(self):
        rec, backend = self.run_v2(LLMError("refusal", stop_reason="refusal"), assessments())
        self.assertEqual(rec["decision"], "unknown")
        self.assertEqual(rec["trace"][0]["stop_reason"], "refusal")
        self.assertEqual(len(backend.calls), 1)

    def test_zero_candidates_needs_no_model_calls(self):
        rec, backend = self.run_v2(assessments(), assessments(), [])
        self.assertEqual(rec["decision"], "benign")
        self.assertEqual(backend.calls, [])


if __name__ == "__main__":
    unittest.main()
