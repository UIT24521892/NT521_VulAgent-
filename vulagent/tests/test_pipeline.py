#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pipeline của nhóm. Không cần mạng, không cần repo gốc (dùng prompt giả trong thư mục tạm).
Chạy: python3 -m unittest discover -s tests -v   (từ thư mục vulagent/)
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from llm import LLMError, LLMResult, ReplayBackend, ScriptedBackend, LLM_ERROR_SENTINEL  # noqa: E402
from pipeline import PromptStore, Sample, analyse, analyse_cot, number_code, parse_json  # noqa: E402
from schema import validate_prototype_output                                   # noqa: E402
import metrics                                                                 # noqa: E402

PROMPTS = {
    "MetaAgent": "META {function_code}",
    "AnalyzerAgent": "ANALYZE {function_code}",
    "BehaviorAnalyzerAgent": "BEHAVE {function_code}",
    "AggregatorAgent": "AGG {function_code} {all_agent_outputs}",
    "TriggerPlannerAgent": "PLAN {function_code} {report_text}",
    "UnifiedPrunerAgent": "PRUNE {function_code} proj={proj} name={name} {report_text} ctx={code_context}",
    "FinalValidatorAgent": "FINAL {function_code} proj={proj} {full_report_text}",
}

META_OUT = '{"activated_agents":["AnalyzerAgent","BehaviorAnalyzerAgent"]}'
DETECT_OUT = '{"vulnerability_reported":true,"confirmed_issues":[{"cwe":"CWE-78","description":"d"}]}'
AGG_OUT = '{"vulnerability_reported":true,"confirmed_issues":[{"cwe":"CWE-78","code_line":"2","description":"d"}]}'
PLAN_OUT = '{"confirmed_issues":[{"cwe":"CWE-78","trigger_path":"A1 -> L2"}]}'
PRUNE_OUT = '```json\n{"confirmed_issues":[{"cwe":"CWE-78","assumptions":"A1[plausible]"}]}\n```'


def final_out(verdict):
    return json.dumps({"reported_issues": [{
        "cwe": "CWE-78", "code_line": "2", "trigger_path": "A1 -> L2: system(cmd)",
        "Is it valid?": verdict, "Reason for judgment": "không có guard trước sink"}]})


def script(**override):
    s = {"MetaAgent": META_OUT, "AnalyzerAgent": DETECT_OUT, "BehaviorAnalyzerAgent": DETECT_OUT,
         "AggregatorAgent": AGG_OUT, "TriggerPlannerAgent": PLAN_OUT,
         "UnifiedPrunerAgent": PRUNE_OUT, "FinalValidatorAgent": final_out("Yes")}
    s.update(override)
    return s


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        for name, text in PROMPTS.items():
            (Path(cls.tmp.name) / f"{name}.txt").write_text(text, encoding="utf-8")
        cls.prompts = PromptStore(cls.tmp.name)
        cls.sample = Sample(id="7", code="def f(cmd):\n    os.system(cmd)",
                            file_name="a.py", proj="{'repo': 'r'}", context="{'imports': []}")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_with(self, **override):
        backend = ScriptedBackend(script(**override))
        rec = analyse(self.sample, backend, self.prompts)
        ok, errs, _ = validate_prototype_output(rec)
        self.assertTrue(ok, errs)
        return rec, backend

    def test_vulnerable_path_and_trace(self):
        rec, backend = self.run_with()
        self.assertEqual(rec["decision"], "vulnerable")
        self.assertEqual(rec["pred"], 1)
        self.assertEqual(rec["cwe_suspected"], ["CWE-78"])
        self.assertIn("system(cmd)", rec["trigger_path"])
        self.assertEqual(rec["stage_counts"], {"detection_agents": 2, "candidates": 1, "retained": 1})
        self.assertEqual([t["agent"] for t in rec["trace"]],
                         ["MetaAgent", "AnalyzerAgent", "BehaviorAnalyzerAgent", "AggregatorAgent",
                          "TriggerPlannerAgent", "UnifiedPrunerAgent", "FinalValidatorAgent"])
        self.assertEqual(rec["cost"]["llm_calls"], 7)

    def test_all_issues_rejected_is_benign(self):
        rec, _ = self.run_with(FinalValidatorAgent=final_out("No"))
        self.assertEqual((rec["decision"], rec["pred"], rec["error"]), ("benign", 0, None))
        self.assertEqual(rec["stage_counts"]["retained"], 0)

    def test_no_candidates_is_benign_and_stops_early(self):
        rec, backend = self.run_with(AggregatorAgent='{"vulnerability_reported":false,"confirmed_issues":[]}')
        self.assertEqual((rec["decision"], rec["error"]), ("benign", None))
        self.assertNotIn("TriggerPlannerAgent", [a for a, _ in backend.calls])

    def test_llm_error_at_every_stage_is_unknown_not_benign(self):
        for stage in ("MetaAgent", "AnalyzerAgent", "AggregatorAgent", "TriggerPlannerAgent",
                      "UnifiedPrunerAgent", "FinalValidatorAgent"):
            with self.subTest(stage=stage):
                rec, _ = self.run_with(**{stage: LLMError("timeout")})
                self.assertEqual((rec["decision"], rec["pred"]), ("unknown", None))
                self.assertEqual(rec["error"]["stage"], stage)
                self.assertEqual(rec["error"]["kind"], "llm_error")

    def test_unparsable_output_is_unknown(self):
        for stage in ("AggregatorAgent", "FinalValidatorAgent"):
            with self.subTest(stage=stage):
                rec, _ = self.run_with(**{stage: "xin lỗi, tôi không trả JSON"})
                self.assertEqual(rec["decision"], "unknown")
                self.assertEqual(rec["error"], {**rec["error"], "stage": stage, "kind": "parse_error"})

    def test_missing_verdict_is_unknown(self):
        rec, _ = self.run_with(FinalValidatorAgent='{"reported_issues":[{"cwe":"CWE-78"}]}')
        self.assertEqual((rec["decision"], rec["error"]["kind"]), ("unknown", "schema_error"))

    def test_meta_garbage_falls_back_with_warning(self):
        rec, _ = self.run_with(MetaAgent="???")
        self.assertEqual(rec["active_agents"], ["AnalyzerAgent", "BehaviorAnalyzerAgent"])
        self.assertTrue(rec["warnings"])

    def test_meta_unknown_agent_is_skipped(self):
        rec, _ = self.run_with(MetaAgent='{"activated_agents":["AnalyzerAgent","BaseAgent","FinalValidatorAgent"]}')
        self.assertEqual(rec["active_agents"], ["AnalyzerAgent"])
        self.assertEqual(len(rec["warnings"]), 2)

    def test_label_never_reaches_prompts(self):
        record = {"idx": 7, "func": "int f(){return 0;}", "file_name": "a.c", "target": 1,
                  "cwe": ["CWE-LABEL-SECRET"], "cve": "CVE-LABEL-SECRET", "commit_message": "fix LABEL-SECRET"}
        sample = Sample.from_record(record)
        self.assertFalse(hasattr(sample, "target"))
        backend = ScriptedBackend(script())
        analyse(sample, backend, self.prompts)
        self.assertTrue(backend.calls)
        for _, prompt in backend.calls:
            self.assertNotIn("LABEL-SECRET", prompt)

    def test_upstream_quirk_swaps_proj_and_name(self):
        _, backend = self.run_with()
        pruner_prompt = dict(backend.calls)["UnifiedPrunerAgent"]
        self.assertIn("proj=a.py", pruner_prompt)            # giữ hành vi repo gốc
        backend2 = ScriptedBackend(script())
        analyse(self.sample, backend2, self.prompts, upstream_quirks=False)
        self.assertIn("name=a.py", dict(backend2.calls)["UnifiedPrunerAgent"])

    def test_ablation_skip_pruner_and_context(self):
        backend = ScriptedBackend(script())
        rec = analyse(self.sample, backend, self.prompts, skip=("pruner",))
        self.assertNotIn("UnifiedPrunerAgent", [a for a, _ in backend.calls])
        self.assertEqual(rec["decision"], "vulnerable")
        backend = ScriptedBackend(script())
        analyse(self.sample, backend, self.prompts, skip=("context",))
        self.assertIn("ctx={}", dict(backend.calls)["UnifiedPrunerAgent"])
        with self.assertRaises(ValueError):
            analyse(self.sample, ScriptedBackend(script()), self.prompts, skip=("validator",))

    def test_replay_backend(self):
        fixture = {
            "MetaAgent": META_OUT, "AnalyzerAgent": DETECT_OUT, "BehaviorAnalyzerAgent": DETECT_OUT,
            "AggregatorAgent": json.loads(AGG_OUT), "TriggerPlannerAgent": PLAN_OUT,
            "FinalValidatorAgent": {"vulnerability_reported": True, "per_issue_reports": [
                {"ProtectionAgent_output": PRUNE_OUT, "FinalValidatorAgent_raw": final_out("Yes")}]},
            "final_vulnerability_reported": True,
        }
        rec = analyse(self.sample, ReplayBackend(fixture), self.prompts)
        self.assertEqual(rec["decision"], "vulnerable")
        self.assertIsNone(rec["cost"]["prompt_tokens"])       # replay không đo token

        broken = dict(fixture, AnalyzerAgent=LLM_ERROR_SENTINEL)
        rec = analyse(self.sample, ReplayBackend(broken), self.prompts)
        self.assertEqual((rec["decision"], rec["error"]["stage"]), ("unknown", "AnalyzerAgent"))


COT_PROMPT_DIR = ROOT / "prompts_cot"


def cot_out(decision="vulnerable", cwe="CWE-78"):
    return ("Bước 1: cmd do caller truyền vào. Bước 2: dòng 2 gọi os.system(cmd) {không có guard}.\n"
            "```python\nos.system(cmd)\n```\n"
            "```json\n" + json.dumps({"decision": decision, "cwe": cwe,
                                      "reason": "dòng 2 đưa cmd chưa lọc vào os.system"}) + "\n```")


class CoTTest(unittest.TestCase):
    """Baseline CoT (PLAN §0.4 T2): 1 lời gọi/mẫu, JSON hỏng → unknown, không lộ nhãn."""

    @classmethod
    def setUpClass(cls):
        cls.prompts = PromptStore(COT_PROMPT_DIR)      # dùng đúng prompt sẽ chạy thật
        cls.sample = Sample(id="7", code="def f(cmd):\n    os.system(cmd)",
                            file_name="a.py", proj="{'repo': 'r'}", context="{'imports': ['os']}")

    def run_cot(self, out, **kw):
        backend = ScriptedBackend({"CoTAgent": out})
        rec = analyse_cot(self.sample, backend, self.prompts, **kw)
        ok, errs, _ = validate_prototype_output(rec)
        self.assertTrue(ok, errs)
        self.assertEqual(len(backend.calls), 1)           # đúng 1 lời gọi mỗi mẫu
        self.assertEqual(rec["cost"]["llm_calls"], 1)
        return rec, backend.calls[0][1]

    def test_prompt_has_code_and_context(self):
        _, prompt = self.run_cot(cot_out())
        self.assertIn("   2:     os.system(cmd)", prompt)
        self.assertIn("{'imports': ['os']}", prompt)
        self.assertNotIn("{function_code}", prompt)
        self.assertNotIn("{code_context}", prompt)

    def test_valid_vulnerable_and_benign(self):
        rec, _ = self.run_cot(cot_out())
        self.assertEqual((rec["decision"], rec["pred"], rec["error"]), ("vulnerable", 1, None))
        self.assertEqual(rec["cwe_suspected"], ["CWE-78"])
        self.assertIn("os.system", rec["evidence_or_guard"])
        self.assertEqual([t["agent"] for t in rec["trace"]], ["CoTAgent"])
        rec, _ = self.run_cot(cot_out("Benign", "None"))
        self.assertEqual((rec["decision"], rec["pred"], rec["cwe_suspected"]), ("benign", 0, []))

    def test_bare_json_after_reasoning_with_braces(self):
        out = 'int f() { if (n > 8) { return -1; } }\nKết luận: {"decision": "benign", "cwe": "None", "reason": "có kiểm tra n"}'
        rec, _ = self.run_cot(out)
        self.assertEqual(rec["decision"], "benign")

    def test_broken_output_is_unknown_not_benign(self):
        cases = {
            "parse_error": ["tôi nghĩ là an toàn", '```json\n{"decision": "benign", "cwe": \n```', ""],
            "schema_error": ['{"decision": "maybe", "reason": "?"}', '{"decision": null}'],
        }
        for kind, outs in cases.items():
            for out in outs:
                with self.subTest(out=out):
                    rec, _ = self.run_cot(out)
                    self.assertEqual((rec["decision"], rec["pred"]), ("unknown", None))
                    self.assertEqual((rec["error"]["stage"], rec["error"]["kind"]), ("CoTAgent", kind))

    def test_missing_decision_key_is_unknown(self):
        rec, _ = self.run_cot('{"cwe": "CWE-78", "reason": "x"}')
        self.assertEqual((rec["decision"], rec["error"]["kind"]), ("unknown", "parse_error"))

    def test_truncated_output_is_unknown(self):
        out = LLMResult(text=cot_out(), prompt_tokens=10, completion_tokens=10, stop_reason="max_tokens")
        rec, _ = self.run_cot(out)
        self.assertEqual((rec["decision"], rec["error"]["kind"]), ("unknown", "parse_error"))

    def test_llm_error_is_unknown(self):
        rec, _ = self.run_cot(LLMError("timeout"))
        self.assertEqual((rec["decision"], rec["error"]["kind"]), ("unknown", "llm_error"))

    def test_skip_context_and_invalid_skip(self):
        _, prompt = self.run_cot(cot_out(), skip=("context",))
        self.assertNotIn("['os']", prompt)
        self.assertIn("is available:\n{}\n", prompt)
        with self.assertRaises(ValueError):
            analyse_cot(self.sample, ScriptedBackend({"CoTAgent": cot_out()}), self.prompts, skip=("pruner",))

    def test_label_never_reaches_prompt(self):
        record = {"idx": 7, "func": "int f(){return 0;}", "file_name": "a.c", "target": 1,
                  "cwe": ["CWE-LABEL-SECRET"], "cve": "CVE-LABEL-SECRET", "commit_message": "fix LABEL-SECRET",
                  "context": "{}"}
        backend = ScriptedBackend({"CoTAgent": cot_out()})
        analyse_cot(Sample.from_record(record), backend, self.prompts)
        self.assertNotIn("LABEL-SECRET", backend.calls[0][1])

    def test_code_with_slot_text_is_not_substituted_twice(self):
        sample = Sample(id="8", code='char *s = "{code_context}";', context="CTX-MARKER")
        backend = ScriptedBackend({"CoTAgent": cot_out()})
        analyse_cot(sample, backend, self.prompts)
        prompt = backend.calls[0][1]
        self.assertIn('"{code_context}"', prompt)
        self.assertEqual(prompt.count("CTX-MARKER"), 1)


class HelperTest(unittest.TestCase):
    def test_parse_json(self):
        self.assertEqual(parse_json('{"a":1}'), {"a": 1})
        self.assertEqual(parse_json('```json\n{"a":1}\n```'), {"a": 1})
        self.assertEqual(parse_json('Kết quả: {"a":[1,2]} hết'), {"a": [1, 2]})
        self.assertEqual(parse_json('[1,2]'), [1, 2])
        self.assertIsNone(parse_json("ERROR: LLM call failed"))
        self.assertIsNone(parse_json(""))

    def test_number_code_renumbers(self):
        self.assertEqual(number_code("a\nb"), "   1: a\n   2: b")
        # Giữ đúng hành vi repo gốc: cắt tại dấu ':' đầu tiên nên còn một dấu cách thừa.
        self.assertEqual(number_code("  10: a\n  11: b"), "   1:  a\n   2:  b")


class MetricsUnknownTest(unittest.TestCase):
    def test_unknown_is_not_counted_as_benign(self):
        with tempfile.TemporaryDirectory() as d:
            pred = Path(d) / "predictions.jsonl"
            pred.write_text("\n".join(json.dumps(r) for r in [
                {"idx": 1, "decision": "vulnerable", "pred": 1},
                {"idx": 2, "decision": "benign", "pred": 0},
                {"idx": 3, "decision": "unknown", "pred": None},
                {"idx": 4, "decision": "benign", "pred": 0},
            ]), encoding="utf-8")
            preds, bad, dups, unknown = metrics.read_predictions_file(pred)
        self.assertEqual((preds, bad, dups, unknown), ({1: 1, 2: 0, 4: 0}, 0, [], [3]))
        gt = {1: 1, 2: 0, 3: 1, 4: 0}
        sm = metrics.sample_metrics(preds, gt)
        self.assertEqual((sm["TP"], sm["FP"], sm["FN"], sm["TN"]), (1, 0, 0, 2))   # idx 3 KHÔNG thành FN
        pairs, _ = metrics.build_pairs([1, 2, 3, 4], gt)
        pm = metrics.pair_metrics(pairs, preds, gt)
        self.assertEqual(pm["skip"]["pairs_missing"], 1)
        self.assertEqual(pm["skip"]["P_C"], 1)

    def test_selftest_still_passes(self):
        metrics.selftest()


if __name__ == "__main__":
    unittest.main()
