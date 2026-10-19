# Kiến thức cần học cho VulAgent

Bản chi tiết (giải thích từng nhóm, danh sách sách/bài báo cần kiểm tra nguồn): [references/kien_thuc_can_hoc.md](references/kien_thuc_can_hoc.md). Phần nền dùng chung với seminar (C, stack, CWE-121/787, source–sink–guard, CFG, debugger): [../seminar_S01/KNOWLEDGE.md](../seminar_S01/KNOWLEDGE.md).

| Ưu tiên | Chủ đề | Cần tự làm được | Dùng ở đâu |
|---|---|---|---|
| 1 | Source–sink–guard, guard dominance, path feasibility | Giải thích vì sao một guard trước sink bác bỏ giả thuyết, và khi nào thì không | Trọng tâm VulAgent |
| 1 | CWE-125/416/476/787/78/862 | Chỉ ra sink, input kiểm soát được, guard trong đoạn C ngắn | Phân loại ca kiểm thử |
| 1 | Cặp vuln/fixed; ACC, precision, recall, F1, FPR, P-C, P-R, VPS | Vẽ bảng đúng/sai một cặp; tính tay rồi đối chiếu script | Thực nghiệm |
| 1 | Hai bản paper (arXiv vs ACL) | Lập bảng khác biệt (split SVEN, định nghĩa P-R) | Báo cáo |
| 1 | Python, Git, JSON/JSONL, schema, unit test, quản lý secret | Ghi/đọc lần chạy, validate output, không commit key | Prototype |
| 2 | CFG, data-flow/taint, call graph, program slicing, CPG/Joern | Giải thích và kiểm tra output của agent; thử Joern trong Docker từ sớm (Mac ARM) | Context builder, FinalValidator |
| 3 | LLM prompting, multi-agent orchestration, structured output, prompt injection từ mã nguồn, token accounting | Mỗi "agent" = một lời gọi LLM với prompt/vai trò riêng; retry có giới hạn; đếm token từ đầu | Pipeline |
| 3 | PrimeVul, SVEN, baseline GPTLens/VulTrial, ablation, bootstrap CI, reproducibility | Phân biệt "tự chạy lại" với "trích số trong bài"; ghi manifest, seed, checksum, ngày chạy | Thực nghiệm |
| 3 | Error analysis, threats to validity, thiết kế slide, diễn tập demo | ≥ 3 ca phân tích; nêu nhiễm dữ liệu, nhãn nhiễu, phụ thuộc model | Báo cáo |

**Lưu ý nguồn:** tên bài báo/tác giả/sách trong tài liệu gốc chưa được tra cứu; kiểm tra trước khi trích. Chi tiết kiến trúc/số liệu VulAgent lấy từ prompt của nhóm, chưa đối chiếu với paper.
