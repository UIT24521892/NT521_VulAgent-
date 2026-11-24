#!/usr/bin/env python3
"""Chấm pilot hoặc lượt SEVEN v2 đã lưu, không gọi API."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from metrics import build_pairs, pair_metrics, read_ground_truth, sample_metrics

PILOT_IDS = Path(__file__).resolve().parent.parent / "configs" / "seven_verification_v2_pilot_ids.txt"


def read_rows(raw: bytes) -> dict:
    rows = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        idx = int(row["idx"])
        if idx in rows or row["pred"] not in (0, 1, None):
            raise ValueError(f"idx={idx} trùng hoặc pred ngoài schema")
        rows[idx] = row
    return rows


def summarize(gt: dict, pairs: list, rows: dict, known_ids: set) -> dict:
    preds = {idx: rows[idx]["pred"] for idx in known_ids}
    return {
        "sample": sample_metrics(preds, gt),
        "pair": pair_metrics(pairs, preds, gt)["skip"],
        "fn_with_candidate_rejected": sum(
            gt[idx] == 1 and preds[idx] == 0 and rows[idx]["stage_counts"]["candidates"] > 0
            for idx in known_ids
        ),
    }


def pilot_diagnostics(gt: dict, pairs: list, baseline: dict, new: dict, known: set) -> dict:
    original = {idx: baseline[idx]["pred"] for idx in known}
    v2 = {idx: new[idx]["pred"] for idx in known}
    keep_all = {idx: int(baseline[idx]["stage_counts"]["candidates"] > 0) for idx in known}
    differs = sorted(idx for idx in known if keep_all[idx] != v2[idx])
    return {
        "keep_all_candidates": {
            "sample": sample_metrics(keep_all, gt),
            "matches_v2": len(known) - len(differs),
            "differs_from_v2": differs,
        },
        "pairs": {
            "baseline": pair_metrics(pairs, original, gt)["skip"],
            "v2": pair_metrics(pairs, v2, gt)["skip"],
            "keep_all_candidates": pair_metrics(pairs, keep_all, gt)["skip"],
            "both_benign_to_both_vulnerable": sum(
                (original.get(v), original.get(f)) == (0, 0)
                and (v2.get(v), v2.get(f)) == (1, 1)
                for v, f in pairs
            ),
        },
        "validator_issue_verdicts": dict(Counter(
            issue["verdict"] for row in new.values() for issue in row["issues"]
        )),
    }


def compare(gt_file: Path, baseline_dir: Path, run_dir: Path, pilot: bool) -> dict:
    config = json.loads((run_dir / "verification_config.json").read_text(encoding="utf-8"))
    if config["variant"] != "verification_v2":
        raise ValueError("config không thuộc verification_v2")
    baseline_raw = (baseline_dir / "predictions.jsonl").read_bytes()
    if hashlib.sha256(baseline_raw).hexdigest() != config["baseline_predictions_sha256"]:
        raise ValueError("file đối chứng khác cấu hình đã dùng để chạy")
    if hashlib.sha256(gt_file.read_bytes()).hexdigest() != config["data_sha256"]:
        raise ValueError("ground truth khác dữ liệu đã dùng để chạy")

    gt, order, duplicates = read_ground_truth(gt_file)
    if duplicates or len(gt) != 166 or Counter(gt.values()) != {0: 83, 1: 83}:
        raise ValueError("cần dữ liệu SEVEN đủ 83 cặp")
    pairs, warnings = build_pairs(order, gt)
    if warnings or len(pairs) != 83:
        raise ValueError("cần 83 cặp SEVEN hợp lệ")
    if pilot:
        ids = {int(line) for line in PILOT_IDS.read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.lstrip().startswith("#")}
    else:
        ids = set(gt)
    if ids != {int(idx) for _, idx in config["selection"]}:
        raise ValueError("ID của lượt chạy khác danh sách đã khóa cho chế độ chấm")

    baseline = read_rows(baseline_raw)
    new = read_rows((run_dir / "predictions.jsonl").read_bytes())
    if set(baseline) != set(gt) or any(row["pred"] is None for row in baseline.values()):
        raise ValueError("đối chứng phải có đủ 166 phán quyết")
    selected_lines = {int(idx): line for line, idx in config["selection"]}
    for idx, row in new.items():
        if idx not in ids or row["line"] != selected_lines[idx] or row["line"] != baseline[idx]["line"]:
            raise ValueError(f"idx={idx} không khớp ID và dòng dữ liệu đối chứng")
        if (row["provenance"].get("model") != config["model"]
                or row["provenance"].get("variant") != config["variant"]
                or row["stage_counts"]["candidates"] != baseline[idx]["stage_counts"]["candidates"]):
            raise ValueError(f"idx={idx} khác model, biến thể hoặc số candidate")

    unknown = sorted(idx for idx, row in new.items() if row["pred"] is None)
    missing = sorted(ids - new.keys())
    known = set(new) - set(unknown)
    report = {"phase": "pilot" if pilot else "full", "model": config["model"],
              "expected": len(ids), "known": len(known), "unknown": unknown, "missing": missing}
    report["cost_totals"] = {
        name: sum(row["cost"][name] or 0 for row in new.values())
        for name in ("llm_calls", "prompt_tokens", "completion_tokens")
    }
    stop_reasons = Counter()
    for idx, row in new.items():
        path = run_dir / "traces" / f"{idx}_L{row['line']}.json"
        trace = json.loads(path.read_text(encoding="utf-8"))["trace"]
        stop_reasons.update(call.get("stop_reason") or "not_reported" for call in trace
                            if call["agent"] == "UnifiedPrunerAgent")
    report["pruner_stop_reasons"] = dict(stop_reasons)

    if pilot:
        fn = {idx for idx in ids if gt[idx] == 1 and baseline[idx]["pred"] == 0}
        tn = {idx for idx in ids if gt[idx] == 0 and baseline[idx]["pred"] == 0}
        if len(fn) != 28 or len(tn) != 28:
            raise ValueError("pilot phải gồm đúng 28 FN và 28 TN ở lượt đối chứng")
        rescued = sorted(idx for idx in fn & known if new[idx]["pred"] == 1)
        regressed = sorted(idx for idx in tn & known if new[idx]["pred"] == 1)
        report.update({
            "fn_rescued": rescued, "tn_regressed": regressed,
            "fn_unknown": sorted(fn.intersection(unknown)), "tn_unknown": sorted(tn.intersection(unknown)),
            "passed": None if unknown or missing else len(rescued) > len(regressed) and len(regressed) <= 2,
        })
        pilot_pairs = [(v, f) for v, f in pairs if v in ids and f in ids]
        report["post_hoc"] = pilot_diagnostics(gt, pilot_pairs, baseline, new, known)
    else:
        control = summarize(gt, pairs, baseline, known)
        improved = summarize(gt, pairs, new, known)
        fn_delta = improved["fn_with_candidate_rejected"] - control["fn_with_candidate_rejected"]
        fpr_delta = improved["sample"]["fpr"] - control["sample"]["fpr"]
        vps_delta = improved["pair"]["VPS"] - control["pair"]["VPS"]
        report.update({
            "baseline": control, "v2": improved, "delta_fpr_points": fpr_delta * 100,
            "delta_vps_points": vps_delta * 100, "delta_fn_with_candidate_rejected": fn_delta,
            "passed": None if unknown or missing else vps_delta > 0 and fn_delta < 0 and fpr_delta <= 0.1,
        })
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gt", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--out", type=Path, help="File JSON để lưu báo cáo")
    args = parser.parse_args()
    try:
        report = compare(args.gt, args.baseline, args.run, args.pilot)
        output = json.dumps(report, indent=2, ensure_ascii=False)
        if args.out:
            args.out.write_text(output + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(output)


if __name__ == "__main__":
    main()
