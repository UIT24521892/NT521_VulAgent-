#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py — Chạy pipeline của nhóm (src/pipeline.py) trên một file dữ liệu .jsonl.

Hai chế độ:
  --backend replay   (mặc định, 0 đồng) phát lại output đã công bố của repo gốc:
      python3 scripts/run_pipeline.py --data <file.jsonl> --replay-dir <thư mục *_full.json> \
          --out results/raw/<tên_lượt>
  --backend api      gọi model thật, TỐN PHÍ. Bắt buộc --confirm-paid và --limit/--ids;
      key đọc từ vulagent/.env hoặc biến môi trường (xem .env.example).

Đầu ra trong --out:
  predictions.jsonl  mỗi dòng một bản ghi (không kèm trace) — đưa thẳng vào metrics.py --pred
  traces/<id>.json   bản ghi đầy đủ kèm trace từng agent
  run_meta.json      cấu hình, hash prompt, tổng chi phí, thống kê quyết định

Script KHÔNG đọc nhãn: `Sample.from_record` bỏ target/cwe. Chấm điểm là bước riêng
(`scripts/metrics.py --gt ... --pred <out>/predictions.jsonl`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from llm import AnthropicBackend, OpenAICompatBackend, PrefixReplayBackend, ReplayBackend, LLMError  # noqa: E402
from pipeline import (PRUNER, V2_PRUNER_MAX_TOKENS, VALIDATOR, PromptStore, Sample,  # noqa: E402
                      analyse, verify_candidates)
from schema import validate_prototype_output                   # noqa: E402

UPSTREAM = ROOT / "upstream" / "VulAgent"
DEFAULT_PROMPTS = UPSTREAM / "Quickly reproduce the experiment" / "prompt_template"
VERIFICATION_PROMPTS = ROOT / "prompts_v2"
FIXTURE_IDX = re.compile(r"_(\d+)_full\.json$")


def load_env_file(path: Path) -> None:
    """Nạp KEY=VALUE từ .env vào os.environ (không ghi đè biến đã có, không in giá trị)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def read_records(path: Path):
    """Trả (số dòng 1-based, record) cho mỗi dòng JSON hợp lệ có idx và func."""
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "idx" in rec and "func" in rec:
                yield n, rec


def index_fixtures(root: Path) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = {}
    for p in sorted(root.rglob("*_full.json")):
        m = FIXTURE_IDX.search(p.name)
        if m:
            idx.setdefault(m.group(1), []).append(p)
    return idx


def upstream_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def load_verification_baseline(path: Path, data: Path, provider: str, model: str) -> tuple[dict, str]:
    meta = json.loads((path / "run_meta.json").read_text(encoding="utf-8"))
    if (meta.get("backend"), meta.get("provider"), meta.get("model"), meta.get("skip")) != (
            "api", provider, model, []):
        raise ValueError("đối chứng phải dùng cùng provider/model và có context")
    baseline_data = Path(meta["data"])
    if data.resolve() not in (baseline_data.resolve(), (ROOT / baseline_data).resolve()):
        raise ValueError("--data phải trỏ tới file dữ liệu của lượt đối chứng")

    raw = (path / "predictions.jsonl").read_bytes()
    baseline = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["line"] in baseline or rec["pred"] not in (0, 1) or rec.get("error"):
            raise ValueError("đối chứng có dòng trùng hoặc phán quyết chưa xác định")
        if rec["provenance"].get("model") != model:
            raise ValueError("đối chứng có mẫu dùng model khác")
        candidates = rec["candidates"]
        if not isinstance(candidates, list) or any(not isinstance(c, dict) for c in candidates):
            raise ValueError("đối chứng có danh sách candidate sai cấu trúc")
        baseline[rec["line"]] = rec
    return baseline, hashlib.sha256(raw).hexdigest()


def main() -> int:
    with ExitStack() as stack:
        return run_pipeline(stack)


def run_pipeline(stack: ExitStack) -> int:
    ap = argparse.ArgumentParser(description="Chạy pipeline VulAgent của nhóm.")
    ap.add_argument("--data", type=Path, required=True, help="File .jsonl (idx, func, ...)")
    ap.add_argument("--out", type=Path, required=True, help="Thư mục kết quả (vd results/raw/<tên>)")
    ap.add_argument("--backend", choices=["replay", "api"], default="replay")
    ap.add_argument("--provider", choices=["dashscope", "anthropic"], default="dashscope",
                    help="Nhà cung cấp cho --backend api: dashscope (Qwen, đúng paper) hoặc "
                         "anthropic (Claude, thí nghiệm backend khác)")
    ap.add_argument("--replay-dir", type=Path, help="Thư mục chứa *_full.json của repo gốc")
    ap.add_argument("--prompts", type=Path, help="Thư mục prompt template")
    ap.add_argument("--verification-v2-from", type=Path, metavar="BASELINE_DIR",
                    help="Kiểm chứng tĩnh v2 trên candidate đã lưu của lượt đối chứng")
    ap.add_argument("--reuse-prefix-from", type=Path, metavar="BASELINE_DIR",
                    help="Phát lại output MetaAgent → TriggerPlanner từ trace của lượt này; "
                         "chỉ gọi API cho UnifiedPruner + FinalValidator (RQ3 tách biến)")
    ap.add_argument("--ids", help="Chỉ chạy các idx này (phân tách bằng dấu phẩy)")
    ap.add_argument("--ids-file", type=Path, help="File chứa idx, mỗi dòng một idx")
    ap.add_argument("--limit", type=int, help="Chỉ chạy N mẫu đầu (sau khi lọc --ids)")
    ap.add_argument("--skip", action="append", default=[], choices=["pruner", "context"],
                    help="Ablation: bỏ một thành phần (chỉ có nghĩa với --backend api)")
    ap.add_argument("--no-upstream-quirks", action="store_true",
                    help="Sửa lỗi hoán đổi proj/name của repo gốc (mặc định giữ để tái hiện)")
    ap.add_argument("--confirm-paid", action="store_true", help="Xác nhận gọi API tốn phí")
    args = ap.parse_args()

    if args.verification_v2_from and (
            args.backend != "api" or args.skip or args.prompts or args.no_upstream_quirks):
        ap.error("--verification-v2-from cần --backend api và cấu hình v2 mặc định có context")
    if args.reuse_prefix_from and (args.backend != "api" or args.verification_v2_from
                                   or "pruner" in args.skip):
        ap.error("--reuse-prefix-from cần --backend api, không dùng cùng v2 hay --skip pruner")
    prompt_dir = (VERIFICATION_PROMPTS if args.verification_v2_from
                  else args.prompts or DEFAULT_PROMPTS)
    if not prompt_dir.is_dir():
        ap.error(f"không thấy thư mục prompt: {prompt_dir}")

    wanted = None
    if args.ids:
        wanted = {s.strip() for s in args.ids.split(",") if s.strip()}
    if args.ids_file:
        wanted = (wanted or set()) | {l.strip() for l in args.ids_file.read_text(encoding="utf-8").splitlines()
                                   if l.strip() and not l.lstrip().startswith("#")}

    fixtures = {}
    if args.backend == "replay":
        if not args.replay_dir or not args.replay_dir.is_dir():
            ap.error("--backend replay cần --replay-dir trỏ tới thư mục *_full.json")
        if args.skip:
            ap.error("--skip vô nghĩa khi phát lại output đã có; chỉ dùng với --backend api")
        fixtures = index_fixtures(args.replay_dir)
        api_backend = None
    else:
        if not args.confirm_paid:
            ap.error("--backend api TỐN PHÍ: thêm --confirm-paid sau khi nhóm đã chốt key và ngân sách")
        if not (args.limit or wanted):
            ap.error("--backend api cần --limit hoặc --ids để giới hạn số mẫu")
        load_env_file(ROOT / ".env")
        try:
            api_backend = (AnthropicBackend() if args.provider == "anthropic"
                           else OpenAICompatBackend())
        except LLMError as e:
            print(f"Không khởi tạo được backend API ({args.provider}): {e}", file=sys.stderr)
            return 2

    prompts = PromptStore(prompt_dir)
    verification = None
    baseline = {}
    records = read_records(args.data)
    if args.verification_v2_from:
        try:
            baseline, baseline_hash = load_verification_baseline(
                args.verification_v2_from, args.data, args.provider, api_backend.model)
            selected = [(line, rec) for line, rec in records
                        if wanted is None or str(rec["idx"]) in wanted]
            if wanted is not None and wanted != {str(rec["idx"]) for _, rec in selected}:
                raise ValueError("danh sách ID có mẫu ngoài tập dữ liệu")
            if args.limit is not None and args.limit <= 0:
                raise ValueError("--limit phải dương")
            records = selected[:args.limit]
            if not records or any(
                    line not in baseline or str(rec["idx"]) != str(baseline[line]["idx"])
                    for line, rec in records):
                raise ValueError("có mẫu thiếu đối chứng cùng ID và dòng dữ liệu")
        except (OSError, KeyError, TypeError, ValueError) as e:
            ap.error(f"không đọc được đối chứng v2: {e}")
        verification = {
            "variant": "verification_v2", "baseline_predictions_sha256": baseline_hash,
            "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
            "selection": [[line, str(rec["idx"])] for line, rec in records],
            "provider": args.provider, "model": api_backend.model,
            "effort": getattr(api_backend, "effort", None),
            "pruner_max_tokens": V2_PRUNER_MAX_TOKENS,
            "validator_max_tokens": api_backend.max_tokens,
            "prompt_sha256": prompts.sha256_all(),
        }

    prefix = None
    if args.reuse_prefix_from:
        try:
            pmeta = json.loads((args.reuse_prefix_from / "run_meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            ap.error(f"không đọc được run_meta của lượt gốc: {e}")
        if (pmeta.get("provider"), pmeta.get("model")) != (args.provider, api_backend.model):
            ap.error("lượt gốc phải cùng provider/model với lượt này")
        prefix = {"from": str(args.reuse_prefix_from), "baseline_skip": pmeta.get("skip"),
                  "live_agents": [PRUNER, VALIDATOR]}

    (args.out / "traces").mkdir(parents=True, exist_ok=True)
    pred_path = args.out / "predictions.jsonl"
    config_path = args.out / "verification_config.json"
    if verification is not None:
        lock = stack.enter_context((args.out / ".verification.lock").open("a"))
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            ap.error("lượt v2 này đang chạy trong một tiến trình khác")
        if config_path.exists():
            if json.loads(config_path.read_text(encoding="utf-8")) != verification:
                ap.error("cấu hình v2 khác lượt trước, hãy dùng thư mục --out mới")
        elif pred_path.exists():
            ap.error("thư mục --out đã có dự đoán của lượt khác")
        else:
            config_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    elif config_path.exists():
        ap.error("thư mục --out dành cho lượt verification_v2")

    done = set()
    if pred_path.exists():   # chạy tiếp: bỏ qua dòng dữ liệu đã có kết quả
        done = {json.loads(l)["line"] for l in pred_path.read_text(encoding="utf-8").splitlines() if l.strip()}

    decisions, errors_by_stage = Counter(), Counter()
    totals = Counter()
    schema_fail, no_fixture, multi_fixture, upstream_diff = [], [], [], []
    n_run = 0

    with pred_path.open("a", encoding="utf-8") as out:
        for line_no, rec in records:
            sid = str(rec["idx"])
            if wanted is not None and sid not in wanted:
                continue
            if args.limit and n_run >= args.limit:
                break
            if line_no in done:
                continue
            n_run += 1

            provenance = {"backend": args.backend}
            if args.backend == "replay":
                paths = fixtures.get(sid, [])
                if not paths:
                    no_fixture.append(sid)
                    continue
                if len(paths) > 1:
                    multi_fixture.append(sid)
                fx = json.loads(paths[0].read_text(encoding="utf-8"))
                backend = ReplayBackend(fx)
                provenance["fixture"] = str(paths[0].relative_to(args.replay_dir))
                provenance["upstream_flag"] = fx.get("final_vulnerability_reported")
            else:
                backend = api_backend
                provenance["model"] = backend.model
                if prefix is not None:
                    tpath = args.reuse_prefix_from / "traces" / f"{sid}_L{line_no}.json"
                    trace = json.loads(tpath.read_text(encoding="utf-8"))["trace"]
                    backend = PrefixReplayBackend(trace, api_backend, prefix["live_agents"])
                    provenance["prefix_from"] = str(tpath)

            sample = Sample.from_record(rec)
            if verification is not None:
                result = verify_candidates(sample, backend, prompts, baseline[line_no]["candidates"])
                provenance["variant"] = verification["variant"]
            else:
                result = analyse(sample, backend, prompts,
                                 upstream_quirks=not args.no_upstream_quirks, skip=tuple(args.skip))
            result["line"] = line_no
            result["idx"] = rec["idx"]
            result["provenance"] = provenance

            ok, errs, _ = validate_prototype_output(result)
            if not ok:
                schema_fail.append((sid, errs))

            (args.out / "traces" / f"{sid}_L{line_no}.json").write_text(
                json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            slim = {k: v for k, v in result.items() if k != "trace"}
            out.write(json.dumps(slim, ensure_ascii=False) + "\n")
            out.flush()

            decisions[result["decision"]] += 1
            if result["error"]:
                errors_by_stage[f"{result['error']['stage']}:{result['error']['kind']}"] += 1
            for k in ("llm_calls", "prompt_chars", "output_chars"):
                totals[k] += result["cost"][k]
            for k in ("prompt_tokens", "completion_tokens"):
                if result["cost"][k] is not None:
                    totals[k] += result["cost"][k]
            if args.backend == "replay":
                up = provenance["upstream_flag"]
                if result["pred"] is None or bool(result["pred"]) != bool(up):
                    upstream_diff.append({"idx": rec["idx"], "ours": result["decision"],
                                          "upstream_flag": up, "error": result["error"]})

    n_done = sum(decisions.values())
    meta = {
        "run_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "command": " ".join(sys.argv),
        "data": str(args.data), "backend": args.backend,
        "provider": args.provider if args.backend == "api" else None,
        "replay_dir": str(args.replay_dir) if args.replay_dir else None,
        "model": api_backend.model if api_backend else "upstream-published-output",
        "upstream_commit": upstream_commit(),
        "upstream_quirks": not args.no_upstream_quirks, "skip": args.skip,
        "prompt_sha256": prompts.sha256_all(),
        "samples_this_invocation": n_done,
        "decisions": dict(decisions), "errors_by_stage": dict(errors_by_stage),
        "cost_totals": dict(totals),
        "avg_llm_calls_per_sample": round(totals["llm_calls"] / n_done, 3) if n_done else None,
        "schema_failures": schema_fail,
        "replay": {"no_fixture": no_fixture, "multiple_fixtures": multi_fixture,
                   "differs_from_upstream": upstream_diff} if args.backend == "replay" else None,
    }
    if verification is not None:
        meta["verification"] = verification
    if prefix is not None:
        meta["prefix_replay"] = prefix
    (args.out / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Đã chạy {n_done} mẫu ({args.backend}). Quyết định: {dict(decisions)}")
    if errors_by_stage:
        print(f"  unknown theo giai đoạn: {dict(errors_by_stage)}")
    if n_done:
        print(f"  Lời gọi LLM: {totals['llm_calls']} (TB {totals['llm_calls'] / n_done:.2f}/mẫu); "
              f"ký tự prompt {totals['prompt_chars']}, ký tự output {totals['output_chars']}")
    if args.backend == "replay":
        print(f"  Thiếu fixture: {len(no_fixture)} | idx có nhiều fixture: {len(multi_fixture)} | "
              f"khác cờ của repo gốc: {len(upstream_diff)}")
    if schema_fail:
        print(f"  ❌ {len(schema_fail)} bản ghi KHÔNG đạt schema: {schema_fail[:3]}")
    print(f"  Kết quả: {pred_path}")
    return 1 if schema_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
