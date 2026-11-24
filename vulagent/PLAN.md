# Kế hoạch VulAgent

Nguồn: tách từ [../_archive/Huong_dan_hoc_va_thuc_hien_S01_VulAgent.md](../_archive/Huong_dan_hoc_va_thuc_hien_S01_VulAgent.md) (mục 4–6) và đặc tả chi tiết ở [references/prompt_nhom_3.md](references/prompt_nhom_3.md). Tiêu chí chấm: [REQUIREMENTS.md](REQUIREMENTS.md). **Trạng thái và thứ tự ưu tiên hiện hành ở mục 0**; nhật ký ở [../ROADMAP.md](../ROADMAP.md).

## 0. Đối chiếu tiêu chí chấm — trạng thái và thứ tự ưu tiên (cập nhật 2026-11-24)

Nguồn chuẩn: [REQUIREMENTS.md](REQUIREMENTS.md). Phần này thay cho mọi mô tả trạng thái cũ hơn ở các mục dưới. Model nhóm dùng: `claude-haiku-5-5` (paper dùng GPT-4o/Qwen3/DeepSeek) nên mọi kết quả thuộc mức **R2 — tái hiện có thay thế khai báo**.

### 0.1 Tiêu chí 3 (5đ): tái hiện các thí nghiệm trong bài + demo + biện luận

Đề giao bản arXiv; thí nghiệm bắt buộc là các RQ có trong bản arXiv. Số tham chiếu: [source_audit §7.7](docs/source_audit.md).

| Thí nghiệm của bài | Việc nhóm phải có | Trạng thái | Chi phí còn lại (ước theo SEVEN: 9.3 lời gọi, ~37k token vào/11k ra mỗi mẫu) |
|---|---|---|---|
| Kiểm chứng số công bố | Tính lại metric từ output tác giả công bố | ✅ Qwen3 SEVEN khớp cả 6 cột; Qwen3 PrimeVul khớp P-C/P-R/VPS; GPT-4o PrimeVul lệch < 0.5 điểm | 0 |
| RQ1 — VulAgent trên SVEN | Chạy đủ 83 cặp, bảng 6 metric | ✅ 1 lượt (ACC 62.65, F1 56.94, FPR 24.10, P-C 28.92, P-R 3.61, VPS 25.30) — [seven_claude_haiku.json](results/tables/seven_claude_haiku.json) | 2 lượt nữa nếu muốn "3 lượt" như ACL: ~2 × lượt đã chạy |
| RQ1 — baseline CoT cùng model, cùng ID | Viết `--mode cot` (1 lời gọi/mẫu, cùng context) + chạy SEVEN | ❌ chưa có mã | rất rẻ: 166 lời gọi |
| RQ1 — VulAgent trên PrimeVul | Chạy 435 cặp hoặc tập con có quy tắc công khai | ❌ chưa chạy | toàn bộ ≈ 5.2 × lượt SEVEN; tập con 100 cặp ≈ 1.2 × |
| RQ2 — nhiều backend | Không chạy lại 3 model của bài; thay bằng: số công bố Qwen3/GPT-4o tính lại + Haiku của nhóm | ⚠️ đủ dữ liệu, chưa viết thành bảng | 0 |
| RQ3 — có/không context | Chạy SEVEN với `--skip context` | ❌ chưa chạy (mã đã có) | ≈ 1 × lượt SEVEN (prompt ngắn hơn) |
| RQ4 — theo CWE | Bảng per-CWE từ lượt SEVEN đã có | ❌ `metrics.py` chưa có per-CWE | 0 |
| RQ5 — oracle-CWE | Ngoài phạm vi trừ khi còn ngân sách; ghi rõ không tái hiện | ⏸ không làm | — |
| Ablation bỏ Pruner / bỏ FinalValidator | **Chỉ có ở ACL** (Table 2), không bắt buộc theo đề; `--skip pruner` đã có, bỏ FinalValidator chưa có | ⏸ tùy ngân sách | ≈ 1 × lượt SEVEN mỗi cấu hình |
| Demo | Chạy trực tiếp cặp 71/72 (~36 giây) + mở trace; có video dự phòng; thêm 1 ca candidate bị guard chặn lấy từ trace sẵn có | ⚠️ chạy được; chưa có kịch bản và video | 0 |
| Biện luận ưu/nhược | ≥ 3 ca (TP, FP bị loại, FN) trỏ vào code thật + ưu/nhược + threats | ❌ chưa viết | 0 |

**Thứ tự làm (điểm/chi phí cao nhất trước):** (1) per-CWE + bảng RQ2 + chọn ca demo + error analysis — 0 đồng; (2) baseline CoT trên SEVEN; (3) SEVEN không context (RQ3); (4) PrimeVul tập con; (5) lượt 2–3 của SEVEN; (6) ablation ACL.

### 0.2 Tiêu chí 4 (1đ): cải tiến có đối chứng

Căn cứ từ lượt Haiku trên SEVEN (tính từ `stage_counts` trong `predictions.jsonl`, 2026-11-24): trong **42 FN**, **35 ca có candidate nhưng bị loại hết ở khâu kiểm chứng**, chỉ 7 ca không phát hiện được candidate nào. Tức điểm yếu chính là **loại nhầm lỗ hổng thật**, không phải bỏ sót khi phát hiện (recall 49.40%, 39/83 cặp bị đoán cả hai vế là benign).

- **Hướng chọn (đề xuất): cải tiến khâu kiểm chứng để giảm loại nhầm**, thực nghiệm trên dữ liệu có sẵn (SEVEN) — khớp nhánh "cải tiến phương pháp và thực nghiệm trên kịch bản/dữ liệu có sẵn".
- **Giả thuyết:** nếu chỉ cho phép loại một giả thuyết khi khâu kiểm chứng **trích được dòng mã/guard cụ thể** làm bằng chứng (thiếu bằng chứng thì giữ), recall và P-C tăng mà FPR không tăng quá mức.
- **Đối chứng:** lượt SEVEN đã có (cùng model, cùng 166 ID, cùng context). **Tiêu chí thành công ghi trước khi chạy:** VPS tăng và số FN "bị loại hết" giảm, FPR tăng không quá 10 điểm. Không đạt thì báo cáo là kết quả âm.
- **Việc trước khi viết mã (0 đồng):** đọc 35 trace FN để xác định bị loại ở Pruner hay FinalValidator và với lý do gì; từ đó chốt đúng chỗ sửa.
- **Phương án thêm nếu còn thời gian:** dữ liệu mới (cặp vá CVE gần đây) — tốn công gán nhãn, làm sau.

### 0.3 Tiêu chí 1–2 (4đ)

Slide và báo cáo: bối cảnh/vấn đề; phương pháp theo 4 giai đoạn kèm một trace thật; bảng khác biệt arXiv ↔ ACL ([source_audit §7.7c](docs/source_audit.md)). ❌ Chưa dựng.

## 1. Đọc paper để hiểu phương pháp

Thứ tự: **hình kiến trúc → một ví dụ xuyên suốt → nhiệm vụ và input/output từng agent → thiết kế dữ liệu/metric → kết quả/ablation → phụ lục prompt**. Cả nhóm trả lời bằng một mẫu mã duy nhất:

1. Agent phân tích phát hiện sink nào và nêu nghi vấn gì?
2. TriggerPlanner xây điều kiện và đường kích hoạt ra sao?
3. AssumptionPruner kiểm tra giả định nào bằng context nào?
4. FinalValidator xem guard/cơ chế bảo vệ nào trước kết luận?
5. Nếu context thiếu, kết luận có thể sai theo hướng nào?

Tên giai đoạn, schema, cách chia dữ liệu, metric phải trích đúng **phiên bản paper đã chọn**. Có chỗ P-R và split SVEN khác nhau giữa arXiv và ACL: đối chiếu tài liệu **và** code trước khi lập báo cáo.

## 2. Prototype tối thiểu

- Input: một đơn vị mã + context, có ID ổn định; nhãn thật chỉ biết ở bước đánh giá.
- Output: sink, CWE nghi vấn, điều kiện giả thuyết, trigger path, chứng cứ/guard, quyết định cuối, trạng thái `unknown` khi thiếu dữ liệu.
- Kiểm tra JSON schema; log lỗi parse riêng, **không biến output lỗi thành `benign`**.
- Chạy một cặp vulnerable/fixed từ đầu tới cuối, lưu output từng bước.
- Ghi model/prompt/config/ngày chạy, token hoặc chi phí; không đưa API key vào repo/log.

**Mốc hoàn thành:** người khác mở một ca và lần ngược từ kết luận về source, sink, guard và bằng chứng.

## 3. Các giai đoạn (đặc tả đầy đủ trong prompt gốc)

| Giai đoạn | Nội dung | Đầu ra chính |
|---|---|---|
| A — Kiểm toán nguồn, khóa giao thức | Đọc repo gốc, đối chiếu 2 bản paper, tìm key nhúng, khóa manifest | `docs/source_audit.md`, `experiment_manifest.yaml`, `docs/reproduction_contract.md` |
| B — Hiện thực/chuẩn hóa pipeline | MetaAgent → Detection → Aggregator → TriggerPlanner → AssumptionPruner → FinalValidator → Output JSON | Mã chạy một cặp, trace trung gian, demo |
| C — Tái hiện thực nghiệm | 435 cặp PrimeVul (ACL), SVEN 803 cặp (paper ghi split 9:1 train/validation, không nêu test; repo dùng 83 cặp — chưa đối chiếu được test IDs), baseline one-shot/CoT cùng backend, metric, ablation | Kết quả thô JSONL/CSV, script metric, bảng, log chi phí |
| D — Điểm cộng, biện luận | Cải tiến khâu kiểm chứng để giảm loại nhầm (mục 0.2); dữ liệu mới nếu còn thời gian | Thí nghiệm đối chứng; mục ưu/nhược/giới hạn |

Điểm bắt buộc nhớ:

- Phân tích hai vế vulnerable/fixed **độc lập**; không rò nhãn/bản fixed vào prompt.
- TriggerPlanner không tự loại đường vì thấy guard; AssumptionPruner chỉ loại khi có chứng cứ mâu thuẫn; FinalValidator bác bỏ khi protection chặn **mọi** đường khả thi.
- Phân biệt `candidate`, `retained hypothesis`, `confirmed by ground truth`.
- Số trích từ paper là **tham chiếu lịch sử**, không phải chạy cùng điều kiện. CWE oracle chỉ dùng ở thí nghiệm `oracle-CWE` riêng.
- Metric: ACC, precision, recall, F1, `FPR = FP/(FP+TN)`, P-C, P-R, `VPS = P-C − P-R`; theo ACL 2026, P-R là cặp bị đảo nhãn (vulnerable→benign và fixed→vulnerable). Kiểm tra bằng bảng TP/FP/TN/FN tính tay; sample-level map dự đoán↔nhãn theo `idx`; pair-level ghép theo hai dòng liền kề của file ground-truth (PrimeVul có idx khác nhau trong cặp và 2 idx trùng — xem [docs/source_audit.md](docs/source_audit.md) §7.3).
- Ablation: bỏ đúng một thành phần (AssumptionPruner, FinalValidator hoặc context), giữ nguyên model, IDs, config.
- Phân tích ≥ 3 ca: TP, FP đã loại nhờ kiểm chứng, FN hoặc FP còn sót; chỉ ra source/sink/guard trên code thật.
- Ghi giới hạn: chất lượng nhãn, thiếu context, nhiễm dữ liệu huấn luyện, biến động model, cỡ mẫu.

Mốc: **M1** audit + manifest + ước lượng ngân sách; **M2** demo pipeline một cặp + trace; **M3** baseline + full pipeline cùng tập; **M4** ablation/điểm cộng; **M5** báo cáo, slide, tập thuyết trình.

Nếu thiếu API/chi phí: hoàn thành toàn bộ phần ngoại tuyến (audit, chuẩn dữ liệu, schema, metric, baseline script, demo với đầu ra có provenance), ghi trạng thái rõ, hỏi đúng quyền còn thiếu.

## 4. Lịch tuần (tuần 2–7 theo hướng dẫn gốc)

| Tuần | Học và làm | Đầu ra kiểm tra được | Xong |
|---|---|---|---|
| 2 | Đọc hình kiến trúc + một ví dụ trong paper; bắt đầu audit repo; thử Joern trong Docker | Sơ đồ luồng VulAgent bằng lời nhóm | [ ] |
| 3 | Dựng repo Python, schema, pipeline chạy một cặp vuln/fixed | Log đầy đủ một cặp qua từng giai đoạn | [ ] |
| 4 | Chốt dữ liệu, IDs, baseline, công thức metric; kiểm tra rò rỉ nhãn | Manifest mẫu, script metric kiểm tra tay, bảng baseline đầu | [ ] |
| 5 | Chạy thí nghiệm chính theo cấu hình đã khóa; theo dõi log, token, lỗi | Bảng kết quả tính lại được từ file dự đoán | [ ] |
| 6 | Ablation, phân tích FP/FN, rà soát bản paper trích | Bảng ablation + 3 ca giải thích chi tiết | [ ] |
| 7 | Báo cáo, hoàn tất demo, diễn tập hỏi đáp | Báo cáo, slide, mã, manifest, kịch bản demo dự phòng | [ ] |

## 5. Phân công (VulAgent)

| Vai trò | Việc |
|---|---|
| A | Nắm luồng source–sink–guard và ý chính pipeline; review ngữ nghĩa candidate/guard |
| B (chính) | Paper, CFG/data flow, agent, JSON schema, context retrieval, mã pipeline, audit repo/key, demo |
| C (chính) | PrimeVul/SVEN, split/IDs, metric, baseline, thí nghiệm chính, ablation, error analysis, chi phí |

Ba buổi chung: (1) một cặp vulnerable/fixed; (2) guard có chặn mọi đường tới sink; (3) một FP và giả định sai. Mỗi tuần cập nhật bảng chung vào [../ROADMAP.md](../ROADMAP.md).

## 6. Tài liệu

- [VulAgent bản ACL](https://aclanthology.org/2026.findings-acl.928/), [bản arXiv](https://arxiv.org/abs/2509.11523)
- Danh sách đọc chi tiết: [references/kien_thuc_can_hoc.md](references/kien_thuc_can_hoc.md)

**Ưu tiên khi thiếu thời gian:** pipeline chạy một cặp trước; Joern/CPG, program slicing sâu, thống kê nâng cao chỉ khi phục vụ câu hỏi thực nghiệm.
