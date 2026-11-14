# docs/reproduction_plan.md — Kế hoạch tái hiện thí nghiệm VulAgent (Giai đoạn C, chia nhỏ)

Ngày: 2026-11-06. Gắn với tiêu chí chấm #3 (5đ) và #4 (1đ) trong [../README.md](../README.md).
Căn cứ mã đã audit: [source_audit.md](source_audit.md). Mức tái hiện: xem [reproduction_contract.md](reproduction_contract.md).

---

## 1. "Tái hiện thí nghiệm" nghĩa là gì ở đồ án này

Thang điểm (bài báo **có mã công khai**):

| # | Tiêu chí | Điểm | Nghĩa cụ thể cho VulAgent |
|---|---|---|---|
| 3 | Hiện thực & demo: **tái hiện các thí nghiệm trong bài** + biện luận ưu/nhược | **5đ** | Chạy lại pipeline trên **đúng dữ liệu/metric của paper**, ra **bảng số** tính-lại-được, rồi phân tích vì sao đúng/sai |
| 4 | Điểm cộng xuất sắc | 1đ | Một thí nghiệm **mới**: dữ liệu mới, hoặc cải tiến pipeline, có đối chứng |

**Phân biệt bắt buộc (quy tắc trung thực):**
- ✅ **Tái hiện** = chạy lại thí nghiệm, tạo bảng metric từ dự đoán của chính mình, so với số của paper và **giải thích chênh lệch**.
- ⚠️ **Demo** = chạy ra một ví dụ (một cặp). **KHÔNG tính** là tái hiện toàn bộ — chỉ là bước M2.
- ❌ **Trích số của paper** = "tham chiếu lịch sử", KHÔNG phải mình chạy ra. Chỉ được dùng để đối chiếu, phải ghi rõ nguồn.
- Không hứa trùng khít số của paper: khác model (ta dùng Qwen, paper chính nhiều chỗ GPT-4o), khác lượt chạy, khác ngân sách → ghi mọi khác biệt.

## 2. Các thí nghiệm trong paper cần tái hiện (phạm vi mục tiêu)

| Thí nghiệm | Dữ liệu | Có trong repo? | Ghi chú |
|---|---|---|---|
| E1 — VulAgent trên **PrimeVul** | 435 cặp (870 mẫu) | ✅ data + `Vulagent_primevul/ChatGPT4o/` | Metric sample-level + pair-level |
| E2 — VulAgent trên **SEVEN/SVEN** | 166 mẫu (~83 cặp) | ✅ data + `VulAgent_Seven/` + `Quickly reproduce/` (Qwen) | Entrypoint 1 lệnh rẻ nhất |
| E3 — **Baseline** cùng backend | như trên | một phần: `Ablation_study_RQ5/` (VulTrial, Direct Eval) | one-shot/CoT phải tự viết cho công bằng |
| E4 — **Ablation RQ5** | tập con | ✅ `Ablation_study_RQ5/` (+ kết quả JSON có sẵn) | bỏ 1 thành phần / oracle-CWE |

Số liệu paper (P-C/P-R/VPS…): đã điền vào `experiment_manifest.yaml::paper_facts` (2026-11-09), **định nghĩa lấy theo bản ACL (primary)**. ✅ Xung đột định nghĩa P-R **đã chốt**: ACL = nhãn đảo (vuln→benign & fixed→vuln) → `metrics.py` đúng (xem [source_audit §7.5](source_audit.md)).

## 3. Phát hiện quan trọng về METRIC (quyết định cách chia việc)

Đọc mã cho thấy **không file nào trong repo tự xuất đủ bảng metric của paper**:

- `Quickly reproduce/VulAgent-Qwen.py::compute_metrics(pred,gt)` → chỉ **sample-level**: TP/FP/FN/TN, Precision, Recall, F1, Accuracy, FPR, FNR. Ghép pred↔gt theo `idx`. ✅ đúng định nghĩa cơ bản.
- `Vulagent_primevul/ChatGPT4o/evaluate.py` → chỉ **pair-level**: both-correct, both-wrong, (1,1), (0,0), 2 chế độ (bỏ mẫu thiếu / coi thiếu là sai). Ghép cặp theo **thứ tự dòng** `2*gi, 2*gi+1`, KHÔNG theo idx.
- **P-C, P-R, VPS = P-C − P-R KHÔNG có sẵn thành hàm.** Suy ra: `both_correct` ≈ **P-C**; nếu dòng chẵn=vulnerable, dòng lẻ=fixed thì `both_wrong` ≈ **P-R** (vuln→benign & fixed→vuln). **VPS phải tự tính.**

→ **Việc offline bắt buộc:** nhóm tự viết `scripts/metrics.py` hợp nhất (sample-level + pair-level + VPS), ghép cặp **theo ID** (không theo thứ tự file), và kiểm bằng tay trên bảng nhỏ. Dùng các file `*_full.json`/`results.txt` có sẵn trong repo gốc làm fixture test — **không cần gọi LLM**.

Rủi ro cần xác minh: evaluate.py ghép cặp theo thứ tự dòng; phải xác nhận thứ tự vuln/fixed trong `primevul_test_paired.jsonl` rồi mới tin `both_wrong = P-R`.

## 4. Cơ chế chạy (đọc từ `VulAgent-Qwen.py`)

- Vòng lặp: `load_jsonl_stream` → `chunked(BATCH_SIZE=20)` → `ThreadPoolExecutor(MAX_WORKERS=6)` → `process_one`.
- `process_one`: gọi `analyse(code, name, proj, context)` (KHÔNG truyền `target` → **nhãn không lọt vào prompt** ở tầng này; vẫn phải đọc `analyse()` xác nhận). `final_vulnerability_reported` → `vuln_flag`. Ghi `idx\tvuln_flag` vào `result/results.txt` + JSON vào `correct/ | false_positives/ | false_negatives/`.
- Chi phí ∝ (số mẫu) × (số agent kích hoạt) × (token/agent). Mỗi mẫu = **nhiều** lời gọi LLM (Meta + pool static + Aggregator + TriggerPlanner + Pruner + FinalValidator). Phải dry-run để đo.

## 5. Kế hoạch chia nhỏ — các mốc C0 → C5

### C0 — Nền offline (0 đồng, KHÔNG cần key) ← làm ngay
- [x] C0.1 **(2026-11-09)** Đọc `analyse()` + `process_one()` + vòng lặp chính `VulAgent-Qwen.py`. Kết quả ([source_audit §7.1–7.2](source_audit.md)): tầng điều phối KHÔNG truyền `target` vào prompt (sạch), **NHƯNG lỗi LLM BỊ quy thành `benign` âm thầm** — `call_llm` nuốt mọi exception → chuỗi `ERROR` → Aggregator/FinalValidator trả `False` → mẫu vuln thành **FN**, không có trạng thái `unknown`. Còn mở: kiểm nội dung trường `context` (nhúng vào UnifiedPruner) + `build_context_from_jsonl.py`.
- [x] C0.2 Viết `scripts/metrics.py` (sample-level + pair-level + P-C/P-R/VPS). `--selftest` PASS; đã kiểm trên fixture output công bố của repo.
- [x] C0.3 **(2026-11-09)** Viết `src/schema.py` (validate output repo + schema đích có `unknown`). `--selftest` PASS (7/7). Quét 854 output Qwen3 PrimeVul: 854/854 đạt cấu trúc, gắn cờ đúng **3 ca "lỗi LLM→benign"** (khớp grep) gồm FN thật `vim_196578`. Validator cũng bắt lỗi "error nhưng decision=benign" cho pipeline nhóm.
- [x] C0.4 **(2026-11-09)** Đọc **cả arXiv v1 HTML và ACL PDF** (ACL qua markitdown 0.1.9). Điền `paper_facts` vào `experiment_manifest.yaml`. **✅ CHỐT định nghĩa P-R theo ACL (primary) = nhãn ĐẢO → `metrics.py` ĐÚNG, không sửa** (xem [source_audit §7.5](source_audit.md)). ACL xác nhận PrimeVul **test set = 435 cặp**, SVEN 803 cặp/9 CWE; số Table 1 VulAgent (GPT-4o) lưu verbatim; VPS=P-C−P-R kiểm khớp. Còn (không chặn): đối chiếu test IDs SEVEN.
- [x] C0.5 **(2026-11-09)** Xác minh trên dữ liệu thật ([source_audit §7.3](source_audit.md)): PrimeVul 870 dòng=**435 cặp**, SEVEN 166 dòng=**83 cặp**; cả hai xen kẽ hoàn hảo dòng-chẵn=vuln(1)/dòng-lẻ=fixed(0), cùng `commit_url` trong cặp. PrimeVul **idx khác nhau trong cặp** → ghép cặp **theo thứ tự liền kề**, KHÔNG theo idx; `build_pairs(consecutive)` của nhóm đã đúng. Còn lại: đối chiếu test IDs với PDF paper (C0.4).
- [x] C0.6 **(2026-11-09)** `shasum -a 256` 4 file dữ liệu → điền manifest; pin `openai>=1.40,<2.0` (chốt chính xác bằng `pip freeze` khi tạo `.venv` ở C1); `metrics.py`/`schema.py` chỉ cần thư viện chuẩn.
- **Nghiệm thu C0:** ✅ **XONG.** `metrics.py --selftest` PASS + khớp fixture + định nghĩa P-R đã chốt theo ACL (đúng); `schema.py --selftest` PASS + validate 854 fixture, bắt cờ benign-do-lỗi; manifest đủ số (ACL verbatim) + shasum + ước chi phí. **Còn lẻ (không chặn):** đối chiếu test IDs SEVEN; dòng Qwen3 Table 2 (nếu nhóm chạy Qwen) — làm khi cần ở C3. → **Sẵn sàng sang C1 (dry-run token) khi nhóm cấp key + ngân sách.**

### C1 — Dry-run 1 mẫu (cần key, chi phí ~vài lời gọi) ← cổng ngân sách
- [ ] C1.1 Tạo `.env` từ `.env.example`, điền `DASHSCOPE_API_KEY` riêng. Sửa 1 adapter đọc key từ env (KHÔNG dùng key nhúng).
- [ ] C1.2 Chạy đúng **1 mẫu** SEVEN qua pipeline; lưu trace + đếm **token thực tế/mẫu**.
- [ ] C1.3 Từ token/mẫu → **ước tính chi phí** cho 166 mẫu SEVEN và 870 mẫu PrimeVul (×1 và ×3 lượt). Cập nhật manifest.
- **Nghiệm thu C1:** có số token/mẫu thật + bảng ước tính chi phí → **chốt phạm vi R với nhóm**.

### C2 — Demo giải thích được (M2 của PLAN) — R4
- [ ] C2.1 Chạy **một cặp** vulnerable/fixed (1 TP + đối chiếu 1 bản fixed); lưu trace từng agent candidate→giả thuyết→kiểm điều kiện→quyết định.
- [ ] C2.2 Chạy thêm **một ca false positive bị guard chặn** để minh họa FinalValidator.
- **Nghiệm thu C2:** người khác lần ngược được từ kết luận về source/sink/guard trên 1 ca. (Đây là **demo**, chưa phải tái hiện.)

### C3 — Thí nghiệm thu nhỏ theo ID — R3
- [ ] C3.1 Chốt tập con cố định theo **ID** (vd 20–40 cặp SEVEN), lưu danh sách ID vào `configs/`.
- [ ] C3.2 Chạy full pipeline trên tập con; xuất `results/raw/*.jsonl` + per-sample JSON.
- [ ] C3.3 Chạy `scripts/metrics.py` → bảng ACC/P/R/F1/FPR/P-C/P-R/VPS **tính-lại-được**; so số paper, ghi chênh lệch.
- **Nghiệm thu C3:** bảng metric tái tạo từ file thô + giải thích khác biệt với paper.

### C4 — Tái hiện quy mô + baseline + ablation — R2/R1 (phụ thuộc ngân sách)
- [ ] C4.1 Chạy **toàn tập** đã chốt (SEVEN trước vì rẻ; PrimeVul nếu đủ ngân sách), 1 lượt (ghi rõ) hoặc 3 lượt (báo trung bình + biến thiên).
- [ ] C4.2 Baseline **one-shot/CoT cùng backend, cùng input, cùng context** (tự viết cho công bằng); Semgrep nếu kịp.
- [ ] C4.3 **Một ablation** đối chứng: bỏ UnifiedPruner HOẶC bỏ FinalValidator HOẶC bỏ context — giữ nguyên model/IDs/config. Ghi candidate count qua từng giai đoạn, TP/FP bị loại, FN phát sinh.
- **Nghiệm thu C4:** bảng so sánh full vs baseline vs ablation trên cùng tập ID.

### C5 — Error analysis + biện luận ưu/nhược (hoàn tất tiêu chí #3)
- [ ] C5.1 Phân tích **≥3 ca**: 1 TP, 1 FP đã loại nhờ kiểm chứng, 1 FN hoặc FP còn sót — chỉ source/sink/guard trên code thật.
- [ ] C5.2 Viết ưu/nhược: coverage đa agent vs chi phí token/độ trễ, FN do pruning, phụ thuộc chất lượng context & model, giới hạn nhãn.
- [ ] C5.3 Ghi threats to validity: nhiễm dữ liệu huấn luyện, cỡ mẫu, một lượt chạy, lệch backend.
- **Nghiệm thu C5:** mục biện luận + 3 ca trong báo cáo, mỗi claim trỏ được tới file/trace/số.

## 6. Phụ thuộc & thứ tự
```
C0 (offline) ──► C1 (dry-run, cần key) ──► [chốt ngân sách với nhóm]
                                              │
                        ┌─────────────────────┼───────────────┐
                        ▼                      ▼               ▼
                   C2 (demo R4)          C3 (nhỏ R3)   ... C4 (full R1/R2)
                                              └──────────────► C5 (phân tích)
```
C0 làm được **toàn bộ ngay bây giờ** mà không tốn tiền. C1 trở đi cần `DASHSCOPE_API_KEY` + `[NGÂN_SÁCH_API]` (chưa chốt).

## 7. Cần hỏi nhóm trước khi vượt C0
- `DASHSCOPE_API_KEY` riêng (hoặc endpoint+key GPT-4o cho baseline) — không suy ra được.
- `[NGÂN_SÁCH_API]` và model được phép dùng; hạn nộp đồ án.
- Ưu tiên tập nào trước: SEVEN (rẻ, 166 mẫu) hay PrimeVul (435 cặp, đúng bảng chính ACL).
