#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metrics.py — Tính metric cho VulAgent (Giai đoạn C0.2).

Hợp nhất hai thứ mà repo gốc tách rời và không đủ:
  - sample-level: TP/FP/FN/TN, Precision, Recall, F1, Accuracy, FPR, FNR
    (giống compute_metrics trong VulAgent-Qwen.py)
  - pair-level:
      P-C (pair-correct): cả hai mẫu trong cặp đều đoán đúng
      P-R (pair-reversed): nhãn bị ĐẢO — với cặp (vuln, fixed):
                           pred(vuln)=benign VÀ pred(fixed)=vulnerable
      VPS = P-C − P-R

  ✅ ĐÃ CHỐT ĐỊNH NGHĨA P-R (2026-11-09, đọc bản ACL PDF primary qua markitdown):
     ACL Table/Sec 4.2 verbatim: P-R = "pairs where the two labels are predicted
     inversely (vulnerable predicted as benign while the fixed version is predicted as
     vulnerable)". ⇒ ĐÚNG định nghĩa 'nhãn đảo' đang hiện thực bên dưới (pv=0 & pf=1).
     metrics.py KHÔNG cần sửa logic. (Bản arXiv v1 ghi "both vulnerable" là câu chữ
     tiền ấn phẩm, KHÁC ACL — không dùng.) Hàm còn xuất both_vulnerable/both_benign để
     đối chiếu nếu cần. Xem docs/source_audit.md §7.5.
    (repo gốc evaluate.py chỉ in both_correct/both_wrong, KHÔNG có VPS.)

Nguyên tắc (xác minh C0.5, 2026-11-09 — xem docs/source_audit.md §7.3):
  - SAMPLE-level: mỗi DỰ ĐOÁN được ghép với nhãn ground-truth THEO `idx`
    (không phụ thuộc thứ tự dòng file kết quả).
  - PAIR-level: cặp (vuln, fixed) được ghép theo THỨ TỰ 2 DÒNG LIỀN KỀ trong
    file ground-truth, KHÔNG theo idx — vì PrimeVul có idx KHÁC nhau giữa hai
    thành viên cùng cặp (vd 195908 vs 234731) nên không thể ghép cặp bằng idx.
    Đã kiểm trên dữ liệu: PrimeVul 870 dòng = 435 cặp, SEVEN 166 dòng = 83 cặp,
    đều xen kẽ (target=1, target=0) liền kề (vuln trước), cùng commit_url.
  - Hai chế độ xử lý mẫu thiếu dự đoán: 'skip' và 'count_wrong'.

Chỉ dùng thư viện chuẩn. Chạy self-test: `python3 metrics.py --selftest`.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PRED_FROM_FILENAME = re.compile(r"_(\d+)_full\.json$")
LINE_RE = re.compile(r"^\s*(-?\d+)\s*[,\t ]+\s*([01])\s*$")


# ───────── Đọc ground truth ─────────
def read_ground_truth(path: Path):
    """Trả về (gt, order, dups): gt[idx]=target(0/1); order = danh sách idx theo thứ tự file;
    dups = danh sách (idx, trái_nhãn) cho idx xuất hiện hơn một lần."""
    gt, order, dups = {}, [], []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            ln = raw.strip()
            if not (ln.startswith("{") and ln.endswith("}")):
                continue
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if "idx" not in obj or "target" not in obj:
                continue
            idx = int(obj["idx"])
            if idx in gt:
                dups.append((idx, gt[idx] != int(obj["target"])))
            gt[idx] = int(obj["target"])
            order.append(idx)
    return gt, order, dups


# ───────── Đọc dự đoán ─────────
def read_predictions_file(path: Path):
    """Đọc file kiểu results.txt: mỗi dòng 'idx<sep>pred' (sep = tab/phẩy/cách)
    hoặc JSON {'idx':..,'pred':..}. Trả về (preds, bad_lines, dups);
    dups = danh sách (idx, trái_kết_luận) cho idx lặp lại (bản sau ghi đè bản trước)."""
    preds, bad, dups = {}, 0, []

    def put(idx, pred):
        if idx in preds:
            dups.append((idx, preds[idx] != pred))
        preds[idx] = pred

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            ln = raw.strip()
            if not ln:
                continue
            m = LINE_RE.match(ln)
            if m:
                put(int(m.group(1)), int(m.group(2)))
                continue
            if ln.startswith("{") and ln.endswith("}"):
                try:
                    obj = json.loads(ln)
                    idx = int(obj.get("idx"))
                    pred = int(obj.get("pred"))
                    if pred in (0, 1):
                        put(idx, pred)
                        continue
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            bad += 1
    return preds, bad, dups


def read_predictions_dir(path: Path, pred_key: str):
    """Đọc thư mục per-sample '*_full.json' của repo gốc.
    idx lấy từ tên file (..._<idx>_full.json); pred từ trường pred_key.
    Trả về (preds, bad, dups) như read_predictions_file."""
    preds, bad, dups = {}, 0, []
    for p in sorted(path.rglob("*_full.json")):
        m = PRED_FROM_FILENAME.search(p.name)
        if not m:
            bad += 1
            continue
        idx = int(m.group(1))
        try:
            obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            bad += 1
            continue
        val = obj.get(pred_key)
        if val is None and pred_key != "vulnerability_reported":
            val = obj.get("vulnerability_reported")
        pred = 1 if val else 0
        if idx in preds:
            dups.append((idx, preds[idx] != pred))
        preds[idx] = pred
    return preds, bad, dups


# ───────── Ghép cặp ─────────
def build_pairs(order, gt, mode="consecutive"):
    """Trả về danh sách cặp (idx_vuln, idx_fixed) và cảnh báo.
    'consecutive': gom 2 idx liền nhau; chuẩn hóa để phần tử đầu là vuln (target=1)."""
    pairs, warns = [], []
    if mode != "consecutive":
        warns.append(f"Chế độ ghép cặp '{mode}' chưa hỗ trợ; dùng 'consecutive'.")
    n = len(order)
    if n % 2 != 0:
        warns.append(f"Số mẫu lẻ ({n}); bỏ mẫu cuối khi ghép cặp.")
    for i in range(0, n - 1, 2):
        a, b = order[i], order[i + 1]
        ta, tb = gt.get(a), gt.get(b)
        if {ta, tb} != {0, 1}:
            warns.append(f"Cặp ({a},{b}) không phải (vuln,fixed): target=({ta},{tb}).")
            pairs.append((a, b))  # giữ nguyên thứ tự, không chuẩn hóa được
            continue
        # chuẩn hóa: phần tử đầu = vuln (target==1)
        pairs.append((a, b) if ta == 1 else (b, a))
    return pairs, warns


# ───────── Metric sample-level ─────────
def sample_metrics(preds, gt):
    TP = FP = FN = TN = 0
    for idx, p in preds.items():
        if idx not in gt:
            continue
        t = gt[idx]
        if t == 1 and p == 1:
            TP += 1
        elif t == 0 and p == 1:
            FP += 1
        elif t == 1 and p == 0:
            FN += 1
        elif t == 0 and p == 0:
            TN += 1
    tot = TP + FP + FN + TN
    r = lambda num, den: (num / den) if den else 0.0
    return {
        "TP": TP, "FP": FP, "FN": FN, "TN": TN, "evaluated": tot,
        "precision": r(TP, TP + FP),
        "recall": r(TP, TP + FN),
        "f1": r(2 * TP, 2 * TP + FP + FN),
        "accuracy": r(TP + TN, tot),
        "fpr": r(FP, FP + TN),
        "fnr": r(FN, FN + TP),
    }


# ───────── Metric pair-level (ACL) ─────────
def pair_metrics(pairs, preds, gt):
    """pairs đã chuẩn hóa (vuln_idx, fixed_idx).
    Trả về dict cho 2 chế độ: 'skip' (bỏ cặp thiếu) và 'count_wrong' (thiếu = sai)."""
    total = len(pairs)

    def bucket(include_missing_as_wrong):
        n_eval = pc = pr = both_pos = both_neg = missing = 0
        for v_idx, f_idx in pairs:
            pv, pf = preds.get(v_idx), preds.get(f_idx)
            tv, tf = gt.get(v_idx), gt.get(f_idx)
            if pv is None or pf is None:
                missing += 1
                if not include_missing_as_wrong:
                    continue
                n_eval += 1  # tính vào mẫu số, coi như không-đúng
                continue
            n_eval += 1
            if pv == tv and pf == tf:
                pc += 1
            # P-R: nhãn bị đảo (chỉ có nghĩa khi cặp thật là (vuln=1, fixed=0))
            if tv == 1 and tf == 0 and pv == 0 and pf == 1:
                pr += 1
            if pv == 1 and pf == 1:
                both_pos += 1
            if pv == 0 and pf == 0:
                both_neg += 1
        den = n_eval if n_eval else 0
        ratio = lambda x: (x / den) if den else 0.0
        return {
            "pairs_total": total, "pairs_evaluated": n_eval, "pairs_missing": missing,
            "P_C": pc, "P_R": pr, "both_vulnerable": both_pos, "both_benign": both_neg,
            "P_C_ratio": ratio(pc), "P_R_ratio": ratio(pr), "VPS": ratio(pc) - ratio(pr),
        }

    return {"skip": bucket(False), "count_wrong": bucket(True)}


# ───────── In & xuất ─────────
def print_report(sm, pm, coverage, warns):
    def pct(x):
        return f"{x * 100:6.2f}%"
    print("==== Sample-level ====")
    print(f"  Đã chấm: {sm['evaluated']} mẫu | Coverage: {pct(coverage)}")
    print(f"  TP={sm['TP']} FP={sm['FP']} FN={sm['FN']} TN={sm['TN']}")
    print(f"  Accuracy={pct(sm['accuracy'])}  Precision={pct(sm['precision'])}  "
          f"Recall={pct(sm['recall'])}  F1={pct(sm['f1'])}")
    print(f"  FPR={pct(sm['fpr'])}  FNR={pct(sm['fnr'])}")
    for mode in ("skip", "count_wrong"):
        b = pm[mode]
        print(f"\n==== Pair-level [{mode}] ====")
        print(f"  Tổng cặp: {b['pairs_total']} | đánh giá: {b['pairs_evaluated']} | "
              f"thiếu dự đoán: {b['pairs_missing']}")
        print(f"  P-C={b['P_C']} ({pct(b['P_C_ratio'])})  "
              f"P-R={b['P_R']} ({pct(b['P_R_ratio'])})  VPS={pct(b['VPS'])}")
        print(f"  both-vulnerable={b['both_vulnerable']}  both-benign={b['both_benign']}")
    if warns:
        print("\n==== CẢNH BÁO ====")
        for w in warns:
            print(f"  ⚠ {w}")


def write_outputs(out_prefix, sm, pm, coverage, pairs, preds, gt, warns):
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    summary = {"sample_level": sm, "pair_level": pm,
               "coverage": coverage, "warnings": warns}
    (out_prefix.with_suffix(".json")).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    with out_prefix.with_suffix(".pairs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_index", "vuln_idx", "pred_vuln", "fixed_idx", "pred_fixed",
                    "pair_correct", "pair_reversed", "missing"])
        for i, (v, fx) in enumerate(pairs):
            pv, pf = preds.get(v), preds.get(fx)
            tv, tfx = gt.get(v), gt.get(fx)
            miss = int(pv is None or pf is None)
            pc = int(not miss and pv == tv and pf == tfx)
            pr = int(not miss and tv == 1 and tfx == 0 and pv == 0 and pf == 1)
            w.writerow([i, v, "" if pv is None else pv, fx,
                        "" if pf is None else pf, pc, pr, miss])
    print(f"\nĐã ghi: {out_prefix.with_suffix('.json')} và {out_prefix.with_suffix('.pairs.csv')}")


# ───────── Self-test ─────────
def selftest():
    # 3 cặp: idx 1-2, 3-4, 5-6. target: vuln=1, fixed=0.
    gt = {1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0}
    order = [1, 2, 3, 4, 5, 6]
    # Dự đoán:
    #  cặp(1,2): pred 1,0 -> ĐÚNG cả hai  -> P-C
    #  cặp(3,4): pred 0,1 -> ĐẢO hoàn toàn -> P-R
    #  cặp(5,6): pred 1,1 -> both-vulnerable (sai 1 nửa)
    preds = {1: 1, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1}
    # Sample-level tay:
    #  idx1 t1p1 TP; idx2 t0p0 TN; idx3 t1p0 FN; idx4 t0p1 FP; idx5 t1p1 TP; idx6 t0p1 FP
    #  TP=2 FP=2 FN=1 TN=1
    sm = sample_metrics(preds, gt)
    assert (sm["TP"], sm["FP"], sm["FN"], sm["TN"]) == (2, 2, 1, 1), sm
    assert abs(sm["precision"] - 2 / 4) < 1e-9
    assert abs(sm["recall"] - 2 / 3) < 1e-9
    assert abs(sm["accuracy"] - 3 / 6) < 1e-9
    assert abs(sm["fpr"] - 2 / 3) < 1e-9
    pairs, warns = build_pairs(order, gt)
    assert pairs == [(1, 2), (3, 4), (5, 6)] and not warns, (pairs, warns)
    pm = pair_metrics(pairs, preds, gt)
    s = pm["skip"]
    assert (s["P_C"], s["P_R"], s["both_vulnerable"], s["both_benign"]) == (1, 1, 1, 0), s
    assert abs(s["VPS"] - (1 / 3 - 1 / 3)) < 1e-9, s
    # count_wrong với 1 cặp thiếu dự đoán:
    preds2 = dict(preds); del preds2[6]
    pm2 = pair_metrics(pairs, preds2, gt)
    assert pm2["skip"]["pairs_evaluated"] == 2 and pm2["skip"]["pairs_missing"] == 1
    assert pm2["count_wrong"]["pairs_evaluated"] == 3
    print("✅ self-test PASS")


def main():
    ap = argparse.ArgumentParser(description="Tính metric VulAgent (sample + pair + VPS).")
    ap.add_argument("--gt", type=Path, help="File ground-truth .jsonl (có idx, target).")
    ap.add_argument("--pred", type=Path, help="File dự đoán kiểu results.txt.")
    ap.add_argument("--pred-dir", type=Path, help="Thư mục per-sample *_full.json.")
    ap.add_argument("--pred-key", default="final_vulnerability_reported",
                    help="Trường chứa kết luận trong *_full.json.")
    ap.add_argument("--pair", default="consecutive", choices=["consecutive"],
                    help="Cách ghép cặp.")
    ap.add_argument("--out", default="results/tables/metrics",
                    help="Tiền tố file kết quả (.json, .pairs.csv).")
    ap.add_argument("--selftest", action="store_true", help="Chạy kiểm thử công thức rồi thoát.")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    if not args.gt or (not args.pred and not args.pred_dir):
        ap.error("Cần --gt và (--pred hoặc --pred-dir). Hoặc dùng --selftest.")

    gt, order, gt_dups = read_ground_truth(args.gt)
    if args.pred:
        preds, bad, pred_dups = read_predictions_file(args.pred)
    else:
        preds, bad, pred_dups = read_predictions_dir(args.pred_dir, args.pred_key)

    warns = []
    if gt_dups:
        conflict = sum(1 for _, c in gt_dups if c)
        warns.append(f"Ground-truth có {len(gt_dups)} idx trùng ({conflict} trái nhãn): "
                     f"{sorted({i for i, _ in gt_dups})[:10]} — sample-level chỉ chấm theo idx duy nhất.")
    if pred_dups:
        conflict = sum(1 for _, c in pred_dups if c)
        warns.append(f"Dự đoán có {len(pred_dups)} idx trùng ({conflict} TRÁI kết luận, bản sau ghi đè): "
                     f"{sorted({i for i, _ in pred_dups})[:10]} — nguồn dự đoán không sạch, kiểm tra lại.")
    if bad:
        warns.append(f"Không parse được {bad} dòng/file dự đoán.")
    extra = [i for i in preds if i not in gt]
    if extra:
        warns.append(f"{len(extra)} idx dự đoán không có trong ground-truth (bỏ qua).")

    pairs, pwarns = build_pairs(order, gt, args.pair)
    warns += pwarns

    coverage = (sum(1 for i in order if i in preds) / len(order)) if order else 0.0
    sm = sample_metrics(preds, gt)
    pm = pair_metrics(pairs, preds, gt)

    print_report(sm, pm, coverage, warns)
    write_outputs(args.out, sm, pm, coverage, pairs, preds, gt, warns)


if __name__ == "__main__":
    main()
