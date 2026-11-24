#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_errors.py — Phân loại mẫu theo khâu quyết định số phận của nó, đọc từ trace.

    python3 scripts/analyze_errors.py --gt <file.jsonl> --run results/raw/<lượt> \
        [--out results/tables/<lượt>.errors]   # ghi <tiền tố>.json

Không gọi model. Cần nhãn (`target`, `cwe`) nên chỉ chạy SAU khi đã có dự đoán.
Với mỗi mẫu vulnerable bị đoán benign (FN), xếp vào đúng một nhóm theo thứ tự:
  0  Aggregator không giữ candidate nào
  1  có candidate nhưng không candidate nào mang CWE của nhãn
  2  UnifiedPruner trả danh sách không còn issue mang CWE của nhãn
  3  UnifiedPruner đánh dấu ít nhất một giả định của issue đó là "contradicted"
  4  output UnifiedPruner không parse được (đa số bị cắt giữa chừng)
  5  UnifiedPruner không bác giả định nào, FinalValidator tự bác
So khớp CWE theo số (CWE-089 ≡ CWE-89). Nhóm 1 chỉ nói "lệch CWE", không khẳng định
candidate đó sai về bản chất.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from pipeline import parse_json  # noqa: E402

GROUPS = {
    0: "Aggregator không giữ candidate nào",
    1: "có candidate nhưng lệch CWE so với nhãn",
    2: "UnifiedPruner xóa issue đúng CWE khỏi danh sách",
    3: "UnifiedPruner đánh dấu contradicted → FinalValidator bác",
    4: "output UnifiedPruner không parse được → FinalValidator bác",
    5: "UnifiedPruner không bác, FinalValidator tự bác",
}


def cwe_num(x):
    m = re.search(r"(\d+)", str(x))
    return int(m.group(1)) if m else None


def pruner_issues(trace):
    """(issues | None nếu không parse được | 'absent' nếu không có lời gọi Pruner)."""
    outs = [s["output"] for s in trace if s["agent"] == "UnifiedPrunerAgent"]
    if not outs:
        return "absent", None
    parsed = parse_json(outs[0])
    if not isinstance(parsed, dict):
        return None, outs[0]
    items = parsed.get("confirmed_issues") or parsed.get("reported_issues") or []
    return [i for i in items if isinstance(i, dict)], outs[0]


def contradicted(issue):
    return any(isinstance(a, dict) and str(a.get("status", "")).lower() == "contradicted"
               for a in issue.get("assumptions_checked") or [])


def fn_group(rec, true_cwe):
    if not rec["stage_counts"]["candidates"]:
        return 0
    if true_cwe not in [cwe_num(c.get("cwe")) for c in rec["candidates"] if isinstance(c, dict)]:
        return 1
    issues, _ = pruner_issues(rec["trace"])
    if issues is None:
        return 4
    if issues == "absent":
        return 5
    same = [i for i in issues if cwe_num(i.get("cwe")) == true_cwe]
    if not same:
        return 2
    return 3 if any(contradicted(i) for i in same) else 5


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gt", type=Path, required=True)
    ap.add_argument("--run", type=Path, required=True, help="Thư mục lượt chạy (có traces/)")
    ap.add_argument("--out", help="Tiền tố file .json kết quả")
    args = ap.parse_args()

    gt = {}
    for raw in args.gt.open(encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(raw)
        except json.JSONDecodeError:
            continue
        gt[int(o["idx"])] = (int(o["target"]), cwe_num(o.get("cwe")))

    confusion, fn_groups = Counter(), defaultdict(list)
    pruner_calls = pruner_unparsed = pruner_cut = 0
    issue_table = Counter()
    for path in sorted((args.run / "traces").glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        idx = int(rec["idx"])
        if idx not in gt or rec["pred"] is None:
            continue
        target, true_cwe = gt[idx]
        kind = {(1, 1): "TP", (0, 1): "FP", (1, 0): "FN", (0, 0): "TN"}[(target, rec["pred"])]
        confusion[kind] += 1
        issues, raw = pruner_issues(rec["trace"])
        if issues != "absent":
            pruner_calls += 1
            if issues is None:
                pruner_unparsed += 1
                pruner_cut += not raw.rstrip().endswith(("}", "```"))
            else:
                for final, pi in zip(rec["issues"], issues):
                    issue_table[("contradicted" if contradicted(pi) else "không bác", final["verdict"])] += 1
        if kind == "FN":
            fn_groups[fn_group(rec, true_cwe)].append(idx)

    result = {
        "run": str(args.run), "confusion": dict(confusion),
        "fn_groups": {f"{k}. {GROUPS[k]}": sorted(v) for k, v in sorted(fn_groups.items())},
        "pruner_output": {"calls": pruner_calls, "unparseable": pruner_unparsed,
                          "unparseable_ending_mid_text": pruner_cut},
        "issue_pruner_vs_final": {f"Pruner {a} / Validator {b}": n for (a, b), n in sorted(issue_table.items())},
    }
    print(f"Confusion: {dict(confusion)}")
    print("FN theo khâu:")
    for k, v in sorted(fn_groups.items()):
        print(f"  {k}. {GROUPS[k]}: {len(v)}  idx={sorted(v)}")
    print(f"Output UnifiedPruner: {pruner_calls} lời gọi, {pruner_unparsed} không parse được "
          f"({pruner_cut} kết thúc giữa chừng)")
    print("Issue: phán quyết Pruner so với FinalValidator (chỉ mẫu parse được, ghép theo thứ tự):")
    for k, n in result["issue_pruner_vs_final"].items():
        print(f"  {k}: {n}")
    if args.out:
        p = Path(str(args.out) + ".json")   # không dùng with_suffix: tiền tố có thể chứa dấu chấm
        p.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Đã ghi: {p}")


if __name__ == "__main__":
    main()
