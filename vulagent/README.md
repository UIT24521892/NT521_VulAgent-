# Đề tài VulAgent — phát hiện lỗ hổng mã nguồn bằng lập và kiểm chứng giả thuyết

**Trạng thái (2026-11-24): pipeline của nhóm đã chạy đủ 166 mẫu SEVEN bằng `claude-haiku-5-5` (1 lượt) và tính lại khớp số Qwen3 mà tác giả công bố; còn baseline CoT, thí nghiệm không context, PrimeVul và phần cải tiến — bảng trạng thái theo tiêu chí chấm ở [PLAN.md](PLAN.md) §0.** Quy tắc chung: [../AGENT.md](../AGENT.md). Tài liệu: [docs/source_audit.md](docs/source_audit.md), [experiment_manifest.yaml](experiment_manifest.yaml), [docs/reproduction_contract.md](docs/reproduction_contract.md), [docs/reproduction_plan.md](docs/reproduction_plan.md) (C0–C5). Mã: [src/pipeline.py](src/pipeline.py), [src/llm.py](src/llm.py), [src/schema.py](src/schema.py), [scripts/run_pipeline.py](scripts/run_pipeline.py), [scripts/show_trace.py](scripts/show_trace.py), [scripts/metrics.py](scripts/metrics.py), [tests/](tests/). Repo gốc clone cô lập ở `upstream/` (gitignore, không commit — có key nhúng cứng, không dùng). Bước tiếp: C1 dry-run 1 mẫu, cần key DashScope + ngân sách.

## Chạy thử (0 đồng, cần clone repo gốc vào `upstream/VulAgent`, commit `065467c`)

```bash
cd vulagent
python3 -m unittest discover -s tests            # 16 test
U=upstream/VulAgent
python3 scripts/run_pipeline.py --data "$U/Dataset/SEVEN_context/test_with_idx_context_cleaned.jsonl" \
    --replay-dir "$U/VulAgent_Seven/With contetxt/Qwen3" --out results/raw/replay_seven_qwen3
python3 scripts/metrics.py --gt "$U/Dataset/SEVEN_context/test_with_idx_context_cleaned.jsonl" \
    --pred results/raw/replay_seven_qwen3/predictions.jsonl --out results/tables/replay_seven_qwen3
python3 scripts/show_trace.py results/raw/replay_seven_qwen3/traces/71_L71.json   # đọc một ca
```

`--backend replay` phát lại output từng agent mà repo gốc đã công bố; đó **không** phải kết quả nhóm chạy model. Chạy model thật: `--backend api --confirm-paid` cùng `--limit`/`--ids`, sau khi nhóm chốt key và ngân sách (xem [docs/reproduction_plan.md](docs/reproduction_plan.md) C1).

- **Paper:** đề giao bản [arXiv 2509.11523](https://arxiv.org/abs/2509.11523); nhóm lấy bản [Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.928/) làm mốc số liệu và định nghĩa, khác biệt giữa hai bản ở [docs/source_audit.md](docs/source_audit.md) §7.7. Mã công khai: https://github.com/HotFrom/VulAgent
- **Dữ liệu:** PrimeVul, SVEN — xác định đường dẫn, phiên bản, giấy phép, split thực tế từ nguồn chính thức trước khi tải.
- **Tiêu chí chấm đồ án cuối kì (thang 10, theo bảng tiêu chí người dùng cung cấp ngày 2026-11-06):**

  | # | Tiêu chí | Điểm |
  |---|---|---|
  | 1 | Hiểu rõ ngữ cảnh, vai trò, vấn đề của bài toán & kỹ năng thuyết trình | 1đ |
  | 2 | Nắm bắt và giải thích được phương pháp – kỹ thuật được sử dụng | 3đ |
  | 3 | Hiện thực và demo — bài báo **có mã công khai** nên yêu cầu: tái hiện các thí nghiệm trong bài báo; biện luận, phân tích ưu và nhược điểm của phương pháp | 5đ |
  | 4 | Điểm cộng xuất sắc — bài báo có mã công khai: thực nghiệm bổ sung trên kịch bản mới hoặc dữ liệu mới; hoặc cải tiến phương pháp và thực nghiệm trên kịch bản/dữ liệu có sẵn | 1đ |

  "Chạy ra một ví dụ" là demo, **không phải** tái hiện toàn bộ.

| File | Nội dung |
|---|---|
| [PLAN.md](PLAN.md) | Kế hoạch giai đoạn A–D, prototype, thực nghiệm, lịch tuần, phân công |
| [KNOWLEDGE.md](KNOWLEDGE.md) | Kiến thức cần học (bản cô đọng + lộ trình) |
| [CHECKLIST.md](CHECKLIST.md) | Checklist nộp và tự kiểm tra |
| [references/prompt_nhom_3.md](references/prompt_nhom_3.md) | Prompt tổng gốc của nhóm cho Claude Code/Codex (đặc tả chi tiết các giai đoạn) |
| [references/kien_thuc_can_hoc.md](references/kien_thuc_can_hoc.md) | Giải thích chi tiết kiến thức theo nhóm và danh sách đọc |

Khi bắt đầu, tạo cấu trúc mã trong thư mục này: `configs/`, `src/`, `scripts/`, `tests/`, `data/README.md`, `results/raw/`, `results/tables/`, `docs/`, `slides/`, `.env.example`, `experiment_manifest.yaml`.

**Biến nhóm cần điền:** `[ĐƯỜNG_DẪN_REPO]`, `[HẠN_NỘP]`, `[NGÂN_SÁCH_API]`, `[MODEL/API_ĐƯỢC_PHÉP]`, `[MÔI_TRƯỜNG_CHẠY]`, `[YÊU_CẦU_NỘP_BÀI]`. Máy mặc định: Mac Apple Silicon; Joern có thể cần Docker/VM.
