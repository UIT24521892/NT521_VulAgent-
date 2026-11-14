# Đề tài VulAgent — phát hiện lỗ hổng mã nguồn bằng lập và kiểm chứng giả thuyết

**Trạng thái (2026-11-14): xong Giai đoạn A (kiểm toán nguồn) + C0 (nền offline: metric, schema, kiểm rò nhãn, đối chiếu paper ACL); chưa chạy LLM, chưa có mã pipeline của nhóm.** Quy tắc chung: [../AGENT.md](../AGENT.md). Tài liệu: [docs/source_audit.md](docs/source_audit.md), [experiment_manifest.yaml](experiment_manifest.yaml), [docs/reproduction_contract.md](docs/reproduction_contract.md), [docs/reproduction_plan.md](docs/reproduction_plan.md) (C0–C5). Mã offline: [scripts/metrics.py](scripts/metrics.py), [src/schema.py](src/schema.py). Repo gốc clone cô lập ở `upstream/` (gitignore, không commit — có key nhúng cứng, không dùng). Bước tiếp: C1 dry-run 1 mẫu, cần key DashScope + ngân sách.

- **Paper chính:** *VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection* — [Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.928/) (mốc trích dẫn chính). Đối chiếu [arXiv 2509.11523](https://arxiv.org/abs/2509.11523). Mã công khai: https://github.com/HotFrom/VulAgent
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
