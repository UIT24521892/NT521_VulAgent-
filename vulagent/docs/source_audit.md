# docs/source_audit.md — Kiểm toán nguồn VulAgent (Giai đoạn A)

Ngày audit: 2026-11-06. Người đối chiếu cần ghi tên khi review chéo: `[CHƯA CHỐT: A/B/C]`.

## 0. Nguồn đã kiểm

| Nguồn | Định danh | Trạng thái |
|---|---|---|
| Repo gốc | `github.com/HotFrom/VulAgent` | Đã clone `--depth 1` vào `vulagent/upstream/VulAgent` (gitignore, KHÔNG commit) |
| Commit đã khóa | `065467c5130c25addb312da69d7238582c8c93b2` ("Update README.md", 2026-05-29 08:56 +0800) | — |
| Paper ACL (mốc chính) | Findings of ACL 2026, DOI 10.18653/v1/2026.findings-acl.928 | Đã đọc PDF 2026-11-09 (qua markitdown) — xem §7.5 |
| Paper arXiv (đối chiếu) | arXiv:2509.11523 | Đã đọc bản v1 HTML 2026-11-09 (PDF không render được) — xem §7.5 |

> **Cập nhật 2026-11-14:** mục 3 và mục 5 dưới đây là ghi nhận ngày 2026-11-06; chỗ nào mâu thuẫn thì **mục 7 là kết luận hiện hành** (đã đối chiếu paper, số cặp, metric).
>
> Ghi chú trung thực (2026-11-06): bảng đối chiếu `khẳng định | arXiv/trang | ACL/trang | file/hàm repo | kết luận | mức chắc chắn` ở mục 5 **chỉ mới điền cột repo** (đọc trực tiếp mã). Hai cột paper để trống cho tới khi tải PDF — không suy từ README repo vì README có thể giản lược.

## 1. Cấu trúc repo gốc

Top-level (số file theo `git ls-files`):

| Thư mục | Vai trò | Số file |
|---|---|---|
| `Quickly reproduce the experiment/` | **Entrypoint khuyến nghị** — chạy pipeline Qwen trên SEVEN+context | 17 |
| `Vulagent_primevul/ChatGPT4o/` | Pipeline GPT-4o chạy PrimeVul | 2633 (gồm kết quả JSON) |
| `VulAgent_Seven/With contetxt/ChatGPT4o/` | Pipeline GPT-4o chạy SEVEN có context | 722 |
| `Ablation_study_RQ5/` | Ablation + baseline (VulTrial oracle, Direct Evaluation) | 528 |
| `Dataset/` | 4 tập dữ liệu (xem mục 3) | 4 |
| `Context construction tool/` | `build_context_from_jsonl.py` + dữ liệu mẫu | 3 |
| `README.md` | Hướng dẫn chạy nhanh | 1 |

**Không có `requirements.txt`, không có `LICENSE`, không có `.env`** ở bất kỳ cấp nào (đã kiểm bằng `git ls-files`). Thiếu LICENSE là rào cản pháp lý khi tái phân phối/đưa vào repo nhóm — xem mục 4.

## 2. Mã pipeline — các file Python thật (bỏ file kết quả)

| File | Backend | Vai trò |
|---|---|---|
| `Quickly reproduce the experiment/VulAgent-Qwen.py` | Qwen (DashScope) | Pipeline đầy đủ, entrypoint 1 lệnh |
| `Vulagent_primevul/ChatGPT4o/VulAgent-GPT4O.py` + `evaluate.py` | GPT-4o | Pipeline + chấm trên PrimeVul |
| `VulAgent_Seven/With contetxt/ChatGPT4o/VulAgent-GPT4O.py` | GPT-4o | Pipeline SEVEN có context |
| `Ablation_study_RQ5/VulAgent-GPT4O.py`, `Direct_Evaluation.py`, `vultrial_oracle_full.py`, `evaluate.py` | GPT-4o | Ablation RQ5 + baseline |
| `Context construction tool/build_context_from_jsonl.py` | — | Dựng trường `context` cho mỗi mẫu |

Cấu hình pipeline Qwen (đọc `VulAgent-Qwen.py`):
- `MODEL = "qwen"`, model thực `qwen3-235b-a22b-instruct-2507`, `base_url=https://dashscope.aliyuncs.com/compatible-mode/v1` (OpenAI-compatible mode của Alibaba DashScope).
- Tham số suy luận: `temperature=0.0`, `top_p=1.0`, `max_tokens=4096`, `extra_body={"enable_thinking": False}`. **Khớp mô tả paper (temperature 0, top_p 1).**
- Phụ thuộc: chỉ `openai` (ngoài stdlib). Python ≥ 3.8.
- Input mặc định `JSONL_PATH = seven_test_with_idx_context_cleaned.jsonl`; output `RESULT_DIR = result/` (`results.txt` + mỗi mẫu một JSON + `vulagent.log`).
- Agent (khớp README): MetaAgent → pool static (Analyzer, BehaviorAnalyzer, CryptoConfig, AuthFlow, FilePermission, FormatString, MemoryLayout, Concurrency, ErrorHandling, CodeInjection) → Aggregator → TriggerPlanner (tên biến `SYMBOLIC_EXECUTOR`) → UnifiedPruner → FinalValidator. 15 prompt template `.txt` trong `prompt_template/`.
- Lưu ý mã: `print(response)` in nguyên đối tượng response mỗi lần gọi (nhiễu log); hàm `call_llm` nuốt lỗi và trả chuỗi `"ERROR: LLM call failed"` — cần kiểm tra bước sau có biến lỗi này thành `benign` âm thầm không (yêu cầu PLAN mục 2).

## 3. Dữ liệu trong repo (đã có sẵn, không cần tải ngoài)

| File | Dòng | Bytes | Ghi chú |
|---|---|---|---|
| `Dataset/PrimeVul/primevul_test_paired.jsonl` | 870 | 6.03 MB | 870 dòng = **435 cặp** → khớp "435 cặp PrimeVul test" của ACL ✅ |
| `Dataset/PrimeVul_context/primevul_zh_format_complete.json` | 10 895 | 6.94 MB | **CÓ TẬP TIN NÀY** — trái với ghi chú ROADMAP 2026-11-06 "thiếu file". Cần mở kiểm nội dung; tên `_zh_` gợi ý context tiếng Trung |
| `Dataset/SEVEN/test_with_idx.jsonl` | 166 | 0.62 MB | SEVEN test, chưa có context |
| `Dataset/SEVEN_context/test_with_idx_context_cleaned.jsonl` | 166 | 1.26 MB | Bản có context; **giống hệt** file trong "Quickly reproduce" (cùng byte) |

**Lưu ý (ghi nhận cũ, ĐÃ ĐÍNH CHÍNH ở §7.3 và §7.5: file = 83 cặp; paper ghi split 9:1 train/validation và không nêu test):** paper nói SVEN/SEVEN 803 cặp split 8:1:1 → test ≈ 80 cặp (160 dòng). File test ở đây **166 dòng ≈ 83 cặp**, không khớp chính xác 80 — phải đối chiếu định nghĩa split và test IDs với paper trước khi tuyên bố "cùng tập". Chưa xác minh đây là 83 cặp hay 166 mẫu lẻ.

Schema một dòng SEVEN_context: `func_name, func, file_name, commit_url, cwe, target, idx, proj, context`.
- `target` = nhãn thật (0/1) **nằm ngay trong input** → pipeline đọc file có nhãn; phải đảm bảo nhãn KHÔNG lọt vào prompt, chỉ dùng ở bước chấm. `idx` để ghép cặp.
- ⚠️ Mẫu SEVEN là **mã Python** (vd `def getKey(client)`, cwe-022), **không phải C/C++** như README nói. Ghi rõ khác biệt này trong báo cáo.

## 4. Bí mật nhúng cứng và rào cản (BẮT BUỘC xử lý)

| Vị trí | Loại | Hành động |
|---|---|---|
| `Quickly reproduce the experiment/VulAgent-Qwen.py:23` | **KEY THẬT** DashScope `sk-699…` (README gọi là "temporary key for anonymous review") | **KHÔNG dùng, KHÔNG in giá trị.** Thay bằng `os.environ["DASHSCOPE_API_KEY"]` trong adapter của nhóm. Giả định key đã/ sẽ bị thu hồi |
| `Ablation_study_RQ5/Direct_Evaluation.py:16`, `vultrial_oracle_full.py:27`, các `VulAgent-GPT4O.py:23` | Placeholder `sk-xxx…`/`sk-REP…`, `base_url=""` | Chỉ là chỗ trống; điền endpoint + key riêng khi chạy baseline GPT-4o |

Rào cản khác:
1. **Không có LICENSE** → chưa rõ quyền tái phân phối. Giữ repo gốc ở `upstream/` (đã gitignore), không copy mã gốc vào `vulagent/src/` cho tới khi làm rõ; nhóm trích dẫn nguồn.
2. **Cần API key + ngân sách** để chạy thật: `[CHƯA CHỐT: DASHSCOPE_API_KEY]`, `[CHƯA CHỐT: NGÂN_SÁCH_API]`. Model `qwen3-235b-a22b-instruct-2507` tính phí theo token DashScope.
3. **Chưa tải 2 PDF paper** → chưa đối chiếu được số trang/bảng (cột paper mục 5 trống).
4. **Python 3.14 trên máy** mới hơn yêu cầu (≥3.8); tạo `.venv` riêng, cài `openai` pin phiên bản để tránh lệch API SDK.

## 5. Bảng đối chiếu khẳng định (điền dần)

| Khẳng định | arXiv/trang | ACL/trang | file/hàm repo | Kết luận | Mức chắc chắn |
|---|---|---|---|---|---|
| Backend Qwen = qwen3-235b-a22b-instruct-2507, temp 0 | — | — | `VulAgent-Qwen.py:19-24,54` | Đúng trong mã | Cao (đọc mã) |
| PrimeVul test = 435 cặp | — | `[CHƯA tải]` | `Dataset/PrimeVul/…paired.jsonl` (870 dòng) | 870/2=435 khớp | Cao (đếm) |
| SEVEN test split 8:1:1 → ~80 cặp | — | `[CHƯA tải]` | `Dataset/SEVEN/…` (166 dòng) | 166 dòng = **83 cặp** (đã xác minh C0.5); vẫn lệch ~3 cặp so với "~80" của paper | Trung bình — số cặp chắc, còn đối chiếu test IDs |
| 15 agent theo pipeline | — | `[CHƯA tải]` | `prompt_template/*.txt` (15 file) | Khớp số lượng | Trung bình |
| Phân tích vuln/fixed độc lập, không rò nhãn vào prompt | — | `[CHƯA tải]` | `VulAgent-Qwen.py` `analyse()`+`process_one()` | **Xác nhận ở tầng điều phối** (C0.1): `target` không truyền vào `analyse`; còn rủi ro nhãn nằm trong trường `context` | Trung bình (mã rõ; context chưa mở hết) |
| Lỗi LLM KHÔNG bị quy thành benign | — | `[CHƯA tải]` | `call_llm`→`analyse`→`process_one` | **BÁC BỎ (C0.1): lỗi LLM → benign âm thầm** — xem mục 7 | Cao (đọc mã) |
| Metric P-C/P-R/VPS định nghĩa ACL | v1: câu chữ khác (bỏ) | Sec 4.2 | `evaluate.py` (chỉ both_correct/both_wrong, không VPS); `scripts/metrics.py` của nhóm | **Đã chốt (§7.5):** P-R = nhãn đảo, VPS = P-C − P-R | Cao |

## 6. Việc tiếp theo của Giai đoạn A (chưa làm)

- [x] **(C0.4)** Đọc bản **arXiv v1 HTML**, điền số PrimeVul/SVEN + định nghĩa P-C/P-R/VPS + chi phí/mẫu vào manifest `paper_facts` → mục 7.5. **Đã tải ACL PDF** (primary) và chốt định nghĩa P-R (§7.5).
- [x] **(C0.2/C0.4)** Đọc `evaluate.py` (PrimeVul): chỉ có pair-level both_correct/both_wrong, không VPS; định nghĩa ACL đã đối chiếu → §7.5.
- [x] **(C0.1)** Đọc `analyse()` + `process_one()` + vòng lặp chính `VulAgent-Qwen.py`: xác nhận không rò nhãn vào prompt **ở tầng điều phối**; phát hiện lỗi LLM **bị** quy thành `benign` → mục 7.
- [x] **(C0.4)** Mở trường `context` (SEVEN + PrimeVul_context): **không rò nhãn** (§7.4); rủi ro C0.1 qua context đã đóng.
- [x] **(C0.4)** Mở `primevul_zh_format_complete.json`: JSON list 419 phần tử có cả `_before`/`_after` — nhưng không lọt prompt (§7.4).
- [x] **(C0.5)** Xác minh SEVEN 166 dòng = **83 cặp**, PrimeVul 870 dòng = **435 cặp**, thứ tự ghép cặp → mục 7. Còn lại: đối chiếu test IDs với paper.

## 7. Kết quả đọc mã C0.1 + C0.5 (ngày 2026-11-09)

### 7.1 C0.1 — Rò nhãn vào prompt?

- **Tầng điều phối SẠCH.** `analyse(src_code, proj, name, context)` (dòng 260) **không** nhận `target`. `process_one` (dòng 465–466) đọc `target`/`cwe` nhưng chỉ dùng để **chấm** (dòng 475–483), không truyền vào `analyse`. Mọi prompt ghép từ `numbered_code / proj / name / report_text / code_context` — không có trường nhãn.
- **Rủi ro còn lại (chưa đóng):** trường `context` (`rec["context"]`, dòng 463) được nhúng vào prompt `UnifiedPrunerAgent` (dòng 335). Phải mở nội dung `context` để chắc chắn nó **không** chứa nhãn hoặc dấu vết bản fixed. → gộp vào việc mở `primevul_zh_format_complete.json`.
- Lỗi phụ (không phải rò nhãn): `process_one` đọc `rec.get("proj")` nhưng PrimeVul có trường tên `project` → `proj="None"` lọt vào prompt cho PrimeVul (mất thông tin project, không ảnh hưởng nhãn).

### 7.2 C0.1 — Lỗi LLM → benign âm thầm **(RỦI RO ĐÃ XÁC NHẬN)**

`call_llm` (dòng 86–110) bắt **mọi** exception, trả chuỗi `"ERROR: LLM call failed"`, **không retry, không raise**. Chuỗi lỗi lan truyền:

- **Tại Aggregator** (dòng 301–314): `safe_parse` → `None` → `or {}` → `confirmed_issues=[]` → **early-return `final_vulnerability_reported=False`** = benign.
- **Tại FinalValidator** (dòng 349–364): parse lỗi → `final_dict={}` → `issues=[]` → `vulnerability_reported=False` = benign.
- `process_one` dòng 472: `vuln_flag = 1 if ...reported else 0` → lỗi thành **0**. Với mẫu `target=1` → đếm thành **False Negative**; mẫu `target=0` → **Correct**. Lỗi hạ tầng **trộn lẫn** với "model kết luận không có lỗ hổng"; **không có trạng thái `unknown`/`error` riêng**.
- Khác biệt: chỉ khi `process_one` **tự** ném exception (vd `KeyError rec["func"]`) thì vòng lặp chính (dòng 522–525) bắt và **bỏ mẫu** (không vào `pred/gt`) → mẫu rơi khỏi mẫu số, cũng âm thầm.

**Hệ quả bắt buộc cho nhóm:**
1. Pipeline của nhóm **phải** tách trạng thái `unknown` khi `call_llm` lỗi (đúng PLAN mục 2), log riêng số mẫu lỗi, **không** để lẫn vào benign.
2. Khi dùng các `*_full.json` công bố của repo làm fixture cho `metrics.py`: ca trong `false_negatives/` **có thể gồm cả lỗi hạ tầng**, không phân biệt được từ file → ghi chú giới hạn này khi báo cáo số tái hiện.

**Bằng chứng thực nghiệm (C0.3, quét bằng `src/schema.py --repo`):** trong output Qwen3 PrimeVul công bố của repo (854 file), có **3 file dính sentinel `ERROR: LLM call failed` + `final_vulnerability_reported=False`** → đúng mẫu "lỗi → benign":
- `Vulagent_primevul/Qwen3/false_negatives/vim_196578_full.json` — mẫu **vuln** (target=1) bị lỗi LLM → benign → đếm thành **FN thật** (ô nhiễm số liệu).
- `…/correct/rpm_247337_full.json`, `…/correct/glewlwyd_230147_full.json` — mẫu **fixed** (target=0), lỗi→benign tình cờ "đúng".
- SEVEN Qwen3 (166 file): **0 file** dính lỗi (lượt chạy sạch). ⇒ rủi ro là THẬT nhưng hiếm; `schema.py` tự động gắn cờ các ca này.

### 7.3 C0.5 — Thứ tự ghép cặp và số cặp (đo trên dữ liệu thật)

| Tập | Dòng | target | Cặp | idx trong cặp | commit_url |
|---|---|---|---|---|---|
| PrimeVul `primevul_test_paired.jsonl` | 870 | xen kẽ `1,0,1,0…` hoàn hảo | **435** | **KHÁC nhau** (vd 195908 vs 234731) | giống nhau trong cặp |
| SEVEN `test_with_idx.jsonl` | 166 | xen kẽ `1,0…` hoàn hảo | **83** | liên tiếp (1,2 / 3,4…) | giống nhau trong cặp |

- Dòng index chẵn (0-based) = **vulnerable** (`target=1`), dòng lẻ = **fixed** (`target=0`), xác nhận trên toàn bộ cả hai tập (435/435 và 83/83 cặp khớp mẫu).
- **PrimeVul KHÔNG ghép cặp được theo `idx`** (hai thành viên khác idx) → phải ghép theo **thứ tự dòng liền kề** (hoặc gom theo `commit_url`). ⇒ `evaluate.py` repo ghép `2*gi, 2*gi+1` là **đúng**; suy luận `both_wrong = P-R` (vuln→benign & fixed→vuln) **hợp lệ**.
- **Đính chính câu chữ tài liệu nhóm:** `scripts/metrics.py` và `reproduction_plan.md` nói "ghép cặp theo ID". Chính xác hơn: **sample-level** map pred↔gt theo `idx` (đúng); **pair-level** phải ghép theo **thứ tự liền kề + chuẩn hóa vuln trước** vì idx khác nhau. `build_pairs(mode="consecutive")` của nhóm (dòng 110–128) **đã làm đúng** điều này — chỉ cần sửa lời mô tả, **không** sửa logic.
- **(2026-11-14) idx trùng:** ground truth PrimeVul có **2 idx xuất hiện hai lần** (349259 ở dòng 447/449, 439495 ở dòng 655/657; đều là mẫu fixed, cùng nhãn) → 870 dòng nhưng chỉ **868 idx duy nhất**; sample-level chấm tối đa 868 mẫu. Output công bố cũng không sạch: thư mục `Vulagent_primevul/Qwen3/` có 6 idx nằm ở cả `correct/` lẫn `false_*/` với kết luận trái nhau (DeepSeek: 5), và `result.txt` Qwen3 cho idx 439495 hai kết luận khác nhau dù temperature 0. ⇒ dùng `result.txt` làm nguồn dự đoán (không dùng `--pred-dir` cho Qwen3/DeepSeek); `metrics.py` nay cảnh báo idx trùng.
- SEVEN là **Python** (`def getKey(client)`), khớp ghi chú audit. Còn lại: đối chiếu 83 cặp này có đúng test split/IDs của paper không (cần PDF).

### 7.4 C0.4 (offline) — Trường `context` có rò nhãn không? **(RỦI RO ĐÃ ĐÓNG)**

Đã mở và quét toàn bộ context của cả hai tập:

- **SEVEN_context** (`test_with_idx_context_cleaned.jsonl`, dùng bởi entrypoint Qwen): trường `context` là `dict {imports, callee_funcs}` — danh sách import + **mã nguồn các hàm phụ trợ liên thủ tục**. 164/166 dòng có `imports+callee_funcs`, 2/166 có key `error`. Quét 166 dòng: **0 dòng** chứa nhãn/bản fixed. ⇒ context là ngữ cảnh code hợp lệ, **không rò nhãn**.
- **PrimeVul_context** (`primevul_zh_format_complete.json`): JSON list **419 phần tử**, mỗi phần tử có `code_context, commit_hash, cve_id, cwe_list, repository, short_hash, vulnerableMethods_before, vulnerableMethods_after`. Chứa **cả bản lỗi lẫn bản vá** → *tiềm ẩn* rò nhãn. Nhưng:
  1. Hàm `extract_code_context_from_primevul` (dòng 199–240) dùng `vulnerableMethods_before/after` **chỉ để KHỚP** bản ghi, và **chỉ trả về chuỗi `code_context`** — KHÔNG trả `vulnerableMethods_after`.
  2. `code_context` **không nhúng** bản vá (đã kiểm: mã `_after` không phải substring của `code_context`); 341/419 phần tử có `code_context` không rỗng.
  3. Hàm này là **DEAD CODE trong entrypoint Qwen** (định nghĩa ở dòng 199, **không có call site**); pipeline GPT-4o PrimeVul (`Vulagent_primevul/ChatGPT4o/VulAgent-GPT4O.py`) load `test.jsonl` và **không dùng context**.
  - ⇒ Không có đường rò nhãn đang hoạt động. **CẢNH BÁO cho nhóm:** nếu tự dựng pipeline PrimeVul-có-context từ file này, chỉ lấy `code_context`, **tuyệt đối không** đưa `vulnerableMethods_after` vào prompt.

### 7.5 C0.4 — Số liệu & định nghĩa từ paper (bản arXiv v1 HTML, đọc 2026-11-09)

Nguồn: `https://arxiv.org/html/2509.11523v1` (đọc verbatim phần đầu; số bảng là **summary**, chưa verbatim). **Chưa đối chiếu bản ACL 2026 (primary).** Chi tiết đã khóa trong [experiment_manifest.yaml](../experiment_manifest.yaml) mục `paper_facts`.

- **PrimeVul:** 435 cặp. ⚠️ Paper **tự mâu thuẫn**: Sec 3.1 gọi là "validation set", Sec 4.3 gọi là "test set". Số 435 khớp file; tên split cần xác minh bản ACL. (Summary: 304/435 cặp có context.)
- **SVEN/SEVEN:** 1606 chương trình = **803 cặp**, **C/C++ và Python**, split **9:1 train/validation** — **KHÔNG phải 8:1:1**, và paper **KHÔNG nêu số cặp test**. ⇒ Đính chính ghi chú cũ "lệch ~80 cặp": paper không hề nêu ~80; 83 cặp là tập đánh giá của repo, không trích được từ paper.
- **Chi phí/mẫu (Sec 3.2, verbatim):** trung bình **8.83 lời gọi LLM** và **7036.95 token output** mỗi mẫu → dùng ước ngân sách C1 (xem manifest `cost.paper_reference`).
- **Backend báo cáo (summary Table 2):** GPT-4o, Qwen3-235B-A22-instruct, DeepSeek v3.1. temp 0, top_p 1 (khớp mã).

#### ✅ ĐÃ CHỐT ĐỊNH NGHĨA P-R (2026-11-09) — đọc bản **ACL PDF (primary)** qua `markitdown`

Tải `https://aclanthology.org/2026.findings-acl.928.pdf`, convert bằng Microsoft **markitdown 0.1.9** sang markdown, đọc mục định nghĩa metric (Sec 4.2 "Evaluation Metrics"). **Verbatim** (đã gỡ ngắt dòng):

- **P-C** = "the percentage of function pairs where both functions are correctly classified (**vulnerable as vulnerable, fixed as benign**)."
- **P-R** = "the percentage of pairs where the two labels are predicted **inversely** (**vulnerable predicted as benign while the fixed version is predicted as vulnerable**)."
- **VPS** = "we compute **VPS = P-C − P-R**, which measures the net gain of correct over reversed pair-wise predictions."

| Nguồn | Định nghĩa P-R | (pred_vuln, pred_fixed) |
|---|---|---|
| **ACL 2026 (primary, verbatim)** | nhãn **ĐẢO** | pred(vuln)=benign **VÀ** pred(fixed)=vuln |
| arXiv v1 (secondary) | "both predicted vulnerable" | pred(vuln)=1 VÀ pred(fixed)=1 — **câu chữ tiền ấn phẩm, KHÁC ACL, không dùng** |
| **`scripts/metrics.py` của nhóm** | nhãn **ĐẢO** (dòng 190: `pv==0 and pf==1`) | **KHỚP ACL** |

**Kết luận:** ACL (primary) định nghĩa P-R = **nhãn đảo** → **`metrics.py` của nhóm ĐANG ĐÚNG**, KHÔNG cần sửa logic. Bản arXiv v1 chỉ là diễn đạt sơ sài, bỏ qua. `pair_metrics()` còn xuất thêm `both_vulnerable`/`both_benign` để đối chiếu nếu cần.

**Số liệu ACL verbatim (Table 1, VulAgent trên backend GPT-4o):**

| Dataset | P-C | P-R | VPS | FPR | F1 | ACC |
|---|---|---|---|---|---|---|
| PrimeVul | 26.6 | 10.1 | 16.5 | 36.7 | 56.2 | 58.6 |
| SVEN | 26.5 | 6.02 | 20.4 | 55.4 | 65.6 | 60.2 |

Kiểm phép trừ VPS = P-C − P-R: PrimeVul 26.6−10.1=16.5 ✓; SVEN 26.5−6.02=20.48≈20.4 ✓ (làm tròn). → **Ở dòng VulAgent, VPS khớp P-C − P-R.** (Ghi chú cũ "Bảng 1 có ô VPS không khớp" nhiều khả năng là lệch cột khi đọc bảng baseline bị trộn 2 nhóm cột PrimeVul/SVEN, không phải lỗi paper — các dòng baseline markitdown trích bị xô cột.) ACL cũng nêu rõ PrimeVul **test set = 435 cặp** (giải quyết mâu thuẫn val/test của arXiv) và SVEN 803 cặp, 9 CWE.

**Còn lại (không chặn):** đối chiếu test IDs SEVEN 83 cặp với split paper (paper không liệt IDs); số Table 1 là của backend GPT-4o — nếu nhóm chạy Qwen3 thì so với dòng Qwen3 ở Table 2/phần robustness.
