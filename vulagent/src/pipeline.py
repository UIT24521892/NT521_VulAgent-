#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py — Pipeline VulAgent do nhóm viết lại (Giai đoạn B).

Luồng (theo `analyse()` của repo gốc, commit 065467c, và mô tả paper ACL):
  MetaAgent → các agent phát hiện → AggregatorAgent → TriggerPlannerAgent
  → UnifiedPrunerAgent (AssumptionPruner, có context) → FinalValidatorAgent → bản ghi JSON

Phần nhóm tự viết: điều phối, parse, luật quyết định, trace, bản ghi output.
Phần dùng lại: 15 prompt template của repo gốc, NẠP LÚC CHẠY từ `upstream/` (repo gốc
không có LICENSE nên không chép prompt vào repo nhóm).

Khác repo gốc (có chủ đích, phải khai báo khi báo cáo):
  1. Lỗi LLM hoặc output không parse được → `decision = "unknown"` kèm `error`,
     KHÔNG rơi về benign (source_audit §7.2).
  2. Nhãn thật không đi vào module này: `Sample` không có trường target/cwe.
  3. Mỗi lời gọi được ghi trace (agent, hash prompt, output) và đếm chi phí.
Giữ nguyên để tái hiện (bật bằng `upstream_quirks=True`): repo gốc gọi
`analyse(code, name, proj, context)` trong khi chữ ký là `(src_code, proj, name, context)`
nên `{proj}` nhận tên file còn `{name}` nhận chuỗi proj.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm import Backend, LLMError

SCHEMA_VERSION = "vulagent-nhom13/0.1"

META = "MetaAgent"
AGGREGATOR = "AggregatorAgent"
PLANNER = "TriggerPlannerAgent"
PRUNER = "UnifiedPrunerAgent"
VALIDATOR = "FinalValidatorAgent"
# Repo gốc dùng 2 agent này khi không parse được output MetaAgent.
META_FALLBACK = ["AnalyzerAgent", "BehaviorAnalyzerAgent"]
PIPELINE_STAGES = (META, AGGREGATOR, PLANNER, PRUNER, VALIDATOR)
V2_PRUNER_MAX_TOKENS = 8192
_TRUNCATED = {"length", "max_tokens"}
_REJECTION_BASES = {"necessary_condition_contradicted", "all_paths_guarded"}


# ───────────────────────── Dữ liệu vào ─────────────────────────
@dataclass
class Sample:
    """Một hàm cần phân tích. Cố ý KHÔNG có nhãn (target) hay CWE thật."""
    id: str
    code: str
    file_name: str = "name"
    proj: str = "{}"
    context: str = "{}"

    @classmethod
    def from_record(cls, rec: dict) -> "Sample":
        """Chỉ lấy các trường mà repo gốc đưa vào prompt; bỏ target/cwe/cve/commit_message."""
        return cls(
            id=str(rec["idx"]),
            code=rec["func"],
            file_name=rec.get("file_name", "name"),
            proj=str(rec.get("proj", {})),          # PrimeVul không có 'proj' → "{}" như repo gốc
            context=str(rec.get("context", {})),
        )


# ───────────────────────── Prompt ─────────────────────────
class PromptStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._cache: dict[str, str] = {}

    def has(self, agent: str) -> bool:
        return (self.root / f"{agent}.txt").is_file()

    def get(self, agent: str) -> str:
        if agent not in self._cache:
            self._cache[agent] = (self.root / f"{agent}.txt").read_text(encoding="utf-8")
        return self._cache[agent]

    def sha256_all(self) -> dict[str, str]:
        return {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.root.glob("*.txt"))}


# ───────────────────────── Parse ─────────────────────────
_FENCE = re.compile(r"```(?:json|[a-zA-Z]+)?\s*([\s\S]*?)\s*```", re.I)


def parse_json(text: str) -> Any:
    """Lấy JSON từ output model: thử nguyên văn, khối ```...```, rồi cắt từ ngoặc mở đầu
    tới ngoặc đóng cuối. Trả None nếu không được (KHÔNG trả {} — để bước gọi biết là lỗi)."""
    s = (text or "").strip()
    candidates = [s]
    m = _FENCE.search(s)
    if m:
        candidates.append(m.group(1).strip())
    starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
    end = max(s.rfind("}"), s.rfind("]"))
    if starts and end > min(starts):
        candidates.append(s[min(starts):end + 1])
    for c in candidates:
        try:
            return json.loads(c)
        except (json.JSONDecodeError, ValueError):
            continue
    return None


_LINE_PREFIX = re.compile(r"\s*\d+:\s")


def number_code(src: str) -> str:
    """Bỏ số dòng sẵn có (nếu có) rồi đánh lại số dòng, giống repo gốc."""
    clean = "\n".join(l.split(":", 1)[-1] if _LINE_PREFIX.match(l) else l
                      for l in src.splitlines()).rstrip("\n")
    return "\n".join(f"{i:>4d}: {l}" for i, l in enumerate(clean.splitlines(), 1))


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ───────────────────────── Chạy một mẫu ─────────────────────────
@dataclass
class _Run:
    backend: Backend
    trace: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    calls: int = 0
    prompt_chars: int = 0
    output_chars: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tokens_measured: bool = True
    latency_s: float = 0.0

    def call(self, agent: str, prompt: str, *, max_tokens: int | None = None) -> str:
        self.calls += 1
        self.prompt_chars += len(prompt)
        entry = {"agent": agent, "prompt_sha256": _sha(prompt), "prompt_chars": len(prompt)}
        self.trace.append(entry)
        try:
            res = (self.backend.complete(agent, prompt, max_tokens=max_tokens)
                   if max_tokens is not None else self.backend.complete(agent, prompt))
        except LLMError as e:
            entry["error"] = str(e)
            entry["stop_reason"] = e.stop_reason
            raise
        entry["output"] = res.text
        entry["stop_reason"] = res.stop_reason
        self.output_chars += len(res.text)
        self.latency_s += res.latency_s
        if res.prompt_tokens is None or res.completion_tokens is None:
            self.tokens_measured = False
        else:
            self.prompt_tokens += res.prompt_tokens
            self.completion_tokens += res.completion_tokens
        return res.text

    def cost(self) -> dict:
        return {
            "llm_calls": self.calls,
            "prompt_chars": self.prompt_chars,
            "output_chars": self.output_chars,
            "prompt_tokens": self.prompt_tokens if self.tokens_measured else None,
            "completion_tokens": self.completion_tokens if self.tokens_measured else None,
            "latency_s": round(self.latency_s, 3),
        }


class _Stop(Exception):
    """Dừng pipeline với quyết định unknown."""
    def __init__(self, stage: str, kind: str, message: str):
        self.info = {"stage": stage, "kind": kind, "message": message}


def _issues_of(obj: Any) -> list | None:
    """Danh sách issue trong output agent; None nếu output sai cấu trúc."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        lists = [obj[k] for k in ("confirmed_issues", "reported_issues") if isinstance(obj.get(k), list)]
        if lists:
            return next((l for l in lists if l), [])   # ưu tiên danh sách không rỗng, như repo gốc
    return None


def _new_record(sample: Sample) -> dict:
    return {
        "schema_version": SCHEMA_VERSION, "id": sample.id,
        "decision": "unknown", "cwe_suspected": [], "sink": None,
        "hypothesis_condition": None, "trigger_path": None, "evidence_or_guard": None,
        "active_agents": [], "candidates": [], "issues": [],
        "stage_counts": {"detection_agents": 0, "candidates": 0, "retained": 0},
        "error": None,
    }


def analyse(sample: Sample, backend: Backend, prompts: PromptStore,
            upstream_quirks: bool = True, skip: tuple = ()) -> dict:
    """Chạy pipeline cho một mẫu. Luôn trả bản ghi (không ném lỗi LLM ra ngoài).

    `skip`: bỏ một thành phần cho ablation — "pruner" (bỏ UnifiedPruner, báo cáo của
    TriggerPlanner đi thẳng vào FinalValidator) hoặc "context" (đưa context rỗng).
    """
    unknown_skip = set(skip) - {"pruner", "context"}
    if unknown_skip:
        raise ValueError(f"skip không hỗ trợ: {sorted(unknown_skip)}")

    run = _Run(backend)
    code = number_code(sample.code)
    proj_slot, name_slot = ((sample.file_name, sample.proj) if upstream_quirks
                            else (sample.proj, sample.file_name))
    context = "{}" if "context" in skip else sample.context

    rec = _new_record(sample)

    def step(stage: str, prompt: str) -> str:
        try:
            return run.call(stage, prompt)
        except LLMError as e:
            raise _Stop(stage, "llm_error", str(e))

    try:
        # 1) MetaAgent chọn agent phát hiện
        meta = parse_json(step(META, prompts.get(META).replace("{function_code}", code)))
        agents = meta.get("activated_agents") if isinstance(meta, dict) else None
        if not isinstance(agents, list) or not agents:
            run.warnings.append("MetaAgent: không đọc được activated_agents → dùng bộ mặc định của repo gốc")
            agents = META_FALLBACK
        agents = list(dict.fromkeys(a for a in agents if isinstance(a, str)))
        for a in [a for a in agents if a in PIPELINE_STAGES or not prompts.has(a)]:
            run.warnings.append(f"MetaAgent chọn '{a}' không phải agent phát hiện hợp lệ → bỏ qua")
            agents.remove(a)
        if not agents:
            raise _Stop(META, "schema_error", "không còn agent phát hiện hợp lệ nào")
        rec["active_agents"] = agents
        rec["stage_counts"]["detection_agents"] = len(agents)

        # 2) Agent phát hiện (ưu tiên không bỏ sót; lọc ở các bước sau)
        outputs = {a: step(a, prompts.get(a).replace("{function_code}", code)) for a in agents}
        payload = {}
        for a, raw in outputs.items():
            parsed = parse_json(raw)
            payload[a] = {"raw": raw, "parsed": parsed if isinstance(parsed, (dict, list)) else None}

        # 3) Aggregator gộp candidate
        agg_raw = step(AGGREGATOR, prompts.get(AGGREGATOR)
                       .replace("{function_code}", code)
                       .replace("{all_agent_outputs}",
                                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))))
        candidates = _issues_of(parse_json(agg_raw))
        if candidates is None:
            raise _Stop(AGGREGATOR, "parse_error", "output không có danh sách confirmed_issues")
        rec["candidates"] = candidates
        rec["stage_counts"]["candidates"] = len(candidates)
        if not candidates:
            # Model kết luận không có candidate: đây là benign thật, không phải lỗi.
            rec["decision"] = "benign"
            rec["evidence_or_guard"] = "Aggregator không giữ candidate nào"
            return _finish(rec, run)

        # 4) TriggerPlanner lập giả thuyết + đường kích hoạt (chuyển nguyên văn)
        report = step(PLANNER, prompts.get(PLANNER)
                      .replace("{function_code}", code)
                      .replace("{report_text}",
                               json.dumps({"confirmed_issues": candidates}, ensure_ascii=False,
                                          sort_keys=True, separators=(",", ":")))).strip()

        # 5) UnifiedPruner kiểm giả định bằng context
        if "pruner" not in skip:
            report = step(PRUNER, prompts.get(PRUNER)
                          .replace("{function_code}", code)
                          .replace("{proj}", proj_slot).replace("{name}", name_slot)
                          .replace("{report_text}", report)
                          .replace("{code_context}", context)).strip()

        # 6) FinalValidator quyết định từng issue
        final_raw = step(VALIDATOR, prompts.get(VALIDATOR)
                         .replace("{function_code}", code)
                         .replace("{proj}", proj_slot)
                         .replace("{full_report_text}", report))
        issues = _issues_of(parse_json(final_raw))
        if issues is None:
            raise _Stop(VALIDATOR, "parse_error", "output không có confirmed_issues/reported_issues")

        valid, undecided = [], 0
        for it in issues:
            if not isinstance(it, dict):
                undecided += 1
                continue
            verdict = str(it.get("Is it valid?", "")).strip().lower()
            verdict = verdict if verdict in ("yes", "no") else "undecided"
            undecided += verdict == "undecided"
            entry = {"cwe": it.get("cwe"), "verdict": verdict, "code_line": it.get("code_line"),
                     "trigger_path": it.get("trigger_path"), "reason": it.get("Reason for judgment")}
            rec["issues"].append(entry)
            if verdict == "yes":
                valid.append(entry)
        rec["stage_counts"]["retained"] = len(valid)

        if valid:
            rec["decision"] = "vulnerable"
            rec["cwe_suspected"] = [v["cwe"] for v in valid if v["cwe"]]
            rec["sink"] = "; ".join(f"{v['cwe']} @ dòng {v['code_line']}" for v in valid if v["code_line"]) or None
            rec["trigger_path"] = " | ".join(v["trigger_path"] for v in valid if v["trigger_path"]) or None
            rec["hypothesis_condition"] = rec["trigger_path"]
            rec["evidence_or_guard"] = " | ".join(v["reason"] for v in valid if v["reason"]) or None
        elif undecided:
            raise _Stop(VALIDATOR, "schema_error",
                        f"{undecided} issue thiếu phán quyết Yes/No và không issue nào được giữ")
        else:
            rec["decision"] = "benign"
            rec["evidence_or_guard"] = " | ".join(i["reason"] for i in rec["issues"] if i["reason"]) or \
                                       "FinalValidator bác bỏ mọi candidate"
    except _Stop as stop:
        rec["decision"] = "unknown"
        rec["error"] = stop.info
    return _finish(rec, run)


def _assessments(raw: str) -> list | None:
    obj = parse_json(raw)
    if isinstance(obj, dict) and isinstance(obj.get("assessments"), list):
        return obj["assessments"]
    return None


def _has_line_evidence(evidence: Any, source_lines: list[str]) -> bool:
    if not isinstance(evidence, dict):
        return False
    line, quote = evidence.get("line"), evidence.get("quote")
    return (type(line) is int and 1 <= line <= len(source_lines)
            and isinstance(quote, str) and bool(quote.strip())
            and quote.strip() == source_lines[line - 1].strip())


def verify_candidates(sample: Sample, backend: Backend, prompts: PromptStore,
                      candidates: list[dict]) -> dict:
    """Kiểm chứng tĩnh v2 trên danh sách candidate cố định từ lượt đối chứng."""
    run = _Run(backend)
    rec = _new_record(sample)
    refs = [{"issue_id": i, "cwe": issue.get("cwe"), "code_line": issue.get("code_line")}
            for i, issue in enumerate(candidates, 1)]
    rec["candidates"] = refs
    rec["stage_counts"]["candidates"] = len(refs)
    if not refs:
        rec["decision"] = "benign"
        rec["evidence_or_guard"] = "Aggregator không giữ candidate nào"
        return _finish(rec, run)

    code = number_code(sample.code)
    source_lines = [line.partition(": ")[2] for line in code.split("\n")]
    ref_text = json.dumps(refs, ensure_ascii=False)
    stage = PRUNER
    try:
        # Thay placeholder một lượt để giữ nguyên dữ liệu có dấu ngoặc nhọn.
        prune_prompt = prompts.get(PRUNER).format(
            function_code=code, candidates=ref_text, code_context=sample.context)
        prune_raw = run.call(PRUNER, prune_prompt, max_tokens=V2_PRUNER_MAX_TOKENS)
        annotations = _assessments(prune_raw)
        if annotations is None or run.trace[-1]["stop_reason"] in _TRUNCATED:
            run.warnings.append(f"{PRUNER}: thiếu annotation đầy đủ, giữ toàn bộ candidate")
            annotations = []

        stage = VALIDATOR
        final_prompt = prompts.get(VALIDATOR).format(
            function_code=code, candidates=ref_text,
            annotations=json.dumps(annotations, ensure_ascii=False))
        final_raw = run.call(VALIDATOR, final_prompt)
        judgments = _assessments(final_raw)
        if judgments is None or run.trace[-1]["stop_reason"] in _TRUNCATED:
            raise _Stop(VALIDATOR, "parse_error", "output kiểm chứng thiếu assessments đầy đủ")

        by_id = {}
        duplicate_ids = set()
        for item in judgments:
            issue_id = item.get("issue_id") if isinstance(item, dict) else None
            if type(issue_id) is int:
                if issue_id in by_id:
                    duplicate_ids.add(issue_id)
                by_id[issue_id] = item

        kept, undecided = [], 0
        for ref in refs:
            issue_id = ref["issue_id"]
            item = by_id.get(issue_id, {}) if issue_id not in duplicate_ids else {}
            verdict, reason = item.get("verdict"), item.get("reason")
            evidence, basis = item.get("evidence"), item.get("rejection_basis")
            reason = reason.strip() if isinstance(reason, str) else ""
            if verdict == "reject" and not (isinstance(basis, str) and basis in _REJECTION_BASES
                                           and reason and _has_line_evidence(evidence, source_lines)):
                verdict = "keep"
                reason = "Thiếu bằng chứng mã nguồn để bác candidate"
            if verdict not in ("keep", "reject"):
                verdict = "undecided"
                undecided += 1
            entry = {**ref, "verdict": {"keep": "yes", "reject": "no"}.get(verdict, verdict),
                     "reason": reason, "trigger_path": None,
                     "rejection_basis": basis if verdict == "reject" else None,
                     "evidence": evidence if verdict == "reject" else None}
            rec["issues"].append(entry)
            if verdict == "keep":
                kept.append(entry)

        rec["stage_counts"]["retained"] = len(kept)
        if kept:
            rec["decision"] = "vulnerable"
            rec["cwe_suspected"] = [item["cwe"] for item in kept if item["cwe"]]
            rec["sink"] = " | ".join(f"{item['cwe']} @ dòng {item['code_line']}"
                                     for item in kept if item["code_line"]) or None
        elif undecided:
            raise _Stop(VALIDATOR, "schema_error", f"{undecided} issue thiếu phán quyết duy nhất")
        else:
            rec["decision"] = "benign"
        rec["evidence_or_guard"] = " | ".join(item["reason"] for item in (kept or rec["issues"])
                                              if item["reason"]) or None
    except LLMError as error:
        rec["error"] = {"stage": stage, "kind": "llm_error", "message": str(error)}
    except _Stop as stop:
        rec["error"] = stop.info
    return _finish(rec, run)


def _finish(rec: dict, run: _Run) -> dict:
    rec["pred"] = {"vulnerable": 1, "benign": 0}.get(rec["decision"])
    rec["warnings"] = run.warnings
    rec["cost"] = run.cost()
    rec["trace"] = run.trace
    return rec
