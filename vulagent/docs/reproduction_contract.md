# docs/reproduction_contract.md — Hợp đồng tái hiện VulAgent

Ngày: 2026-11-06. Mục đích: nói rõ mức nào là "tái hiện", mức nào là "demo", để không claim quá tay (quy tắc trung thực AGENT.md mục 4).

## 1. Bốn mức, phân biệt rõ

| Mức | Định nghĩa | Điều kiện cần | Trạng thái hiện tại |
|---|---|---|---|
| **R1 — Tái hiện đúng cấu hình** | Chạy đúng model/dữ liệu/tham số/split của paper, báo ACC/P/R/F1/FPR/P-C/P-R/VPS trên **toàn** tập test | Key DashScope + ngân sách đủ 435 cặp PrimeVul (×3 lượt) và/hoặc SEVEN; prompt + metric đã đối chiếu paper | ❌ chưa (thiếu key/ngân sách; metric đã đối chiếu ACL 2026-11-09) |
| **R2 — Tái hiện có thay thế khai báo** | Như R1 nhưng đổi backend (vd Qwen thay GPT-4o), 1 lượt thay 3, hoặc tập con có quy tắc lấy mẫu công khai; ghi rõ mọi thay thế | Key + ngân sách vừa phải | ❌ chưa |
| **R3 — Thí nghiệm thu nhỏ** | Chạy một tập con nhỏ cố định theo ID (vd 10–20 cặp), đủ để tính bảng metric tính-lại-được, nêu rõ là mẫu nhỏ | Key + ngân sách tối thiểu | ❌ chưa — **mục tiêu khả thi đầu tiên khi có key** |
| **R4 — Demo thủ công** | Chạy pipeline trên **một** cặp vulnerable/fixed, lưu trace từng agent (candidate → giả thuyết → kiểm điều kiện → quyết định) | Key cho ~vài chục lời gọi LLM | ❌ chưa — **mốc M2 của PLAN** |

"Chạy ra một ví dụ" = R4 = demo, **không** phải tái hiện (khớp tiêu chí chấm: demo ≠ tái hiện toàn bộ).

## 2. Việc KHÔNG cần API (làm ngay, 0 đồng) — đang/đã bắt đầu

- [x] Clone + khóa commit repo gốc, cô lập trong `upstream/` (gitignore).
- [x] Audit cấu trúc, tìm key nhúng, ghi `docs/source_audit.md`, `experiment_manifest.yaml`.
- [x] (C0.2) Đọc `evaluate.py` → viết lại script metric độc lập trong `vulagent/scripts/`, kiểm bằng tay trên bảng TP/FP/TN/FN nhỏ (không cần LLM).
- [x] (C0.3) Viết parser + validator JSON schema đầu ra trong `vulagent/src/` (không cần LLM; test bằng các file `*_full.json` có sẵn trong repo gốc làm fixture).
- [x] (C0.4) Đối chiếu paper (ACL PDF + arXiv v1 HTML), điền `paper_facts` trong manifest và [source_audit §7.5](source_audit.md).
- [ ] Chuẩn hóa tập con cố định theo ID cho R3/R4 (chọn vài cặp, lưu danh sách ID).

Theo PLAN: "nếu thiếu API/chi phí, hoàn thành toàn bộ phần ngoại tuyến rồi mới hỏi quyền còn thiếu".

## 3. Đề xuất phạm vi theo ngân sách

| Nếu có | Làm tới mức | Ước lượng |
|---|---|---|
| Chưa có key | R4 offline-prep: parser, schema, metric script, chọn ID, demo khung chưa gọi LLM | 0 đồng |
| Key + ngân sách nhỏ | R4 (1 cặp) rồi R3 (10–20 cặp) trên SEVEN+context (rẻ hơn, 166 dòng) | sau dry-run 1 mẫu mới ước được token |
| Key + ngân sách khá | R2/R1 trên PrimeVul 435 cặp, ±ablation RQ5 | cần ước token/cặp trước |

## 4. Điều chỉ hỏi nhóm khi thật sự cần

- Thông tin thanh toán / `DASHSCOPE_API_KEY` (hoặc endpoint+key GPT-4o cho baseline) — không suy ra được.
- `[NGÂN_SÁCH_API]`, model được phép dùng, hạn nộp đồ án.
Mọi thứ còn lại triển khai ngoại tuyến trước, ghi trạng thái rõ.
