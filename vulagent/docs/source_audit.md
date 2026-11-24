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

### 7.6 Phát lại output công bố qua pipeline của nhóm (2026-11-15)

Cách làm: `scripts/run_pipeline.py --backend replay` dựng lại prompt từ dữ liệu, lấy output từng agent đã lưu trong `*_full.json` của repo gốc, rồi áp luật quyết định của nhóm ([src/pipeline.py](../src/pipeline.py)). **Không gọi model**; số dưới đây mô tả lượt chạy Qwen3 mà repo gốc công bố, không phải kết quả nhóm chạy.

| Tập (output Qwen3 công bố) | Mẫu phát lại | Trùng cờ repo gốc | `unknown` | Nguyên nhân `unknown` |
|---|---|---|---|---|
| SEVEN có context | 166/166 | 137 | **29** | 28 FinalValidator trả JSON không parse được; 1 Aggregator không cho danh sách candidate đọc được |
| PrimeVul | 850/870 dòng (20 dòng không có fixture) | 843 | **7** | 3 lỗi LLM (sentinel, đã biết ở §7.2); 2 FinalValidator không parse được; 2 Aggregator không đọc được |

- **Phát hiện mới — lỗi parse cũng thành benign âm thầm.** Cả 29 ca SEVEN và 7 ca PrimeVul đều mang cờ `final_vulnerability_reported=False` trong output công bố. Đối chứng bằng bản sao nguyên văn `strip_codeblock`/`safe_parse` của repo gốc: 28/28 output FinalValidator của SEVEN cũng trả `None` → `final_dict={}` → benign. `schema.py --repo` chỉ bắt sentinel lỗi LLM nên trước đây báo SEVEN "0 file dính lỗi".
- **Dạng hỏng (SEVEN, 28 ca):** 19 "Unterminated string", 9 "Expecting ',' delimiter"; 27/28 output kết thúc dở dang (dài 7.2k–16.4k ký tự), phù hợp với việc bị cắt ở `max_tokens=4096` — fixture không lưu `finish_reason` nên **chưa xác minh** được nguyên nhân. Cả 28 ca là file C/C++ (`.c` 23, `.cc` 4, `.cpp` 1); 14 mẫu vulnerable và 14 mẫu fixed.
- **Ảnh hưởng tới số công bố của SEVEN Qwen3** (tính bằng `metrics.py`, bảng ở `results/tables/seven_qwen3.json` và `replay_seven_qwen3.json`): theo cờ repo gốc TP 40/FP 24/FN 43/TN 59, recall 48.19%, P-C 25/83, P-R 9/83, VPS 19.28%. Khi tách 29 ca `unknown`: 137 mẫu có dự đoán, FN còn 28 (15/43 FN công bố là lỗi parse, không phải model kết luận an toàn), TN còn 45; trên 61 cặp đủ dự đoán P-C 20, P-R 3.
- **Hệ quả cho nhóm:** khi chạy thật phải báo số `unknown` cạnh mọi bảng; cân nhắc tăng `max_tokens` của FinalValidator hoặc thử lại khi JSON hỏng, và khai báo đó là thay đổi so với repo gốc.
- **Lỗi hoán đổi tham số:** `process_one` gọi `analyse(code, name, proj, context)` trong khi chữ ký là `analyse(src_code, proj, name, context)` → `{proj}` trong prompt nhận tên file, `{name}` nhận chuỗi `proj`. Pipeline nhóm giữ hành vi này mặc định để tái hiện (`--no-upstream-quirks` để sửa).
- **Chi phí đo từ phát lại:** SEVEN 8.38 lời gọi/mẫu, PrimeVul 9.02 (paper: 8.83). Lượng ký tự prompt gấp khoảng 4 lần ký tự output — xem `experiment_manifest.yaml::cost.replay_measured`.

### 7.7 Đối chiếu arXiv v1 ↔ ACL 2026: bảng kết quả và danh sách thí nghiệm (2026-11-24)

**Nguồn và cách đọc.** arXiv: `https://arxiv.org/html/2509.11523v1` (trang abs chỉ liệt kê **v1**, nộp 15-09-2025), trích bảng từ thẻ `<table>` của HTML. ACL: `https://aclanthology.org/2026.findings-acl.928.pdf` (19 trang, pp. 18598–18616), trích text bằng PyMuPDF. Mọi số dưới đây chép từ hai file đó; cột "nhóm tính lại" lấy từ `results/tables/*.json` (output do repo gốc công bố, chấm bằng `metrics.py`). Đề giao bản arXiv ([REQUIREMENTS.md](../REQUIREMENTS.md)); nhóm giữ ACL làm mốc chính và dùng mục này để giải thích khác biệt.

#### a) Danh sách thí nghiệm

| Thí nghiệm | arXiv v1 | ACL 2026 | Khác biệt |
|---|---|---|---|
| RQ1 so với baseline (PrimeVul + SVEN) | Table 1 | Table 1 | ACL **thêm dòng Semgrep**; ACL ghi "chạy **3 lần**, lấy trung bình" (arXiv không nêu số lượt) |
| Ablation thành phần (bỏ FinalValidator / bỏ PathPruner) | **không có** | **Table 2 (mới)** | Thí nghiệm chỉ có ở ACL |
| RQ2 tổng quát hóa qua 3 backend | Table 2 | Table 3 | Cùng số, ACL cắt bớt chữ số |
| RQ3 có/không context | Table 3 | Table 4 | Cùng số, ACL cắt bớt chữ số |
| RQ4 theo CWE | Table 4 (PrimeVul Top-8 + SVEN 9 CWE) | Table 5 (rút gọn 5+5) + Table 7 phụ lục (đầy đủ) | Table 7 ACL trùng Table 4 arXiv; Table 5 ACL có dòng **CWE-617** không nằm trong bảng đầy đủ |
| RQ5 oracle-CWE trên SVEN | Table 5 | Table 6 | **Giống hệt** |
| Radar theo CWE | Figure 4 | Figure 4 | Cùng nội dung |
| Case study `search_make_new` (libevent) | Mục 5 | Mục 6 + Phụ lục A | Cùng ca |
| Chi phí | 8.83 lời gọi, 7,036.95 token output/mẫu | như arXiv + so với GPTLens 2263.95, VulTrial 3119.16 token/mẫu | ACL thêm so sánh chi phí và mục Limitations |
| Phụ lục | không có | A–G (case, luồng xử lý, bảng agent, nguồn context, thuật toán dựng context SVEN, đạo đức, prompt) | Chỉ có ở ACL |

#### b) Số liệu VulAgent (các dòng nhóm cần so)

Thứ tự cột: P-C / P-R / VPS / FPR / F1 / ACC (%).

| Bảng | Dòng | arXiv v1 | ACL 2026 | Nhóm tính lại từ output công bố |
|---|---|---|---|---|
| RQ1 | GPT-4o, PrimeVul | 26.6 / 10.1 / 16.5 / 36.7 / 56.2 / **58.4** | 26.6 / 10.1 / 16.5 / 36.7 / 56.2 / **58.6** | 26.40 / 10.28 / 16.12 / 36.62 / 55.98 / 58.20 (428/435 cặp chấm được; một lượt, paper là trung bình 3 lượt) |
| RQ1 | GPT-4o, SVEN | 26.5 / 6.02 / 20.4 / 55.4 / 65.62 / 60.2 | 26.5 / 6.02 / 20.4 / 55.4 / 65.6 / 60.2 | repo không công bố output GPT-4o cho SVEN |
| RQ2 | Qwen3, PrimeVul | 25.75 / 11.03 / 14.71 / 40.15 / 57.70 / 57.36 | 25.7 / 11.0 / 14.7 / 40.1 / 57.7 / 57.3 | **25.75 / 11.03 / 14.71** / 43.42 / 57.76 / 57.37 |
| RQ2 | Qwen3, SVEN | 30.12 / 10.84 / 19.28 / 28.91 / 54.42 / 59.63 | 30.1 / 10.8 / 19.2 / 28.9 / 54.4 / 59.6 | **30.12 / 10.84 / 19.28 / 28.92 / 54.42 / 59.64** |
| RQ2 | DeepSeek v3.1, PrimeVul | 17.70 / 8.74 / 8.96 / 19.95 / 41.59 / 54.73 | 17.7 / 8.74 / 8.96 / 19.9 / 41.5 / 54.7 | không có output |
| RQ2 | DeepSeek v3.1, SVEN | 30.12 / 9.64 / 20.48 / 31.30 / 56.58 / 60.20 | 30.1 / 9.64 / 20.4 / 31.3 / 56.5 / 60.2 | không có output |
| RQ2 | GPT-4o, PrimeVul | 26.67 / 10.11 / 16.55 / 36.78 / 56.11 / 58.62 | 26.6 / 10.1 / 16.5 / 36.7 / 56.1 / 58.6 | như dòng RQ1 |
| RQ2 | GPT-4o, SVEN | 26.51 / 6.02 / 20.49 / 55.42 / 65.62 / 60.20 | 26.5 / 6.02 / 20.4 / 55.4 / 65.6 / 60.2 | — |
| RQ3 | PrimeVul w/o context | 17.50 / 7.50 / 10.00 / 38.75 / 52.00 / 55.00 | 17.5 / 7.5 / 10.0 / 38.7 / 52.0 / 55.0 | chưa chạy |
| RQ3 | PrimeVul w/ context | 28.73 / 10.70 / 18.03 / 36.34 / 57.02 / 59.01 | 28.7 / 10.7 / 18.0 / 36.3 / 57.0 / 59.0 | chưa chạy |
| RQ3 | SVEN w/o context | 20.48 / 7.20 / 13.25 / 60.00 / 63.27 / 56.63 | 20.4 / 7.20 / 13.2 / 60.0 / 63.2 / 56.6 | chưa chạy |
| RQ3 | SVEN w/ context | 26.51 / 6.02 / 20.48 / 55.42 / 65.62 / 60.20 | 26.5 / 6.02 / 20.4 / 55.4 / 65.6 / 60.2 | — |
| RQ5 | Direct (oracle-CWE, SVEN) | 36.14 / 12.05 / 24.10 / 49.40 / 65.95 / 62.05 | giống hệt | chưa chạy |
| RQ5 | VulTrial (oracle-CWE) | 25.30 / 7.23 / 18.07 / 39.76 / 58.54 / 59.04 | giống hệt | chưa chạy |
| RQ5 | VulAgent (oracle-CWE) | 24.10 / 1.20 / 22.98 / 20.48 / 52.94 / 61.45 | giống hệt | chưa chạy |

Chỉ có ở ACL — Table 2 (ablation thành phần):

| Dataset | Cấu hình | P-C / P-R / VPS / FPR / F1 / ACC |
|---|---|---|
| PrimeVul | đầy đủ | 26.61 / 10.10 / 16.50 / 36.70 / 56.20 / 58.60 |
| PrimeVul | bỏ FinalValidator | 15.56 / 11.94 / 3.62 / 65.00 / 58.74 / 51.81 |
| PrimeVul | bỏ PathPruner | 15.63 / 10.34 / 5.29 / 61.15 / 58.38 / 52.64 |
| SVEN | đầy đủ | 26.50 / 6.02 / 20.40 / 55.40 / 65.60 / 60.20 |
| SVEN | bỏ FinalValidator | 12.07 / 7.23 / 4.48 / 72.29 / 61.48 / 52.41 |
| SVEN | bỏ PathPruner | 18.07 / 4.82 / 13.25 / 62.65 / 63.64 / 56.62 |

Các dòng baseline của Table 1 (UniXcoder, GPT-3.5 CoT/GPTLens/VulTrial, GPT-4o CoT/LLM-MultiRole/GPTLens/VulTrial) **giống nhau từng số** giữa hai bản; ACL chỉ thêm Semgrep (PrimeVul 0.00 / 0.08 / −0.08 / 64.0 / 50.9 / 46.0; SVEN 0.00 / 0.00 / 0.00 / 31.3 / 38.5 / 50.0).

#### c) Bảng khác biệt hoàn chỉnh và lý do lấy ACL làm mốc

| Điểm | arXiv v1 | ACL 2026 | Nhận xét |
|---|---|---|---|
| Định nghĩa P-R (câu chữ) | "both functions are incorrectly classified as vulnerable" (Sec 3.3) | nhãn bị đoán **đảo** (Sec 4.3) | **Số trong bảng arXiv đã tính theo nghĩa "đảo"**: với output Qwen3 SVEN công bố, số cặp đảo = 9/83 = 10.84% (khớp Table 2 arXiv), còn số cặp "cả hai vulnerable" = 15/83 = 18.07% (không khớp). PrimeVul Qwen3 tương tự: đảo 11.03% (khớp), cả hai vulnerable 32.41%. ⇒ arXiv sai ở câu mô tả, không sai ở số; ACL sửa câu chữ. |
| Tên tập 435 cặp PrimeVul | Sec 3.1 "validation set", Sec 4.3 "test set" | "test set" thống nhất | ACL hết mâu thuẫn nội bộ |
| Split SVEN | "9:1 train/validation" | "8:1:1 train/validation/test" | Cả hai bản **không nêu số cặp đánh giá**; số 83 cặp suy từ dữ liệu repo và từ mẫu số của bảng (9/83 = 10.84%) |
| ACC VulAgent GPT-4o PrimeVul | Table 1 ghi 58.4, Table 2 ghi 58.62, lời văn "+5.0 điểm" | 58.6 ở cả hai bảng, "+5.2 pp" | arXiv tự lệch giữa hai bảng; ACL nhất quán |
| FPR PrimeVul trong lời văn | "36.8%" (bảng 36.7) | "36.7%" | lỗi làm tròn ở arXiv |
| Số lượt chạy | không nêu | 3 lượt, lấy trung bình | ACL rõ giao thức hơn |
| Ablation thành phần | không có | Table 2 | Bằng chứng trực tiếp cho vai trò Pruner/FinalValidator chỉ có ở ACL |
| Baseline Semgrep | không có | có | |
| Link mã nguồn | chỉ viết "We have also released…", **không có URL** | `https://github.com/HotFrom/VulAgent` | Căn cứ xếp đề vào nhánh "có mã nguồn công khai" nằm ở bản ACL |
| Tên giai đoạn | Phase I–IV; "Hypothesis-Path Verification" | "Hypothesis-Path validation"; tên agent PathPrunerAgent / FinalValidatorAgent xuất hiện trong bảng ablation | |
| Thảo luận hạn chế | Mục 6 Discussion (threats, limitations ngắn) | Mục 9 Limitations (context, coverage, chi phí có số) + Phụ lục F đạo đức | |

**Điểm tồn tại ở CẢ hai bản (không phải ACL sửa được hết):**
- Table 1, các dòng baseline: cột VPS không bằng P-C − P-R (vd GPT-4o VulTrial PrimeVul 18.6 − 11.4 = 7.2 nhưng in 7.13; GPT-3.5 VulTrial cùng P-C/P-R lại in 1.38; GPT-3.5 GPTLens 10.1 − 6.44 = 3.66 nhưng in −0.91). Dòng VulAgent thì khớp. Không rõ nguyên nhân; khi trích baseline phải ghi "số in trong bài".
- RQ5: 24.10 − 1.20 = 22.90 nhưng in 22.98.
- FPR Qwen3 PrimeVul: bài in 40.15, tính từ output công bố ra 43.42 (P-C/P-R/VPS/F1/ACC thì khớp). Chưa giải thích được.

**Kết luận dùng cho slide/báo cáo.** Hai bản cùng tác giả, cùng phương pháp, cùng bộ số chính (Table 1 dòng VulAgent, RQ2, RQ3, RQ5 trùng nhau, ACL chỉ làm tròn). ACL là bản đã bình duyệt, sửa câu định nghĩa P-R cho đúng với cách tính thực tế, thống nhất tên split, nêu số lượt chạy, thêm ablation thành phần + Semgrep + phụ lục, và là bản duy nhất dẫn URL repo. Vì vậy lấy ACL làm mốc không làm đổi mục tiêu tái hiện của bản arXiv; phần chỉ có ở ACL (ablation Table 2) là thí nghiệm cộng thêm.

> Đính chính §7.5: câu "KHÔNG phải 8:1:1" chỉ đúng với arXiv v1 (9:1); ACL ghi 8:1:1. Câu "arXiv v1 định nghĩa P-R khác — bỏ qua" nay thay bằng nhận xét ở bảng (c): khác ở câu chữ, số liệu vẫn theo nghĩa đảo nhãn.
