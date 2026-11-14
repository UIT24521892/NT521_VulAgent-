#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schema.py — Validate JSON đầu ra VulAgent (Giai đoạn C0.3).

Hai mục tiêu:

A) validate_repo_output(d): kiểm cấu trúc file `*_full.json` mà pipeline GỐC xuất ra
   (dùng để parse 3752 fixture trong upstream một cách an toàn + PHÁT HIỆN rủi ro
   "lỗi LLM → benign" đã nêu ở C0.1: quét chuỗi sentinel "ERROR: LLM call failed"
   ở mọi nơi trong cây JSON; nếu có mà kết luận lại là benign ⇒ cảnh báo).

B) validate_prototype_output(d): kiểm SCHEMA ĐÍCH mà pipeline của NHÓM phải phát ra
   (theo PLAN §2). Khác repo ở chỗ BẮT BUỘC có trạng thái `unknown` khi thiếu dữ liệu
   / lỗi LLM — để lỗi hạ tầng KHÔNG bị âm thầm quy thành `benign`.

Chỉ dùng thư viện chuẩn. Tự kiểm: `python3 schema.py --selftest`.
Quét thư mục fixture repo: `python3 schema.py <dir> --repo`
Kiểm 1 file prototype: `python3 schema.py <file.json> --prototype`

Nguồn phát hiện: docs/source_audit.md §7 (C0.1) và reproduction_plan.md (C0.3).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Any

# Sentinel mà call_llm() của repo trả về khi một lời gọi LLM thất bại (dòng 110
# VulAgent-Qwen.py). Nếu xuất hiện trong output nghĩa là đã có lỗi hạ tầng.
LLM_ERROR_SENTINEL = "ERROR: LLM call failed"

# Quyết định hợp lệ của schema ĐÍCH (nhóm). `unknown` là bắt buộc để tách lỗi/thiếu
# dữ liệu khỏi `benign`.
VALID_DECISIONS = ("vulnerable", "benign", "unknown")


# ───────────────────────── Tiện ích ─────────────────────────
def _walk_strings(obj: Any):
    """Duyệt đệ quy mọi chuỗi trong một cây JSON (dict/list/str)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def has_llm_error(obj: Any) -> bool:
    """True nếu bất kỳ chuỗi nào trong cây chứa sentinel lỗi LLM."""
    return any(LLM_ERROR_SENTINEL in s for s in _walk_strings(obj))


# ───────────────────── A) Schema output REPO ─────────────────────
def validate_repo_output(d: Any) -> tuple[bool, list[str], list[str]]:
    """
    Kiểm cấu trúc `*_full.json` của pipeline gốc.
    Trả về (ok, errors, warnings). `ok` chỉ phản ánh LỖI CẤU TRÚC;
    cảnh báo (vd benign-do-lỗi) KHÔNG làm ok=False nhưng phải được báo cáo.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(d, dict):
        return False, [f"top-level không phải object (là {type(d).__name__})"], []

    # Trường bắt buộc
    if "final_vulnerability_reported" not in d:
        errors.append("thiếu 'final_vulnerability_reported'")
    elif not isinstance(d["final_vulnerability_reported"], bool):
        errors.append("'final_vulnerability_reported' phải là bool")

    # MetaAgent + active_agents
    if "active_agents" in d:
        aa = d["active_agents"]
        if not isinstance(aa, list) or not all(isinstance(x, str) for x in aa):
            errors.append("'active_agents' phải là list[str]")
        else:
            # mỗi agent được kích hoạt nên có khóa output tương ứng
            for ag in aa:
                if ag not in d:
                    warnings.append(f"active_agent '{ag}' không có khóa output tương ứng")
    else:
        warnings.append("thiếu 'active_agents' (có thể do early-return)")

    # FinalValidatorAgent: dict có ít nhất 'vulnerability_reported'
    fv = d.get("FinalValidatorAgent")
    if fv is None:
        errors.append("thiếu 'FinalValidatorAgent'")
    elif not isinstance(fv, dict):
        errors.append("'FinalValidatorAgent' phải là object")
    else:
        if "vulnerability_reported" not in fv:
            errors.append("'FinalValidatorAgent.vulnerability_reported' thiếu")
        elif not isinstance(fv["vulnerability_reported"], bool):
            errors.append("'FinalValidatorAgent.vulnerability_reported' phải là bool")
        # Nhất quán cờ cuối với FinalValidator
        if (isinstance(fv.get("vulnerability_reported"), bool)
                and isinstance(d.get("final_vulnerability_reported"), bool)
                and fv["vulnerability_reported"] != d["final_vulnerability_reported"]):
            warnings.append("final_vulnerability_reported KHÁC FinalValidatorAgent.vulnerability_reported")

    # 🔴 Phát hiện rủi ro C0.1: lỗi LLM → benign
    if has_llm_error(d):
        if d.get("final_vulnerability_reported") is False:
            warnings.append(
                "BENIGN-DO-LỖI: có 'ERROR: LLM call failed' trong output NHƯNG "
                "final_vulnerability_reported=False → quyết định benign có thể do lỗi "
                "hạ tầng, KHÔNG phải model kết luận an toàn (rủi ro C0.1)."
            )
        else:
            warnings.append("có sentinel lỗi LLM trong output (nhưng kết luận vuln=True)")

    return (len(errors) == 0), errors, warnings


# ─────────────────── B) Schema ĐÍCH (prototype nhóm) ───────────────────
# Mẫu bản ghi đích (tối thiểu). `decision` thay cho cờ bool để có `unknown`.
PROTOTYPE_REQUIRED = ("id", "decision")
PROTOTYPE_OPTIONAL = (
    "sink", "cwe_suspected", "hypothesis_condition",
    "trigger_path", "evidence_or_guard", "error",
)


def validate_prototype_output(d: Any) -> tuple[bool, list[str], list[str]]:
    """
    Kiểm bản ghi output của pipeline NHÓM (PLAN §2).
    Quy tắc then chốt (sửa rủi ro C0.1):
      - `decision` ∈ {vulnerable, benign, unknown} (bắt buộc).
      - Nếu `error` khác rỗng ⇒ `decision` PHẢI là 'unknown' (KHÔNG được 'benign').
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(d, dict):
        return False, [f"top-level không phải object (là {type(d).__name__})"], []

    for k in PROTOTYPE_REQUIRED:
        if k not in d:
            errors.append(f"thiếu trường bắt buộc '{k}'")

    if not isinstance(d.get("id", ""), str) or not str(d.get("id", "")).strip():
        errors.append("'id' phải là chuỗi không rỗng (định danh ổn định)")

    dec = d.get("decision")
    if dec is not None and dec not in VALID_DECISIONS:
        errors.append(f"'decision'='{dec}' không hợp lệ; phải thuộc {VALID_DECISIONS}")

    # Quy tắc trung thực: lỗi/thiếu dữ liệu → unknown, không phải benign
    err = d.get("error")
    if err not in (None, "", []):
        if dec != "unknown":
            errors.append(
                f"có 'error' nhưng decision='{dec}' (phải 'unknown'): "
                "lỗi/thiếu dữ liệu KHÔNG được quy thành benign (rủi ro C0.1)."
            )

    # cwe_suspected nên là list/str
    cw = d.get("cwe_suspected")
    if cw is not None and not isinstance(cw, (list, str)):
        warnings.append("'cwe_suspected' nên là list[str] hoặc str")

    # Khi decision=vulnerable, nên có đủ dấu vết suy luận (khuyến nghị, không bắt buộc)
    if dec == "vulnerable":
        for k in ("sink", "hypothesis_condition", "trigger_path"):
            if not d.get(k):
                warnings.append(f"decision=vulnerable nhưng thiếu '{k}' (khó lần ngược suy luận)")

    return (len(errors) == 0), errors, warnings


# ───────────────────────── Quét thư mục ─────────────────────────
def scan_dir(path: str, mode: str) -> dict:
    """Quét mọi *_full.json (repo) hoặc *.json (prototype) dưới `path`."""
    validate = validate_repo_output if mode == "repo" else validate_prototype_output
    pattern_ok = (lambda n: n.endswith("_full.json")) if mode == "repo" else (lambda n: n.endswith(".json"))
    total = passed = 0
    with_errors: list[str] = []
    benign_by_error: list[str] = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if not pattern_ok(name):
                continue
            fp = os.path.join(root, name)
            total += 1
            try:
                d = json.load(open(fp, encoding="utf-8"))
            except Exception as e:
                with_errors.append(f"{fp}: không parse được JSON ({e})")
                continue
            ok, errs, warns = validate(d)
            if ok:
                passed += 1
            else:
                with_errors.append(f"{fp}: " + "; ".join(errs))
            if any("BENIGN-DO-LỖI" in w for w in warns):
                benign_by_error.append(fp)
    return {
        "total": total, "passed": passed,
        "schema_errors": with_errors, "benign_by_error": benign_by_error,
    }


# ───────────────────────── Self-test ─────────────────────────
def _selftest() -> int:
    fails = 0

    def check(name, cond):
        nonlocal fails
        if not cond:
            fails += 1
            print(f"  ✗ {name}")
        else:
            print(f"  ✓ {name}")

    # Repo schema: bản hợp lệ
    good = {
        "MetaAgent": "{}", "active_agents": ["AnalyzerAgent"],
        "AnalyzerAgent": "{}", "AggregatorAgent": {"vulnerability_reported": True, "confirmed_issues": []},
        "TriggerPlannerAgent": "report",
        "FinalValidatorAgent": {"vulnerability_reported": True, "per_issue_reports": [], "cwe_list": ["CWE-22"]},
        "final_vulnerability_reported": True,
    }
    ok, errs, warns = validate_repo_output(good)
    check("repo: bản hợp lệ → ok", ok and not errs)

    # Repo schema: thiếu cờ cuối → lỗi
    bad = dict(good); del bad["final_vulnerability_reported"]
    ok, errs, warns = validate_repo_output(bad)
    check("repo: thiếu final_vulnerability_reported → not ok", not ok)

    # Repo schema: lỗi LLM + benign → cảnh báo benign-do-lỗi
    err_case = {
        "active_agents": ["AnalyzerAgent"], "AnalyzerAgent": "ERROR: LLM call failed",
        "AggregatorAgent": {}, "FinalValidatorAgent": {"vulnerability_reported": False},
        "final_vulnerability_reported": False,
    }
    ok, errs, warns = validate_repo_output(err_case)
    check("repo: lỗi LLM + benign → cảnh báo BENIGN-DO-LỖI",
          any("BENIGN-DO-LỖI" in w for w in warns))

    # Prototype: bản hợp lệ
    proto_ok = {"id": "x1", "decision": "vulnerable", "sink": "system()",
                "hypothesis_condition": "input→sink", "trigger_path": "a→b",
                "cwe_suspected": ["CWE-78"], "error": None}
    ok, errs, warns = validate_prototype_output(proto_ok)
    check("prototype: bản hợp lệ → ok", ok and not errs)

    # Prototype: có error nhưng decision=benign → LỖI (đúng quy tắc C0.1)
    proto_bad = {"id": "x2", "decision": "benign", "error": "LLM timeout"}
    ok, errs, warns = validate_prototype_output(proto_bad)
    check("prototype: error+benign → not ok (phải unknown)", not ok)

    # Prototype: error + unknown → hợp lệ
    proto_unk = {"id": "x3", "decision": "unknown", "error": "LLM timeout"}
    ok, errs, warns = validate_prototype_output(proto_unk)
    check("prototype: error+unknown → ok", ok)

    # Prototype: decision lạ → lỗi
    ok, errs, warns = validate_prototype_output({"id": "x4", "decision": "maybe"})
    check("prototype: decision không hợp lệ → not ok", not ok)

    print("✅ self-test PASS" if fails == 0 else f"❌ self-test FAIL ({fails} lỗi)")
    return 1 if fails else 0


# ───────────────────────── CLI ─────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Validate JSON output VulAgent (C0.3).")
    ap.add_argument("path", nargs="?", help="file .json hoặc thư mục fixture")
    ap.add_argument("--repo", action="store_true", help="dùng schema output repo (mặc định cho thư mục)")
    ap.add_argument("--prototype", action="store_true", help="dùng schema đích của nhóm")
    ap.add_argument("--selftest", action="store_true", help="chạy self-test nội bộ")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.path:
        ap.print_help()
        return 2

    mode = "prototype" if args.prototype else "repo"

    if os.path.isdir(args.path):
        res = scan_dir(args.path, mode)
        print(f"Quét ({mode}): {res['passed']}/{res['total']} file đạt schema.")
        if res["schema_errors"]:
            print(f"  Lỗi schema: {len(res['schema_errors'])} file (hiện 10 đầu):")
            for line in res["schema_errors"][:10]:
                print("   -", line)
        if res["benign_by_error"]:
            print(f"  🔴 BENIGN-DO-LỖI (lỗi LLM → benign): {len(res['benign_by_error'])} file:")
            for fp in res["benign_by_error"][:10]:
                print("   -", fp)
        return 0

    # file đơn
    d = json.load(open(args.path, encoding="utf-8"))
    validate = validate_repo_output if mode == "repo" else validate_prototype_output
    ok, errs, warns = validate(d)
    print(f"[{mode}] {args.path}: {'ĐẠT' if ok else 'KHÔNG ĐẠT'}")
    for e in errs:
        print("  LỖI:", e)
    for w in warns:
        print("  cảnh báo:", w)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
