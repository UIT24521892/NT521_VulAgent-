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
| RQ2 — nhiều backend | Không chạy lại 3 model của bài; thay bằng: số công bố Qwen3 tính lại + Haiku của nhóm | ✅ bảng ở [error_analysis §1](docs/error_analysis.md) | 0 |
| RQ3 — có/không context | Chạy SEVEN với `--skip context` | ✅ 1 lượt (VPS 28.92 không context vs 25.30 có context; chưa tách được khỏi biến thiên giữa lượt) — [error_analysis §6](docs/error_analysis.md); ✅ lượt (a) + nhánh đo nhiễu: context làm Pruner bác nhiều hơn (13/16 mẫu đổi cùng chiều, p ≈ 0,02), không cải thiện VPS — [§7–§8](docs/error_analysis.md) | (a) 292 + nhiễu 290 lời gọi |
| RQ4 — theo CWE | Bảng per-CWE từ lượt SEVEN đã có | ✅ `metrics.py` xuất `per_cwe`; bảng ở [error_analysis §2](docs/error_analysis.md) | 0 |
| RQ5 — oracle-CWE | Ngoài phạm vi trừ khi còn ngân sách; ghi rõ không tái hiện | ⏸ không làm | — |
| Ablation bỏ Pruner / bỏ FinalValidator | **Chỉ có ở ACL** (Table 2), không bắt buộc theo đề; `--skip pruner` đã có, bỏ FinalValidator chưa có | ⏸ tùy ngân sách | ≈ 1 × lượt SEVEN mỗi cấu hình |
| Demo | Chạy trực tiếp cặp 71/72 (~36 giây) + mở trace; có video dự phòng; thêm 1 ca candidate bị guard chặn lấy từ trace sẵn có | ⚠️ đã chọn ca (71/72, 143/144, 79 — [error_analysis §4](docs/error_analysis.md)); chưa có kịch bản và video | 0 |
| Biện luận ưu/nhược | ≥ 3 ca (TP, FP bị loại, FN) trỏ vào code thật + ưu/nhược + threats | ⚠️ số liệu và ca đã có ở [error_analysis](docs/error_analysis.md); chưa viết thành mục báo cáo, chưa có threats | 0 |

**Thứ tự làm (điểm/chi phí cao nhất trước):** (1) per-CWE + bảng RQ2 + chọn ca demo + error analysis — 0 đồng; (2) baseline CoT trên SEVEN; (3) SEVEN không context (RQ3); (4) PrimeVul tập con; (5) lượt 2–3 của SEVEN; (6) ablation ACL.

### 0.2 Tiêu chí 4 (1đ): cải tiến có đối chứng

Căn cứ từ lượt Haiku trên SEVEN (tính từ `stage_counts` trong `predictions.jsonl`, 2026-11-24): trong **42 FN**, **35 ca có candidate nhưng bị loại hết ở khâu kiểm chứng**, chỉ 7 ca không phát hiện được candidate nào. Tức điểm yếu chính là **loại nhầm lỗ hổng thật**, không phải bỏ sót khi phát hiện (recall 49.40%, 39/83 cặp bị đoán cả hai vế là benign).

- **Hướng chọn (đề xuất): cải tiến khâu kiểm chứng để giảm loại nhầm**, thực nghiệm trên dữ liệu có sẵn (SEVEN) — khớp nhánh "cải tiến phương pháp và thực nghiệm trên kịch bản/dữ liệu có sẵn".
- **Giả thuyết:** nếu chỉ cho phép loại một giả thuyết khi khâu kiểm chứng **trích được dòng mã/guard cụ thể** làm bằng chứng (thiếu bằng chứng thì giữ), recall và P-C tăng mà FPR không tăng quá mức.
- **Đối chứng:** lượt SEVEN đã có (cùng model, cùng 166 ID, cùng context). **Tiêu chí thành công ghi trước khi chạy:** VPS tăng và số FN "bị loại hết" giảm, FPR tăng không quá 10 điểm. Không đạt thì báo cáo là kết quả âm.
- **Chỗ sửa đã xác định (2026-11-24, [error_analysis §3](docs/error_analysis.md)):** 28/42 FN đã phát hiện đúng CWE rồi bị khâu kiểm chứng loại, qua ba cơ chế: (a) luật *Special Cases* của FinalValidator bác cả đường khi **bất kỳ** giả định nào bị `contradicted` (idx 79); (b) thiếu bằng chứng về nguồn dữ liệu bị coi như bị bác (idx 61, 47); (c) Pruner tự xóa issue không lý do (idx 45). Có 40/144 output Pruner không parse được, trong đó 39 kết thúc giữa chừng. Lượt gốc chưa lưu `stop_reason`.
- **Giao thức khóa trước pilot (2026-11-24).** Dùng lại CWE và vị trí của toàn bộ candidate sau Aggregator từ lượt Haiku có context. V2 kiểm chứng tĩnh trên cùng hàm và context bằng hai prompt của nhóm trong [prompts_v2/](prompts_v2/). Pruner chỉ đính kèm nhận xét theo ID, có trần 8.192 token. Validator có trần 4.096 token, chỉ bác khi bằng chứng ở dòng mã cụ thể chứng minh điều kiện cần bị phủ định hoặc guard chặn mọi đường liên quan. Mẫu giữ ít nhất một candidate được tính là `vulnerable` khi chấm. Trace ghi `stop_reason` nếu backend cung cấp.
- **Pilot 56 mẫu.** Lấy đủ 28 FN nhóm 2–5 từ [bảng phân loại lỗi](results/tables/seven_claude_haiku.errors.json) và 28 TN có idx nhỏ nhất trong 63 TN của lượt đối chứng. [Danh sách ID cố định](configs/seven_verification_v2_pilot_ids.txt). Báo số FN chuyển thành TP, TN chuyển thành FP và `unknown` theo từng nhóm. Pilot đạt nếu đủ phán quyết cho 56 mẫu, số FN cứu được lớn hơn số TN chuyển sai và nhiều nhất 2 TN chuyển sai (2/28 dưới ngưỡng 10 điểm phần trăm). Pilot đo trên tập chọn theo lỗi của đối chứng nên tỷ lệ của tập này chỉ dùng để quyết định có mở rộng.
- **Đánh giá đủ 166 mẫu.** Chỉ mở rộng khi pilot đạt và đã duyệt ngân sách lượt đầy đủ. So với mốc VPS 25,30%, FPR 24,10%, 35 FN có candidate bị bác hết. Đạt khi VPS tăng, số FN có candidate bị bác hết giảm và FPR tăng tối đa 10 điểm phần trăm. Báo kết quả âm khi đủ dữ liệu và không đạt ngưỡng, hoặc chưa kết luận khi còn `unknown` hay thiếu mẫu.
- **Giới hạn đối chứng.** V2 dùng lại candidate đã lưu và dùng nhận xét tĩnh thay cho báo cáo TriggerPlanner gốc. So sánh đo hiệu ứng của cả thiết kế kiểm chứng trên cùng candidate. Không quy thay đổi chỉ cho từng luật prompt hay trần token. Pilot lấy mẫu theo lỗi đã thấy và lượt đầy đủ vẫn dùng cùng benchmark đã phân tích.
- **Kết quả pilot (2026-11-24).** Haiku chấm đủ 56/56 mẫu, cứu 26/28 FN và đổi 19/28 TN thành FP. Ngưỡng đã khóa là tối đa 2 TN chuyển sai, nên pilot cho kết quả âm và dừng trước lượt 166 mẫu. Đối chiếu hậu nghiệm cho thấy v2 trùng quy tắc giữ mọi candidate ở 54/56 mẫu và cả 12 cặp đủ hai vế. Pruner ghi `end_turn` ở cả 47 lần gọi. Tổng lượt pilot là 94 lời gọi, 327.491 token vào và 91.173 token ra. [Bảng kết quả pilot](results/tables/seven_claude_haiku_verification_v2_pilot.json) · [Phân tích theo cặp](docs/error_analysis.md#5-hệ-quả-cho-biện-luận-và-cho-phần-cải-tiến)
- **Phương án thêm nếu còn thời gian:** dữ liệu mới (cặp vá CVE gần đây) — tốn công gán nhãn, làm sau.

### 0.3 Tiêu chí 1–2 (4đ)

Slide và báo cáo: bối cảnh/vấn đề; phương pháp theo 4 giai đoạn kèm một trace thật; bảng khác biệt arXiv ↔ ACL ([source_audit §7.7c](docs/source_audit.md)). ❌ Chưa dựng.

### 0.4 Bàn giao việc cho thành viên (cập nhật 2026-11-25)

Mục này là danh sách việc để chia cho cả nhóm. Mỗi việc có người phụ trách theo vai trò ở [mục 5](#5-phân-công-vulagent), đầu vào, các bước, đầu ra và điều kiện xong. Nhận việc nào thì ghi tên vào cột "Người nhận" trong bảng dưới rồi commit. Xong việc thì tick [CHECKLIST.md](CHECKLIST.md) và thêm một dòng nhật ký vào [../ROADMAP.md](../ROADMAP.md).

**Tóm tắt trạng thái lúc bàn giao.** Mọi commit đã lên `origin/main` (`268605c`). Đã có RQ1 trên SEVEN (1 lượt), RQ2, RQ3 (3 nhánh), RQ4, phân tích lỗi và pilot cải tiến cho kết quả âm. Bảng nằm trong `results/tables/` và tính lại được từ kết quả thô. Đã thử lại ngày 2026-11-25: `metrics.py` trên `results/raw/seven_claude_haiku/predictions.jsonl` cho ra đúng `seven_claude_haiku.json`. Còn thiếu baseline CoT, PrimeVul, kịch bản demo, phần biện luận và toàn bộ báo cáo/slide.

| Việc | Vai trò chính | Người nhận | Tốn phí API? | Phụ thuộc | Trạng thái |
|---|---|---|---|---|---|
| T0 Chia sẻ kết quả thô + chốt thông tin nhóm | người đang giữ máy chạy | `[CHƯA CHỐT]` | không | — | ❌ |
| T1 Dựng môi trường và kiểm tra tái lập | mỗi thành viên | cả nhóm | không | T0 | ❌ |
| T2 Baseline CoT (RQ1) | B viết mã, C chạy và chấm | `[CHƯA CHỐT]` | có, ~166 lời gọi | T1 | ❌ |
| T3 PrimeVul tập con 100 cặp (RQ1) | C | `[CHƯA CHỐT]` | có, ~1.850 lời gọi | T1 | ❌ |
| T4 Kịch bản demo + video dự phòng | A | `[CHƯA CHỐT]` | ~10 lời gọi khi quay | T0 | ❌ |
| T5 Biện luận: ≥ 3 ca + ưu/nhược + threats | A + C | `[CHƯA CHỐT]` | không | T0 | ❌ |
| T6 Review chéo phân tích RQ3 và pilot v2 | người không viết phần đó | `[CHƯA CHỐT]` | không | T0 | ❌ |
| T7 Báo cáo + slide | B (khung), cả nhóm viết | `[CHƯA CHỐT]` | không | T2, T3, T5 cho số cuối | ❌ |
| T8 Quyết định RQ5, ablation, lượt 2–3 | C, cả nhóm duyệt | `[CHƯA CHỐT]` | tùy quyết định | T2, T3 | ❌ |

Thứ tự đề xuất: T0 → T1 ngay. Sau đó T2, T4, T5, T6 chạy song song. T3 làm khi đã duyệt ngân sách. T7 dựng khung ngay, điền số cuối khi có T2/T3.

**Quy tắc chung cho mọi việc.** Lượt gọi API tốn phí phải được nhóm đồng ý trước, nêu số mẫu và ước lượng token. Chạy thử `--limit 2` trước khi chạy cả tập. Không commit `.env`, `results/raw/`, `data/`, `upstream/`. Mỗi lượt chạy giữ `run_meta.json` và ghi lệnh, commit, ngày, chi phí vào nhật ký ROADMAP. Số của paper chỉ là tham chiếu lịch sử; mọi bảng của nhóm ghi rõ model `claude-haiku-5-5` và số lượt.

#### T0 — Chia sẻ kết quả thô và chốt thông tin nhóm

`results/raw/` bị gitignore nên các thành viên khác chưa có trace. Không có trace thì không làm được T4, T5, T6.

1. Trên máy đang giữ kết quả, từ thư mục `vulagent/`: `zip -r vulagent_raw_2026-11-24.zip results/raw/seven_claude_haiku* results/raw/demo_seven_pair_71_72 results/raw/dryrun_claude_71` (khoảng 37 MB; bỏ `replay_*` vì ai cũng tự tạo lại được offline). Ghi `shasum -a 256` của file zip.
2. Đưa file zip lên thư mục chung của nhóm, không đưa lên GitHub. Ghi link và shasum vào dòng nhật ký ROADMAP.
3. Chốt và điền vào [../AGENT.md](../AGENT.md) mục 6 và [../ROADMAP.md](../ROADMAP.md) dòng đầu: tên A/B/C, hạn nộp, ngày thuyết trình, ngân sách API còn lại, ai giữ key.
4. Bỏ hai dòng thừa ở cuối `vulagent/.env.example`, chưa commit, nếu không cố ý thêm: `git checkout vulagent/.env.example`.

**Xong khi:** link + shasum có trong nhật ký; bảng trên có tên người nhận.

#### T1 — Dựng môi trường và kiểm tra tái lập

Mỗi thành viên làm một lần. Đây cũng là bằng chứng cho mục "người khác clone và tạo lại bảng" trong [CHECKLIST.md](CHECKLIST.md).

```bash
git clone <repo nhóm> && cd project_521/vulagent
git clone https://github.com/HotFrom/VulAgent upstream/VulAgent
git -C upstream/VulAgent checkout 065467c        # đúng commit đã kiểm toán; KHÔNG chạy mã trong upstream (có key nhúng)
python3 -m venv .venv && . .venv/bin/activate && pip install anthropic openai
python3 -m unittest discover -s tests            # phải OK
unzip ../vulagent_raw_2026-11-24.zip             # từ T0, bung ra results/raw/
DATA='upstream/VulAgent/Quickly reproduce the experiment/seven_test_with_idx_context_cleaned.jsonl'
python3 scripts/metrics.py --gt "$DATA" --pred results/raw/seven_claude_haiku/predictions.jsonl --out /tmp/chk
diff <(python3 -m json.tool /tmp/chk.json) <(python3 -m json.tool results/tables/seven_claude_haiku.json)
python3 scripts/show_trace.py results/raw/seven_claude_haiku/traces/71_L71.json | less
```

Người chạy API thì `cp .env.example .env` và điền `ANTHROPIC_API_KEY`, `VULAGENT_MODEL=claude-haiku-5-5`, `VULAGENT_EFFORT=low`. Giữ nguyên các giá trị này để cùng điều kiện với các lượt đã chạy.

**Xong khi:** test OK, `diff` rỗng (nếu lệch, chỉ cho phép khác ở trường đường dẫn hoặc thời gian), đọc được trace 71. Ghi kết quả T1 của từng người vào nhật ký.

#### T2 — Baseline CoT cùng model, cùng ID (RQ1)

Bài so VulAgent với baseline CoT của GPT-4o và GPT-3.5 ([source_audit §7.7](docs/source_audit.md)). Nhóm phải tự viết một baseline CoT dùng cùng model, cùng 166 mẫu, cùng context để so sánh công bằng.

1. **B — viết mã.** Thêm `--mode {vulagent,cot}` vào [scripts/run_pipeline.py](scripts/run_pipeline.py) (mặc định `vulagent`) và hàm `analyse_cot()` trong [src/pipeline.py](src/pipeline.py). Mỗi mẫu gọi đúng **1 lời gọi**. Prompt đặt ở `prompts_cot/CoTAgent.txt`, gồm mã hàm đánh số dòng (`number_code`) và context (`sample.context`, rỗng khi `--skip context`). Yêu cầu model suy luận từng bước rồi trả JSON `{"decision": "vulnerable"|"benign", "cwe": "...", "reason": "..."}`. Có thể tham khảo cách hỏi trong `upstream/VulAgent/Ablation_study_RQ5/Direct_Evaluation.py`; chỉ đọc, không chạy file đó. Prompt không được chứa nhãn, CVE hay bản vá.
2. Output ghi vào `predictions.jsonl` cùng định dạng với pipeline chính để `metrics.py` và `show_trace.py` dùng được ngay. JSON hỏng hoặc thiếu `decision` thì ghi `unknown`, **không** quy về `benign`. `run_meta.json` có `prompt_sha256` của prompt CoT.
3. Thêm test offline vào [tests/test_pipeline.py](tests/test_pipeline.py) với backend giả: output hợp lệ, JSON hỏng → `unknown`, đúng 1 lời gọi mỗi mẫu.
4. **C — chạy.** Sau khi nhóm duyệt (~166 lời gọi, token vào cỡ độ dài hàm + context), chạy trước `--limit 2` rồi chạy đủ:
   `python3 scripts/run_pipeline.py --data "$DATA" --out results/raw/seven_claude_haiku_cot --backend api --provider anthropic --mode cot --confirm-paid`
   Mẫu `unknown` chạy lại đúng một lần bằng `--ids` và ghi rõ trong nhật ký.
5. Chấm: `python3 scripts/metrics.py --gt "$DATA" --pred results/raw/seven_claude_haiku_cot/predictions.jsonl --out results/tables/seven_claude_haiku_cot`.
6. Thêm bảng "VulAgent và CoT, cùng Haiku, cùng 166 ID" vào [docs/error_analysis.md](docs/error_analysis.md) (mục mới §9), cạnh số CoT GPT-4o của bài để tham chiếu.

**Xong khi:** test mới đạt; bảng có đủ 6 metric (ACC, F1, FPR, P-C, P-R, VPS) và tính lại được từ thô; nhật ký có lệnh, commit, số lời gọi, token.

#### T3 — VulAgent trên PrimeVul, tập con 100 cặp (RQ1)

Bảng chính của bài dùng PrimeVul 435 cặp. Chạy đủ tốn khoảng 5,2 lần lượt SEVEN nên đề xuất tập con 100 cặp, quy tắc chọn công khai.

1. **Dữ liệu:** `upstream/VulAgent/Dataset/PrimeVul/primevul_test_paired.jsonl`, 870 dòng = 435 cặp, dòng chẵn là vulnerable, dòng lẻ là fixed. Ghép cặp theo **thứ tự dòng**, không theo `idx`.
2. **Không lấy 100 cặp đầu**: 44/100 cặp đầu là tensorflow, trong khi cả tập chỉ 72/435. Viết `scripts/make_subset.py`: loại 4 cặp có `idx` trùng (dòng 447, 449, 655, 657, tức cặp 223, 224, 327, 328), rồi lấy ngẫu nhiên 100 cặp bằng `random.Random(521).sample(...)`, giữ thứ tự gốc. Ghi `data/primevul_subset100.jsonl` (gitignore) và danh sách số thứ tự cặp + idx vào `configs/primevul_subset100_pairs.txt` (commit). Ghi shasum file subset vào [experiment_manifest.yaml](experiment_manifest.yaml).
3. **Context:** file PrimeVul không có trường `context`, pipeline sẽ tự dùng context rỗng. Điều này khớp lượt GPT-4o PrimeVul của tác giả, vốn không dùng context ([source_audit §7.4](docs/source_audit.md)). Ghi rõ điều này trong bảng. Nếu sau này muốn có context từ `PrimeVul_context/primevul_zh_format_complete.json` thì **chỉ** được lấy `code_context`, tuyệt đối không đưa `vulnerableMethods_after` vào prompt.
4. **Chi phí:** ~9,3 lời gọi/mẫu × 200 mẫu ≈ 1.850 lời gọi, ~7M token vào, ~2,2M token ra (ước từ SEVEN; hàm PrimeVul dài hơn nên có thể cao hơn). Nhóm duyệt trước. Chạy `--limit 4` để đo token thật rồi mới chạy đủ.
5. Chạy: `python3 scripts/run_pipeline.py --data data/primevul_subset100.jsonl --out results/raw/primevul100_claude_haiku --backend api --provider anthropic --confirm-paid`. Bị ngắt thì chạy lại cùng lệnh, chương trình tự nối tiếp.
6. Chấm: `metrics.py --gt data/primevul_subset100.jsonl --pred .../predictions.jsonl --out results/tables/primevul100_claude_haiku`. Để đối chiếu cùng 100 cặp, chấm lại output Qwen3 công bố (`results/raw/replay_primevul_qwen3`) trên đúng tập con này.
7. Nếu T2 đã xong, chạy thêm CoT trên cùng tập con (~200 lời gọi).

**Xong khi:** bảng 6 metric cho Haiku trên 100 cặp, bảng Qwen3 cùng 100 cặp, file danh sách cặp đã commit, nhật ký có chi phí.

#### T4 — Kịch bản demo và video dự phòng

Ca đã chọn: cặp **71/72** (SQL injection `.format()` so với truy vấn tham số hóa, chạy thật khoảng 36 giây), ca phụ **143/144**, ca FN **79** (phát hiện đúng CWE rồi bị luật Special Cases của FinalValidator bác). Lý do chọn ở [error_analysis §4](docs/error_analysis.md).

1. Viết `docs/demo_script.md`: lệnh chạy trực tiếp 71/72 (`--ids 71,72 --backend api --provider anthropic --confirm-paid --out results/raw/demo_live`), lời thoại theo từng khâu MetaAgent → Detection → Aggregator → TriggerPlanner → Pruner → FinalValidator, chỉ vào dòng mã source/sink/guard thật trong trace (`show_trace.py`).
2. Phương án offline khi mất mạng: mở trace đã lưu của lượt chính, gồm `results/raw/seven_claude_haiku/traces/71_L71.json` và `72_L72.json`, bằng `show_trace.py`. Thư mục `demo_seven_pair_71_72` chỉ có trace 71. Thử lệnh trên máy trình chiếu trước buổi thuyết trình.
3. Thêm một ca "candidate bị guard chặn" lấy từ trace sẵn có (TN có candidate bị Validator bác đúng).
4. Quay video 3–5 phút (màn hình + lời thoại). Video để ở thư mục chung, không commit.
5. Diễn tập đủ hai lần liên tiếp, ghi thời gian.

**Xong khi:** có `docs/demo_script.md`, video và phương án offline đã thử; tick mục demo trong CHECKLIST.

#### T5 — Biện luận: ≥ 3 ca, ưu/nhược, threats to validity

Số liệu và ca đã có ở [error_analysis](docs/error_analysis.md); việc còn lại là viết thành mục báo cáo hoàn chỉnh.

1. Ba ca bắt buộc, mỗi ca trỏ vào dòng mã thật: **TP** (71), **FP bị loại nhờ kiểm chứng** (chọn một TN có candidate bị bác, xem `seven_claude_haiku.errors.json`), **FN** (79). Mỗi ca nêu source → sink → điều kiện → guard → kết luận của từng khâu.
2. Đọc tay thêm FN: hiện mới đọc 8/42. Đọc tối thiểu các FN còn lại thuộc nhóm "bị khâu kiểm chứng loại" (28 ca) và ghi cơ chế (a)/(b)/(c) theo [error_analysis §3](docs/error_analysis.md) vào một bảng.
3. Ưu điểm (có số): P-R thấp (3,61), FPR 24,10; mỗi kết luận có trace lần ngược được tới dòng mã. Chưa có ablation bỏ khâu kiểm chứng nên chưa được nói "kiểm chứng làm giảm FP" bằng số của nhóm. Nhược điểm (có số): recall 49,40, 39/83 cặp đoán cả hai vế benign, 37–40/144 output Pruner bị cắt, kết quả dao động giữa các lượt (671/927 lời gọi cùng prompt cho output khác).
4. Threats to validity: khác model với bài (R2), 1 lượt mỗi cấu hình, SEVEN chỉ 83 cặp, nhiễm dữ liệu huấn luyện, chất lượng nhãn, PrimeVul chỉ tập con, pilot v2 chọn mẫu theo lỗi.

**Xong khi:** mục §10 "Biện luận" trong `docs/error_analysis.md` (hoặc thẳng vào báo cáo) có đủ 4 phần trên; tick mục Error analysis trong CHECKLIST.

#### T6 — Review chéo

Người **không** viết phần đó đọc lại và tính lại số:

- [error_analysis §6–§8](docs/error_analysis.md) (RQ3 ba nhánh và đo nhiễu): tính lại VPS, số mẫu đổi phán quyết, p-value từ `results/raw/seven_claude_haiku*`.
- [error_analysis §5](docs/error_analysis.md) và [PLAN §0.2](#02-tiêu-chí-4-1đ-cải-tiến-có-đối-chứng) (pilot v2): chạy lại `compare_verification.py --pilot` (không tốn phí) và đối chiếu 26/28 FN cứu được, 19/28 TN chuyển sai.
- Mẫu 161 vẫn `unknown` ở nhánh (a): ghi cách xử lý trong bảng.

**Xong khi:** mỗi mục có một dòng "đã review: tên, ngày, khớp / lệch gì" trong nhật ký ROADMAP.

#### T7 — Báo cáo và slide

Tiêu chí 1–2 (4 điểm) chưa có gì. Có thể dựng khung ngay và điền số cuối sau.

1. Khung báo cáo `docs/report.md` (hoặc định dạng nhóm chốt): (1) bối cảnh và vấn đề; (2) phương pháp 4 giai đoạn kèm trace cặp 71/72; (3) khác biệt arXiv ↔ ACL và lý do lấy ACL làm mốc ([source_audit §7.7](docs/source_audit.md)); (4) cài đặt của nhóm: phần tự viết, phần dùng lại, model thay thế; (5) RQ1–RQ4 bảng số, RQ5 ghi rõ không làm và lý do; (6) cải tiến v2 với kết quả âm và đối chứng; (7) biện luận (T5); (8) tái lập: lệnh, commit, chi phí.
2. Slide 15–20 trang theo đúng thứ tự đó, mỗi bảng số ghi nguồn file trong `results/tables/`.
3. Mọi số trên slide phải trỏ được tới một file trong `results/tables/` hoặc số paper có ghi phiên bản.

**Xong khi:** báo cáo + slide nằm trong `vulagent/slides/` hoặc `docs/`, đã review chéo, tick mục tiêu chí 1–2 trong CHECKLIST.

#### T8 — Quyết định các thí nghiệm tùy chọn

Nhóm chốt và ghi lý do vào bảng §0.1:

- **RQ5 (oracle-CWE):** đề xuất không làm, ghi lý do: ngoài phạm vi ngân sách, cần CWE gốc làm đầu vào.
- **Ablation ACL** (`--skip pruner` đã có, bỏ FinalValidator chưa có mã): chỉ có trong bản ACL, không bắt buộc. Mỗi cấu hình tốn ~1 lượt SEVEN (~1.550 lời gọi).
- **Lượt 2–3 cho SEVEN:** giúp tách hiệu ứng khỏi nhiễu ở RQ3, mỗi lượt ~1.550 lời gọi.
- **Cải tiến:** giữ pilot âm làm kết quả tiêu chí 4, hoặc thử một biến thể mới với giao thức và ngưỡng ghi **trước** khi chạy, như cách §0.2 đã làm.

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
