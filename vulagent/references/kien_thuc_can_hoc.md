# Kiến thức cần học và đọc cho đề tài VulAgent (nhóm 3)

> Tài liệu này mở rộng mục 8 của file `VulAgent_prompt_nhom_3.md`: giải thích từng nhóm chủ đề, mức độ cần nắm, dùng ở đâu trong đề tài và nên đọc gì. Sắp xếp theo mức ưu tiên vì thời gian có hạn.

---

## Nhóm 1: Bắt buộc, cả 3 người đều phải nắm

### 1.1 Nền tảng lỗ hổng bộ nhớ và CWE

- **Cần biết:** CWE-125 (đọc ngoài biên), CWE-787 (ghi ngoài biên), CWE-476 (NULL dereference), CWE-416 (use-after-free), CWE-78 (OS command injection), CWE-862 (thiếu kiểm tra quyền).
- **Mức độ:** nhìn một đoạn code C ngắn và chỉ ra được sink, đầu vào kiểm soát được, và guard nào chặn được lỗi.
- **Đọc:** mô tả từng CWE trên cwe.mitre.org, phần "Demonstrative Examples" là đáng đọc nhất. Bổ sung C/C++ memory model (stack/heap, con trỏ, kích thước buffer, integer overflow).

### 1.2 Source – Sink – Sanitizer/Guard

- Đây là tư duy cốt lõi của VulAgent. Mỗi giả thuyết phải trả lời: dữ liệu vào từ đâu, đi qua đâu, tới thao tác nguy hiểm nào, và có điều kiện nào chặn trước đó không.
- Nếu không hiểu khái niệm này thì không giải thích được TriggerPlanner, AssumptionPruner, FinalValidator, cũng như các trường hợp hệ thống sai.

### 1.3 Cặp vulnerable/fixed và các metric của bài

- **Cần hiểu:** vì sao dùng cặp, ACC / Precision / Recall / F1 / FPR, P-C, P-R, VPS.
- **Chú ý:** theo prompt, P-R ở bản ACL là cặp bị đảo nhãn (vulnerable→benign và fixed→vulnerable), còn bản arXiv mô tả không nhất quán. Người phụ trách metric nên tự vẽ bảng đúng/sai của một cặp và đối chiếu với code.
- **Đọc:** phần metric của PrimeVul (bài "Vulnerability Detection with Code Language Models: How Far Are We?", Ding et al.).

### 1.4 Đọc hiểu hai bản paper VulAgent

- Thứ tự đọc: kiến trúc (hình) → phương pháp → bảng kết quả → phụ lục prompt.
- Lập bảng khác biệt giữa bản arXiv (2509.11523) và bản ACL 2026, ví dụ split SVEN và định nghĩa P-R.

### 1.5 Git, Python, quản lý bí mật

- **Cần biết:** commit hash, `.env`, `.gitignore`, JSONL/CSV, unit test cho parser và metric.
- Repo gốc có thể chứa API key nhúng cứng: phải biết cách không dùng và không đưa key vào log.

---

## Nhóm 2: Phân tích chương trình (cho người phụ trách pipeline và phương pháp)

Không cần học sâu lý thuyết, chỉ cần hiểu đủ để giải thích và kiểm tra output của agent.

| Chủ đề | Cần hiểu được | Dùng ở đâu trong đề tài |
|---|---|---|
| Control-flow graph (CFG) | Vẽ CFG cho hàm có `if`/`return` sớm | FinalValidator kiểm tra sink có đạt tới không |
| Data-flow / taint analysis | Theo dõi một biến từ nguồn tới sink | `trigger_path` |
| Guard dominance | Guard nằm trên mọi đường tới sink thì mới chặn được sink | Điều kiện để bác bỏ giả thuyết |
| Path feasibility | Có đường đi không có nghĩa là thực thi được | Phân biệt "giữ giả thuyết" với "bác bỏ" |
| Call graph | Ai gọi hàm này, đối số đến từ đâu | Context cấp dự án, ví dụ hàm gọi |
| Program slicing | Cắt phần code liên quan tới một biến/dòng | Xây context chọn lọc (hướng điểm cộng a) |
| Code Property Graph + Joern | Truy vấn CPG, chạy Joern trên Mac ARM | Context builder của SVEN |

**Đọc:**

- *Static Program Analysis* (Møller & Schwartzbach, có bản miễn phí online): chương về control-flow và data-flow analysis.
- Yamaguchi et al., "Modeling and Discovering Vulnerabilities with Code Property Graphs" (IEEE S&P 2014).
- Tài liệu Joern: docs.joern.io.
- Tài liệu Semgrep, nếu dùng làm baseline.

> **Lưu ý:** Joern có thể không chạy tốt trên Mac Apple Silicon. Nên thử trong Docker ngay từ tuần đầu để biết rào cản thật.

---

## Nhóm 3: LLM và multi-agent (cho người phụ trách hiện thực và demo)

- **Prompting:** one-shot, chain-of-thought (Wei et al., 2022), vai trò của temperature/top_p. Cần biết vì baseline của bài là one-shot/CoT.
- **Multi-agent orchestration:** trong code, mỗi "agent" thực chất là một lời gọi LLM với prompt và vai trò riêng, chạy tuần tự hoặc song song. Đọc thêm ReAct và tool calling để hiểu ngữ cảnh chung.
- **Structured output:** JSON schema, validate bằng pydantic hoặc jsonschema, retry có giới hạn; không để JSON lỗi bị biến thành dự đoán "benign" một cách âm thầm.
- **Prompt injection từ mã nguồn:** comment trong code có thể chứa câu kiểu "ignore previous instructions". Đọc OWASP Top 10 for LLM Applications. Cũng là chủ đề hay cho phần threats to validity.
- **Token accounting, rate limit, chi phí:** viết bộ đếm token và log chi phí ngay từ đầu (435 cặp × nhiều agent × 3 lượt tốn kém rất nhanh).
- **Data leakage:** bản fixed hoặc nhãn thật không được lọt vào prompt của bản vulnerable; CWE thật chỉ dùng trong thí nghiệm `oracle-CWE`.

---

## Nhóm 4: Thực nghiệm (cho người phụ trách dữ liệu và kết quả)

- **PrimeVul:** cách xây dựng, vì sao dedup và chia theo thời gian, thế nào là paired test.
- **SVEN:** dữ liệu từ bài "Large Language Models for Code: Security Hardening and Adversarial Testing" (He & Vechev, CCS 2023). Prompt nhắc split 8:1:1 trên 803 cặp, cần xác định đúng test IDs.
- **Baseline GPTLens / VulTrial:** đọc để phân biệt "tự chạy lại" với "trích số trong bài" (số trích là tham chiếu lịch sử, không phải chạy cùng điều kiện).
- **Ablation study:** thay đổi đúng một thành phần, giữ cố định model, IDs và config.
- **Thống kê cơ bản:** trung bình và độ lệch chuẩn qua 3 lượt, bootstrap confidence interval; mẫu nhỏ thì kết luận phải dè dặt.
- **Reproducibility:** ghi manifest, seed, checksum, phiên bản model. API model có thể bị đổi hoặc ngừng nên cần ghi ngày chạy.

---

## Nhóm 5: Báo cáo và thuyết trình

- **Error analysis:** phân tích ít nhất 3 ca (TP, FP đã loại, FN hoặc FP còn sót), đối chiếu source/sink/guard với code thật.
- **Threats to validity:** nhiễm dữ liệu huấn luyện của LLM, nhãn dataset có nhiễu, phụ thuộc model, context không đầy đủ.
- **Slide và demo:** thiết kế slide ánh xạ được tiêu chí chấm; diễn tập demo; có video hoặc kịch bản dự phòng nếu API lỗi lúc trình bày.

---

## Lộ trình học đề xuất

| Tuần | Nội dung |
|---|---|
| 1 | Nhóm 1 (CWE, source–sink–guard) và đọc hai bản paper |
| 2 | CFG / data-flow / call graph mức khái niệm, thử Joern, bắt đầu audit repo |
| 3 | Structured output, schema, đếm token, dry run một cặp |
| 4–5 | Metric, PrimeVul/SVEN, baseline, chạy thí nghiệm chính |
| 6 | Ablation, error analysis, chọn hướng điểm cộng |
| 7 | Báo cáo, slide, tập thuyết trình |

**Nếu thiếu thời gian:** bỏ phần lý thuyết sâu về phân tích chương trình. Điều bắt buộc là cả nhóm giải thích được **vì sao một guard trước sink làm giả thuyết bị bác bỏ, và khi nào thì không**. Đó là điểm khác biệt chính của VulAgent so với việc chỉ hỏi LLM "hàm này có lỗi không?".

---

## Gợi ý phân bổ theo vai trò

| Thành viên | Ưu tiên học |
|---|---|
| Người 1 (phương pháp & tài liệu) | Nhóm 1, Nhóm 2 (mức khái niệm), Nhóm 5 |
| Người 2 (hiện thực & demo) | Nhóm 1, Nhóm 2 (Joern, CPG), Nhóm 3 |
| Người 3 (dữ liệu & thực nghiệm) | Nhóm 1, Nhóm 4, Nhóm 5 |

---

## Lưu ý về nguồn

Tên bài báo, tác giả và sách ở trên được nêu từ hiểu biết chung, chưa được tra cứu lại khi soạn tài liệu này. Cần kiểm tra tên tác giả, năm và đường dẫn trước khi đưa vào báo cáo. Các chi tiết về kiến trúc và số liệu của VulAgent lấy từ prompt của nhóm, chưa đối chiếu với nội dung hai bản paper.
