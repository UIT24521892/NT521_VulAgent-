# Đề tài VulAgent — phát hiện lỗ hổng mã nguồn bằng lập và kiểm chứng giả thuyết

**Trạng thái: chưa bắt đầu** — trọng tâm hiện tại là [seminar S05](../seminar_S05/). Quy tắc chung: [../AGENT.md](../AGENT.md).

- **Paper chính:** *VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection* — [Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.928/) (mốc trích dẫn chính). Đối chiếu [arXiv 2509.11523](https://arxiv.org/abs/2509.11523). Mã công khai: https://github.com/HotFrom/VulAgent
- **Dữ liệu:** PrimeVul, SVEN — xác định đường dẫn, phiên bản, giấy phép, split thực tế từ nguồn chính thức trước khi tải.
- **Tiêu chí chấm:** (1) hiểu bối cảnh/vai trò/vấn đề và thuyết trình; (2) giải thích phương pháp; (3) tái hiện thí nghiệm (đã có mã công khai) và biện luận ưu/nhược; (4) điểm cộng: dữ liệu/kịch bản mới hoặc cải tiến có đối chứng. "Chạy ra một ví dụ" là demo, **không phải** tái hiện toàn bộ.

| File | Nội dung |
|---|---|
| [PLAN.md](PLAN.md) | Kế hoạch giai đoạn A–D, prototype, thực nghiệm, lịch tuần, phân công |
| [KNOWLEDGE.md](KNOWLEDGE.md) | Kiến thức cần học (bản cô đọng + lộ trình) |
| [CHECKLIST.md](CHECKLIST.md) | Checklist nộp và tự kiểm tra |
| [references/prompt_nhom_3.md](references/prompt_nhom_3.md) | Prompt tổng gốc của nhóm cho Claude Code/Codex (đặc tả chi tiết các giai đoạn) |
| [references/kien_thuc_can_hoc.md](references/kien_thuc_can_hoc.md) | Giải thích chi tiết kiến thức theo nhóm và danh sách đọc |

Khi bắt đầu, tạo cấu trúc mã trong thư mục này: `configs/`, `src/`, `scripts/`, `tests/`, `data/README.md`, `results/raw/`, `results/tables/`, `docs/`, `slides/`, `.env.example`, `experiment_manifest.yaml`.

**Biến nhóm cần điền:** `[ĐƯỜNG_DẪN_REPO]`, `[HẠN_NỘP]`, `[NGÂN_SÁCH_API]`, `[MODEL/API_ĐƯỢC_PHÉP]`, `[MÔI_TRƯỜNG_CHẠY]`, `[YÊU_CẦU_NỘP_BÀI]`. Máy mặc định: Mac Apple Silicon; Joern có thể cần Docker/VM.

**Điểm nối với S01:** cách nhóm phân tích thủ công mã vulnerable/fixed ở S01 dùng để thiết kế schema đầu ra và phần giải thích của prototype. Kết quả CTF **không** là kết quả benchmark.
