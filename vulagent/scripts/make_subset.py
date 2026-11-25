#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_subset.py — Chọn tập con 100 cặp PrimeVul cho RQ1 (PLAN §0.4 T3). Không gọi API.

Quy tắc (công khai, chạy lại cho cùng kết quả):
  1. File gốc 870 dòng = 435 cặp. Ghép cặp theo THỨ TỰ DÒNG: cặp k (0-based) = dòng 2k+1
     (vulnerable, target=1) và 2k+2 (fixed, target=0), đánh số dòng 1-based. Không ghép theo idx.
  2. Loại các cặp có idx xuất hiện nhiều lần trong file (metrics.py khóa theo idx nên idx trùng
     sẽ chấm sai). Với file đã kiểm toán, đó là cặp 223, 224, 327, 328 (dòng 447, 449, 655, 657).
  3. random.Random(SEED).sample(các cặp còn lại, N), rồi sắp lại theo thứ tự gốc.

Chạy từ thư mục vulagent/:
  python3 scripts/make_subset.py
Ghi:
  data/primevul_subset100.jsonl          (gitignore) các dòng gốc giữ nguyên byte, theo thứ tự cặp
  configs/primevul_subset100_pairs.txt   (commit) số thứ tự cặp, dòng gốc, idx vuln/fixed
In shasum của file subset để ghi vào experiment_manifest.yaml.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT / "upstream" / "VulAgent" / "Dataset" / "PrimeVul" / "primevul_test_paired.jsonl"
# experiment_manifest.yaml → datasets.primevul_test.sha256
EXPECTED_SRC_SHA256 = "82f443066dde5eb3fd07539dd811ef63344a2442f7abd242e9a86d62bfd8d885"
EXPECTED_DUP_PAIRS = [223, 224, 327, 328]
SEED = 521
N_PAIRS = 100


def load_pairs(lines: list[bytes]) -> list[dict]:
    """Ghép dòng liền kề thành cặp và kiểm (vuln, fixed). Lỗi cấu trúc → ValueError."""
    if len(lines) % 2:
        raise ValueError(f"số dòng lẻ ({len(lines)}), không ghép cặp theo thứ tự dòng được")
    pairs = []
    for k in range(len(lines) // 2):
        a, b = json.loads(lines[2 * k]), json.loads(lines[2 * k + 1])
        if (a.get("target"), b.get("target")) != (1, 0):
            raise ValueError(f"cặp {k} (dòng {2 * k + 1}-{2 * k + 2}) không phải (vulnerable, fixed): "
                             f"target=({a.get('target')}, {b.get('target')})")
        pairs.append({"pair": k, "line": 2 * k + 1, "idx_vul": a["idx"], "idx_fix": b["idx"],
                      "raw": (lines[2 * k], lines[2 * k + 1])})
    return pairs


def duplicate_pairs(pairs: list[dict]) -> list[int]:
    count = Counter(i for p in pairs for i in (p["idx_vul"], p["idx_fix"]))
    return [p["pair"] for p in pairs if count[p["idx_vul"]] > 1 or count[p["idx_fix"]] > 1]


def select(pairs: list[dict], n: int, seed: int) -> tuple[list[dict], list[int]]:
    dups = set(duplicate_pairs(pairs))
    eligible = [p["pair"] for p in pairs if p["pair"] not in dups]
    if n > len(eligible):
        raise ValueError(f"chỉ có {len(eligible)} cặp hợp lệ, không chọn được {n}")
    chosen = sorted(random.Random(seed).sample(eligible, n))
    return [pairs[k] for k in chosen], sorted(dups)


def main() -> int:
    ap = argparse.ArgumentParser(description="Chọn tập con cặp PrimeVul (PLAN §0.4 T3).")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "primevul_subset100.jsonl")
    ap.add_argument("--pairs-out", type=Path, default=ROOT / "configs" / "primevul_subset100_pairs.txt")
    ap.add_argument("--n", type=int, default=N_PAIRS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--allow-other-source", action="store_true",
                    help="Cho phép file nguồn khác shasum đã kiểm toán (chỉ để thử nghiệm)")
    args = ap.parse_args()

    raw = args.src.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()
    if src_sha != EXPECTED_SRC_SHA256 and not args.allow_other_source:
        print(f"shasum nguồn {src_sha} khác bản đã kiểm toán {EXPECTED_SRC_SHA256}", file=sys.stderr)
        return 2
    lines = [l for l in raw.splitlines(keepends=True) if l.strip()]
    pairs = load_pairs(lines)
    chosen, dups = select(pairs, args.n, args.seed)
    if src_sha == EXPECTED_SRC_SHA256 and dups != EXPECTED_DUP_PAIRS:
        print(f"cặp idx trùng {dups} khác bản kiểm toán {EXPECTED_DUP_PAIRS}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    body = b"".join(l if l.endswith(b"\n") else l + b"\n" for p in chosen for l in p["raw"])
    args.out.write_bytes(body)
    subset_sha = hashlib.sha256(body).hexdigest()

    projects = Counter(json.loads(p["raw"][0]).get("project", "?") for p in chosen)
    header = [
        "# Tập con PrimeVul cho RQ1 (PLAN §0.4 T3), tạo bởi scripts/make_subset.py",
        f"# nguồn: {(args.src.resolve().relative_to(ROOT) if args.src.resolve().is_relative_to(ROOT) else args.src).as_posix()}",
        f"# nguồn sha256: {src_sha}",
        f"# {len(pairs)} cặp, loại {len(dups)} cặp idx trùng {dups}, "
        f"random.Random({args.seed}).sample(..., {args.n}), giữ thứ tự gốc",
        f"# subset sha256: {subset_sha}",
        "# cặp (0-based)\tdòng vuln trong nguồn (1-based)\tidx_vul\tidx_fix",
    ]
    rows = [f"{p['pair']}\t{p['line']}\t{p['idx_vul']}\t{p['idx_fix']}" for p in chosen]
    args.pairs_out.parent.mkdir(parents=True, exist_ok=True)
    args.pairs_out.write_text("\n".join(header + rows) + "\n", encoding="utf-8")

    print(f"Đã chọn {len(chosen)} cặp ({2 * len(chosen)} mẫu) từ {len(pairs)} cặp, loại cặp {dups}.")
    print(f"  {args.out}  sha256={subset_sha}")
    print(f"  {args.pairs_out}")
    print(f"  project nhiều nhất: {projects.most_common(5)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
