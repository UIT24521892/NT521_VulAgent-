#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_trace.py — In một trace của pipeline (results/raw/<lượt>/traces/<id>_L<dòng>.json)
ở dạng đọc được, để lần ngược từ kết luận về candidate → đường kích hoạt → lý do giữ/bác.

    python3 scripts/show_trace.py results/raw/<lượt>/traces/45_L45.json [file khác ...]
"""
import json
import sys
import textwrap


def wrap(label: str, text, width: int = 100) -> str:
    body = textwrap.fill(str(text), width=width, subsequent_indent=" " * 6)
    return f"    {label}: {body}"


def show(path: str) -> None:
    r = json.load(open(path, encoding="utf-8"))
    prov = r.get("provenance", {})
    print("=" * 100)
    print(f"Mẫu idx={r.get('idx')} (dòng {r.get('line')})  →  QUYẾT ĐỊNH: {r['decision'].upper()}")
    print(f"  Nguồn: backend={prov.get('backend')}"
          + (f", fixture={prov.get('fixture')}" if prov.get("fixture") else "")
          + (f", model={prov.get('model')}" if prov.get("model") else ""))
    c = r["stage_counts"]
    print(f"  Số lượng qua các bước: {c['detection_agents']} agent phát hiện → "
          f"{c['candidates']} candidate → {c['retained']} giả thuyết được giữ")
    print(f"  1) MetaAgent chọn: {', '.join(r['active_agents']) or '(không có)'}")
    print("  2-3) Candidate sau Aggregator:")
    for i, cand in enumerate(r["candidates"], 1):
        desc = cand.get("description")
        desc = desc[0] if isinstance(desc, list) and desc else desc
        print(f"    [{i}] {cand.get('cwe')} tại dòng {cand.get('code_line')}")
        print(wrap("mô tả", desc))
    print("  4-6) Phán quyết FinalValidator (sau TriggerPlanner và UnifiedPruner):")
    for i, it in enumerate(r["issues"], 1):
        print(f"    [{i}] {it.get('cwe')} → {it['verdict'].upper()}")
        if it.get("trigger_path"):
            print(wrap("đường kích hoạt", it["trigger_path"]))
        if it.get("reason"):
            print(wrap("lý do", it["reason"]))
    if r.get("error"):
        e = r["error"]
        print(f"  LỖI tại {e['stage']} ({e['kind']}): {e['message']}")
    for w in r.get("warnings", []):
        print(f"  cảnh báo: {w}")
    cost = r["cost"]
    print(f"  Chi phí: {cost['llm_calls']} lời gọi; {cost['prompt_chars']} ký tự prompt, "
          f"{cost['output_chars']} ký tự output; token đo được: "
          f"{'không' if cost['prompt_tokens'] is None else cost['prompt_tokens'] + cost['completion_tokens']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for p in sys.argv[1:]:
        show(p)
