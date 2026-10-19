# Kế hoạch VulAgent

Nguồn: tách từ [../_archive/Huong_dan_hoc_va_thuc_hien_S01_VulAgent.md](../_archive/Huong_dan_hoc_va_thuc_hien_S01_VulAgent.md) (mục 4–6) và đặc tả chi tiết ở [references/prompt_nhom_3.md](references/prompt_nhom_3.md). **Chưa kích hoạt** — xem [../ROADMAP.md](../ROADMAP.md).

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
| C — Tái hiện thực nghiệm | 435 cặp PrimeVul (ACL), SVEN 803 cặp split 8:1:1 (xác định đúng test IDs), baseline one-shot/CoT cùng backend, metric, ablation | Kết quả thô JSONL/CSV, script metric, bảng, log chi phí |
| D — Điểm cộng, biện luận | Chọn **một** hướng: (a) context chọn lọc theo giả thuyết, (b) dữ liệu mới, (c) độ bền khi thiếu context | Thí nghiệm đối chứng; mục ưu/nhược/giới hạn |

Điểm bắt buộc nhớ:

- Phân tích hai vế vulnerable/fixed **độc lập**; không rò nhãn/bản fixed vào prompt.
- TriggerPlanner không tự loại đường vì thấy guard; AssumptionPruner chỉ loại khi có chứng cứ mâu thuẫn; FinalValidator bác bỏ khi protection chặn **mọi** đường khả thi.
- Phân biệt `candidate`, `retained hypothesis`, `confirmed by ground truth`.
- Số trích từ paper là **tham chiếu lịch sử**, không phải chạy cùng điều kiện. CWE oracle chỉ dùng ở thí nghiệm `oracle-CWE` riêng.
- Metric: ACC, precision, recall, F1, `FPR = FP/(FP+TN)`, P-C, P-R, `VPS = P-C − P-R`; theo ACL 2026, P-R là cặp bị đảo nhãn (vulnerable→benign và fixed→vulnerable). Kiểm tra bằng bảng TP/FP/TN/FN tính tay; gắn cặp theo ID, không theo thứ tự file.
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
