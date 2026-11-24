# docs/error_analysis.md — Phân tích kết quả lượt SEVEN bằng Claude Haiku

Ngày: 2026-11-24. Lượt chạy: `results/raw/seven_claude_haiku/` (166 mẫu = 83 cặp, `claude-haiku-5-5`, 1 lượt, prompt nguyên bản của repo gốc, `max_tokens` 4096). Mọi số ở đây tính lại được, không gọi model:

```bash
D="upstream/VulAgent/Quickly reproduce the experiment/seven_test_with_idx_context_cleaned.jsonl"
python3 scripts/metrics.py --gt "$D" --pred results/raw/seven_claude_haiku/predictions.jsonl --out results/tables/seven_claude_haiku
python3 scripts/analyze_errors.py --gt "$D" --run results/raw/seven_claude_haiku --out results/tables/seven_claude_haiku.errors
python3 scripts/show_trace.py results/raw/seven_claude_haiku/traces/79_L79.json
```

Số của bài báo là tham chiếu lịch sử (khác model, bài lấy trung bình 3 lượt), không phải chạy cùng điều kiện.

## 1. RQ2 — so các backend trên SVEN (83 cặp)

| Backend | Nguồn số | P-C | P-R | VPS | FPR | F1 | ACC |
|---|---|---|---|---|---|---|---|
| GPT-4o | bài báo (arXiv Table 2) | 26.51 | 6.02 | 20.49 | 55.42 | 65.62 | 60.20 |
| DeepSeek v3.1 | bài báo | 30.12 | 9.64 | 20.48 | 31.30 | 56.58 | 60.20 |
| Qwen3-235B | bài báo | 30.12 | 10.84 | 19.28 | 28.91 | 54.42 | 59.63 |
| Qwen3-235B | nhóm tính lại từ output tác giả công bố | 30.12 | 10.84 | 19.28 | 28.92 | 54.42 | 59.64 |
| **Claude Haiku 5.5** | **nhóm chạy pipeline của nhóm, 1 lượt** | **28.92** | **3.61** | **25.30** | **24.10** | **56.94** | **62.65** |

Nhận xét: kết quả Haiku nằm trong cùng vùng với ba backend của bài (ACC 60–63, P-C 27–30) và nghiêng về phía "thận trọng" giống DeepSeek/Qwen3: FPR thấp, recall thấp (49.40%). Điều này phù hợp với kết luận RQ2 của bài rằng phương pháp giữ được hành vi qua các model; nó **không** chứng minh Haiku tốt hơn, vì chỉ có một lượt và 83 cặp (chênh 1 cặp ≈ 1.2 điểm P-C).

## 2. RQ4 — theo CWE trên SVEN

`robust` = (#đúng − #sai)/#mẫu (định nghĩa ở Figure 4 của bài). Cột "bài báo" là Table 4 arXiv (GPT-4o).

| CWE | Mẫu | Prec | Rec | F1 | Acc | FPR | robust | Bài báo: Rec / FPR / Acc |
|---|---|---|---|---|---|---|---|---|
| CWE-089 | 40 | 0.667 | 0.600 | 0.632 | 0.650 | 0.300 | 0.300 | 1.000 / 0.800 / 0.600 |
| CWE-125 | 30 | 0.625 | 0.667 | 0.645 | 0.633 | 0.400 | 0.267 | 0.733 / 0.600 / 0.567 |
| CWE-078 | 22 | 0.600 | 0.273 | 0.375 | 0.545 | 0.182 | 0.091 | 0.636 / 0.455 / 0.591 |
| CWE-476 | 16 | 0.750 | 0.375 | 0.500 | 0.625 | 0.125 | 0.250 | 0.875 / 0.625 / 0.625 |
| CWE-416 | 14 | 0.667 | 0.286 | 0.400 | 0.571 | 0.143 | 0.143 | 0.571 / 0.286 / 0.643 |
| CWE-022 | 12 | 0.600 | 0.500 | 0.545 | 0.583 | 0.333 | 0.167 | 0.667 / 0.667 / 0.500 |
| CWE-787 | 12 | 0.667 | 0.667 | 0.667 | 0.667 | 0.333 | 0.333 | 0.667 / 0.333 / 0.667 |
| CWE-079 | 10 | 1.000 | 0.400 | 0.571 | 0.700 | 0.000 | 0.400 | 0.400 / 0.200 / 0.600 |
| CWE-190 | 10 | 1.000 | 0.400 | 0.571 | 0.700 | 0.000 | 0.400 | 0.800 / 0.400 / 0.700 |

Nhận xét: accuracy theo CWE gần với bài (lệch nhiều nhất 0.1), nhưng cách đạt được khác: GPT-4o trong bài báo recall cao kèm FPR cao (CWE-089: 1.000 / 0.800), còn Haiku recall thấp kèm FPR thấp. `robust` dương ở cả 9 CWE, khớp nhận định của bài rằng VulAgent "giữ điểm dương trên mọi loại". Yếu nhất là CWE-078 (command injection) và CWE-416 (use-after-free), đúng hai nhóm bài xếp vào loại "khó lập giả thuyết / phụ thuộc context". Mỗi CWE chỉ 5–20 cặp nên từng ô có sai số lớn.

## 3. 42 ca FN bị mất ở khâu nào

| Nhóm | Số ca | idx |
|---|---|---|
| 0. Aggregator không giữ candidate nào | 7 | 11, 19, 27, 31, 95, 125, 147 |
| 1. Có candidate nhưng lệch CWE so với nhãn | 7 | 13, 35, 43, 127, 131, 133, 137 |
| 2. UnifiedPruner xóa issue đúng CWE khỏi danh sách | 6 | 15, 17, 45, 83, 93, 117 |
| 3. UnifiedPruner đánh dấu `contradicted` → FinalValidator bác | 8 | 1, 29, 63, 69, 79, 113, 149, 153 |
| 4. Output UnifiedPruner không parse được → FinalValidator bác | 6 | 5, 111, 115, 151, 159, 163 |
| 5. UnifiedPruner không bác, FinalValidator tự bác | 8 | 21, 39, 47, 53, 61, 103, 121, 139 |

**28/42 FN (nhóm 2–5) đã phát hiện đúng CWE rồi bị khâu kiểm chứng loại**; khâu phát hiện chỉ chịu trách nhiệm 14 ca. Ba cơ chế cụ thể đọc được từ trace:

1. **Luật "một giả định bị bác thì bác cả đường".** Prompt FinalValidator của repo gốc có mục *Special Cases*: giả định nào bị Pruner đánh `contradicted` thì coi đường kích hoạt là không hợp lệ. Trên các issue ghép được, Pruner `contradicted` → Validator `no` ở 92/93 trường hợp. Luật này không phân biệt giả định **cần** cho lỗ hổng với giả định phụ. Ca điển hình **idx 79** (`add_input`, `"...VALUES('{}')".format(data)`, mã nguồn còn ghi chú "deliberate security flaw"): Pruner bác giả định A4 "driver cho chạy nhiều câu lệnh trong một `execute`" (đúng: pymysql mặc định không bật) và Validator bác luôn cả SQL injection, dù chèn vào một câu lệnh vẫn thực hiện được.
2. **Thiếu bằng chứng bị coi như bị bác.** Dữ liệu ở mức hàm, không có hàm gọi. Ở **idx 61** (`reportMatch`, `"VALUES ('%s', '%s')" % (winner, loser)`) Validator viết rằng "không có bằng chứng tham số do kẻ tấn công điều khiển" rồi bác; context của mẫu này là thông báo tải lỗi 404. **idx 47** bị bác vì giá trị "đến từ cấu hình do admin kiểm soát". Bài báo mô tả ngược lại: chỉ loại khi có bằng chứng mâu thuẫn, thiếu bằng chứng thì giữ ở trạng thái chưa chắc.
3. **Pruner tự xóa candidate, không để lại lý do.** Prompt yêu cầu Pruner gắn trạng thái cho giả định, nhưng ở 9 mẫu (5 FN, 4 TN) nó trả `"confirmed_issues": []`. **idx 45** (`"insert into comment_like values(%d,%d);" % (userid, commentid)`) mất theo cách này; trace không có lý do để kiểm tra lại.

**Phát hiện phụ — output Pruner bị cắt.** 40/144 output UnifiedPruner không parse được, 39 trong số đó kết thúc giữa câu ở độ dài 6–8 nghìn ký tự, phù hợp với giới hạn `max_tokens` 4096 (pipeline chưa lưu `stop_reason` nên chưa khẳng định được). Văn bản cụt vẫn được chuyển nguyên cho FinalValidator như repo gốc làm. 40 ca này rải trên TP 14, FP 7, TN 12, FN 7, nên chưa thấy nó lệch hẳn về một phía, nhưng Validator đã quyết định trên báo cáo thiếu ở 28% số mẫu có candidate. Cùng cơ chế với 28 ca FinalValidator hỏng JSON trong output Qwen3 công bố ([source_audit §7.6](source_audit.md)).

**Giới hạn của phân tích này.** Nhãn lấy theo commit vá ở mức hàm; có ca lập luận của model đứng được theo context (idx 1: `validateClient` trong context đã chặn ký tự ngoài chữ-số), nên không phải FN nào cũng là model sai. Nhóm 1 chỉ so số CWE. Chưa đọc tay đủ 42 ca; ba cơ chế trên rút từ 8 ca đã đọc (1, 5, 45, 47, 61, 79, 111, 115) cộng thống kê toàn bộ.

## 4. Ba ca dùng cho demo và báo cáo

| Vai trò | idx | Mã | Điều trace cho thấy |
|---|---|---|---|
| Cặp cơ bản (TP + TN) | 71 / 72 | `retrieve_videos_from_playlist`, SQL qua `.format()` so với truy vấn tham số hóa | 71: 4 agent → 1 candidate CWE-89 → giữ. 72: không có candidate. Hai mẫu tổng ~36 giây, chạy trực tiếp được |
| **Candidate bị guard chặn** (phương pháp làm đúng việc của nó) | 143 / 144 | `rds_tcp_kill_sock` (Linux, CWE-476); bản vá thêm `if (tc->t_sock)` | 143: giữ CWE-476 vì "không có kiểm tra `tc->t_sock` trước khi dereference". 144: vẫn nêu candidate CWE-476 nhưng bác với lý do "kiểm tra NULL ở L21 chặn dereference" |
| Như trên, ca bộ nhớ | 165 / 166 | `RemoveICCProfileFromResourceBlock` (ImageMagick, CWE-787); bản vá thêm điều kiện biên trước `CopyMagickMemory` | 165: giữ CWE-787 và CWE-125. 166: bác cả hai, dẫn guard ở L38 |
| **FN do khâu kiểm chứng** (nhược điểm) | 79 | `add_input`, SQL injection có chủ ý | Phát hiện đúng, bị bác vì một giả định phụ (mục 3, cơ chế 1) |

Trong 24 cặp đoán đúng cả hai vế, chỉ 5 cặp có candidate đúng CWE ở vế fixed rồi bị bác (7, 101, 143, 161, 165); các cặp còn lại vế fixed không phát sinh candidate đúng CWE.

## 5. Hệ quả cho biện luận và cho phần cải tiến

- **Ưu điểm thấy được:** FPR 24.10% và P-R 3.61%; khi bản vá thêm guard rõ ràng, khâu kiểm chứng trích đúng dòng guard để bác (143/144, 165/166).
- **Nhược điểm thấy được:** recall 49.40%; 2/3 số FN là lỗ hổng đã được phát hiện rồi bị loại; hai trong ba cơ chế loại nhầm trái với mô tả trong bài ("thiếu bằng chứng thì giữ").
- **Chỗ sửa cho tiêu chí 4** (chi tiết ở [PLAN.md](../PLAN.md) §0.2): (a) chỉ bác đường khi giả định bị bác là điều kiện cần để tới sink; (b) thiếu bằng chứng về nguồn dữ liệu thì giữ, không bác; (c) Pruner không được xóa issue; (d) nâng `max_tokens` cho Pruner và lưu `stop_reason`. Trần cải thiện về lý thuyết: 22 FN ở nhóm 2, 3, 5 (thêm 6 ca nhóm 4 nếu sửa cắt cụt); cái giá phải đo là FPR tăng trên 63 TN, trong đó 48 TN hiện được loại ở chính khâu này.

Pilot khóa trước trên 56 mẫu cho kết quả **âm**. V2 cứu 26/28 FN và làm 19/28 TN thành FP theo nhãn SEVEN, vượt giới hạn 2 TN.

| Phương án | FN → TP (28 mẫu) | TN → FP (28 mẫu) | P-C (12 cặp đủ) | Cả hai vế vulnerable | VPS trên 12 cặp |
|---|---:|---:|---:|---:|---:|
| Haiku gốc | 0 | 0 | 0 | 0 | 0% |
| Giữ mọi candidate | 28 | 19 | 1 | 11 | 8,33% |
| Kiểm chứng v2 | 26 | 19 | 1 | 11 | 8,33% |

Trong đối chiếu hậu nghiệm, quy tắc “giữ mọi candidate” dự đoán vulnerable nếu Aggregator đã lưu ít nhất một candidate. Dự đoán của quy tắc này trùng với v2 ở **54/56 mẫu**. Hai mẫu khác là FN 45 và 121 mà v2 vẫn bác hết. Trên cả 12 cặp đủ hai vế, hai phương án cho cùng dự đoán. So với Haiku gốc, 11 cặp chuyển từ cả hai benign sang cả hai vulnerable. Chỉ cặp 39/40 được dự đoán đúng cả hai vế. Cả ba phương án có P-R bằng 0. Các cặp được chọn theo lỗi của đối chứng nên các tỷ lệ này chỉ mô tả tập pilot. [Bảng kết quả pilot, mục `post_hoc`](../results/tables/seven_claude_haiku_verification_v2_pilot.json)

Validator trả 117 phán quyết giữ và 13 phán quyết bác ở mức issue. Bước kiểm tra trích dẫn không đổi phán quyết nào. Trên 47 mẫu có candidate, output Pruner gốc có 6 ca không parse được. V2 parse được cả 47 và API báo `end_turn` ở cả 47. V2 dùng lại candidate sau Aggregator và thay báo cáo TriggerPlanner bằng đánh giá tĩnh. Thí nghiệm đo hiệu ứng tổng hợp của thiết kế kiểm chứng trên danh sách candidate cố định, gồm thay đổi đầu vào, prompt và trần token.

## 6. RQ3 — có và không có code context trên SVEN (83 cặp)

Lượt không context: `results/raw/seven_claude_haiku_noctx/` (166 mẫu, `claude-haiku-5-5`, mã commit `3b4a4d1`, prompt gốc, `--skip context`; 165 mẫu chạy thành 6 tiến trình song song, idx 1 từ lượt tuần tự trước). Lần chạy đầu có 2 mẫu `unknown`: idx 159 (FinalValidator trả rỗng, `stop_reason=max_tokens`) và idx 79 (Aggregator không parse được). Hai mẫu này được chạy lại riêng một lần bằng đúng mã `3b4a4d1`; bản ghi lỗi còn trong `results/raw/seven_claude_haiku_noctx_parts/`. Chi phí: 1.535 lời gọi, 5,83M token vào và 1,82M token ra, thêm 16 lời gọi (48k vào, 19k ra) của hai lần lỗi.

```bash
python3 scripts/metrics.py --gt "$D" --pred results/raw/seven_claude_haiku_noctx/predictions.jsonl --out results/tables/seven_claude_haiku_noctx
```

Cột: P-C / P-R / VPS / FPR / F1 / ACC (%).

| Lượt | Không context | Có context |
|---|---|---|
| Bài báo, GPT-4o, SVEN (Table 3 arXiv) | 20.48 / 7.20 / 13.25 / 60.00 / 63.27 / 56.63 | 26.51 / 6.02 / 20.48 / 55.42 / 65.62 / 60.20 |
| Nhóm, Haiku, 1 lượt | **34.94 / 6.02 / 28.92 / 24.10 / 59.86 / 64.46** | 28.92 / 3.61 / 25.30 / 24.10 / 56.94 / 62.65 |

Mức mẫu: không context TP 44 FP 20 FN 39 TN 63; có context TP 41 FP 20 FN 42 TN 63.

**Kết luận hiện tại: chưa tách được hiệu ứng của context khỏi biến thiên giữa các lượt chạy.** Với Haiku, bỏ context làm VPS tăng 3,6 điểm, trong khi bài báo ghi giảm 7,2 điểm. Lý do chưa kết luận:

- Giữa hai lượt có 23 mẫu đổi phán quyết (13 mẫu chuyển sang vulnerable, 10 mẫu chuyển sang benign; McNemar chính xác p ≈ 0,68). Theo cặp, 12 cặp mới thành P-C và 7 cặp mất P-C (p ≈ 0,36). Giá trị p chỉ nói chênh lệch nhỏ, không nói chênh lệch đến từ nguồn nào.
- Trong pipeline, context chỉ đi vào **UnifiedPruner** (`{code_context}`). Các agent trước Aggregator (MetaAgent và agent phát hiện) nhận prompt giống hệt nhau ở hai lượt, nhưng output vẫn khác: xét lời gọi đầu tiên của mỗi agent trên mỗi mẫu, 927 cặp lời gọi trùng hash prompt thì 671 cặp khác văn bản output (Codex đếm theo cách lọc khác ra 634/761, cùng kết luận). Backend Anthropic không đặt `temperature`, nên hai lượt khác nhau do cả context lẫn nhiễu ngẫu nhiên của model, và một lượt mỗi bên không tách được hai nguồn.
- Bài báo dùng GPT-4o và lấy trung bình 3 lượt; FPR của bài (55–60%) khác hẳn Haiku (24%), nên chỉ so được chiều thay đổi, không so được độ lớn.

Cách tách hiệu ứng context khỏi nhiễu: (a) giữ nguyên output MetaAgent → TriggerPlanner của lượt có context, chỉ chạy lại Pruner + Validator với context rỗng, khoảng 2 lời gọi mỗi mẫu có candidate; hoặc (b) chạy thêm một lượt có context để đo mức dao động giữa hai lượt cùng cấu hình. **Người dùng chọn (a) ngày 2026-11-24**; kết quả ghi ở mục 7 khi chạy xong.

## 7. RQ3 tách biến (a) — giữ nguyên phần đầu pipeline, chỉ đổi context

Lượt `results/raw/seven_claude_haiku_noctx_prefix/` (mã commit `59039d3`, `--skip context --reuse-prefix-from results/raw/seven_claude_haiku`). Output MetaAgent → TriggerPlanner được phát lại nguyên văn từ trace của lượt có context (hash prompt kiểm từng lời gọi; phát lại offline cả 166 trace tái tạo đúng 166/166 phán quyết). Chỉ UnifiedPruner và FinalValidator được gọi lại, với `{code_context}` = `{}`. 22 mẫu không có candidate không gọi API. Chi phí: 288 lời gọi + 4 lời gọi chạy lại 2 mẫu `unknown`; 1,68M token vào, 0,70M token ra. Idx 159 chạy lại thì có kết quả; idx 161 vẫn `unknown` (Validator chạm `max_tokens`), để nguyên.

```bash
python3 scripts/metrics.py --gt "$D" --pred results/raw/seven_claude_haiku_noctx_prefix/predictions.jsonl --out results/tables/seven_claude_haiku_noctx_prefix
```

Cột: P-C / P-R / VPS / FPR / F1 / ACC (%).

| Lượt | Số liệu |
|---|---|
| Có context (gốc) | 28.92 / 3.61 / 25.30 / 24.10 / 56.94 / 62.65 |
| (a) Không context, phần đầu giữ nguyên | 30.49 / 1.22 / **29.27** / 26.51 / 60.40 / 64.24 (82 cặp; tính cặp thiếu là sai: VPS 28.92) |
| Không context, chạy lại toàn bộ (§6) | 34.94 / 6.02 / 28.92 / 24.10 / 59.86 / 64.46 |

So với lượt có context, (a) đổi phán quyết ở 19 mẫu (13 benign → vulnerable, 6 vulnerable → benign; McNemar p ≈ 0,17), ít hơn 23 mẫu của lượt chạy lại toàn bộ dù chỉ còn hai khâu có thể dao động. Chiều thay đổi nhất quán ở cả hai lượt không context: **bỏ context làm Pruner ít đánh dấu `contradicted` hơn** (189 → 154 ở (a), 159 ở §6; nhãn `unknown` tăng 191 → 225 và 217), nên Validator bác ít hơn, recall và FPR cùng tăng nhẹ, VPS gần như không đổi.

Kết luận dùng cho báo cáo: với Haiku, context chủ yếu giúp Pruner **bác** giả định; trong pipeline này điều đó đổi thêm cả TP lẫn FP thành benign, nên không cải thiện VPS như bài báo ghi với GPT-4o. Bằng chứng vẫn là một lượt mỗi nhánh và Pruner/Validator tự dao động, nên đây là xu hướng, chưa phải kết luận thống kê.

Phát hiện phụ: lượt này lưu `stop_reason`. **37/144 output Pruner gốc kết thúc vì `max_tokens`** (4096), xác nhận giả thuyết ở §3 rằng output Pruner không parse được là do bị cắt cụt.
