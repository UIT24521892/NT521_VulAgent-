# Prompt tổng cho Claude Code / Codex — đề tài VulAgent (nhóm 3 người)

> Sao chép toàn bộ phần dưới đây vào Claude Code hoặc Codex trong thư mục dự án. Điền các biến ở mục 0 nếu đã biết. Bạn là trợ lý lập trình thực thi công việc, cần tạo mã, kết quả thực nghiệm và tài liệu thật; không dừng ở việc đề xuất kế hoạch.

## 0. Bối cảnh và đầu vào

Bạn đang hỗ trợ nhóm 3 sinh viên làm đề tài môn **Lập trình khai thác lỗ hổng**, chủ đề **Code vulnerability detection**, dựa trên **VulAgent: A Hypothesis Validation-Based Multi-Agent System for Software Vulnerability Detection** (arXiv:2509.11523, 2025) và bản xuất bản tiếp theo **VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection** (Findings of ACL 2026, DOI: 10.18653/v1/2026.findings-acl.928). Đọc cả hai, lấy bản ACL 2026 làm mốc chính khi có khác biệt và ghi rõ phiên bản của số liệu được trích dẫn.

Nguồn bắt buộc:

- arXiv: https://arxiv.org/pdf/2509.11523
- Bản xuất bản ACL: https://aclanthology.org/2026.findings-acl.928.pdf
- Repository do bản ACL dẫn: https://github.com/HotFrom/VulAgent
- Dữ liệu PrimeVul, SVEN: xác định đường dẫn, phiên bản, giấy phép và split thực tế từ nguồn chính thức/được tác giả đóng gói trước khi tải hay chạy.

Biến nhóm điền: `[ĐƯỜNG_DẪN_REPO]`, `[HẠN_NỘP]`, `[NGÂN_SÁCH_API]`, `[MODEL/API_ĐƯỢC_PHÉP]`, `[MÔI_TRƯỜNG_CHẠY]`, `[YÊU_CẦU_NỘP_BÀI]`. Mặc định máy phát triển là **Mac Apple Silicon**; nếu Joern hoặc công cụ khác không chạy phù hợp ARM, khảo sát cách chạy tương thích trong Docker/VM và ghi rõ giới hạn, không tự giả định hỗ trợ.

Tiêu chí chấm: (1) hiểu bối cảnh, vai trò, vấn đề và thuyết trình; (2) giải thích phương pháp/kỹ thuật; (3) vì **đã có mã công khai**, tái hiện thí nghiệm trong bài và biện luận ưu, nhược điểm; (4) điểm cộng: thực nghiệm kịch bản/dữ liệu mới hoặc cải tiến phương pháp và kiểm chứng trên dữ liệu có sẵn. Coi “chạy ra được một ví dụ” là demo, **không** coi là tái hiện toàn bộ thí nghiệm.

## 1. Mục tiêu và phạm vi

Tạo một bản tái hiện **kiểm chứng được** của VulAgent, một demo giải thích được vì sao mẫu có lỗ hổng hoặc bị loại, báo cáo so sánh đúng giao thức, và một thực nghiệm bổ sung có đối chứng nếu đủ thời gian/ngân sách. Không hứa lặp lại chính xác các con số bài báo nếu khác model, phiên bản dữ liệu, prompt, context hoặc ngân sách; ghi rõ khác biệt.

Vấn đề cốt lõi: phát hiện một lời gọi/thao tác nhạy cảm trong hàm chưa đủ; cần xác định đầu vào có thể kiểm soát, điều kiện kích hoạt, đường dữ liệu/đường thực thi, và kiểm tra các guard trước sink trong ngữ cảnh dự án để hạn chế false positive. Nêu rõ phân tích ở mức hàm và ngữ cảnh cấp dự án, điểm mạnh cũng như giới hạn của phương pháp.

Đầu ra tối thiểu: repository có hướng dẫn chạy; mã và cấu hình đã kiểm tra; tập dữ liệu/mẫu được phép sử dụng; bản ghi thực nghiệm; script tính metric; báo cáo kỹ thuật; slide; kịch bản demo ngoại tuyến hoặc dự phòng; bảng chia việc 3 người. Không tạo số đo, trích dẫn, kết quả chạy, screenshot hoặc claim “đã tái hiện” khi chưa có bằng chứng thực tế.

## 2. Giai đoạn A — Kiểm toán nguồn và khóa giao thức

1. Kiểm tra môi trường/repo sẵn có; đọc `README`, toàn bộ script entrypoint, prompt, config, đường dẫn dữ liệu, code đánh giá, phụ thuộc, commit và giấy phép. Lưu commit hash; ghi lại cấu trúc folder hữu ích. Đối chiếu với hình kiến trúc, phần phương pháp, bảng thí nghiệm và phụ lục ở **cả hai** phiên bản bài báo. Repository README có thể đơn giản hóa hoặc đổi thứ tự các bước: **mã đang chạy, bài báo và README phải được đối chiếu**, không tự xem là tương đương.
2. Lập `docs/source_audit.md` gồm bảng `khẳng định | arXiv/trang | ACL/trang | file/hàm trong repo | kết luận | mức chắc chắn`. Xác minh đủ prompt, reports, dataset, context builder, script RQ5, entrypoint chạy PrimeVul và SVEN; đánh dấu mục không có hoặc không tái lập được.
3. Soi mã/config tìm API key hoặc token nhúng trong repository, không in giá trị và không sử dụng khóa được công bố. Thay cơ chế bí mật bằng biến môi trường hoặc file `.env` không commit; cấu hình bỏ qua file bí mật. Kiểm tra lệnh chạy không tự gọi mạng/hệ thống ngoài phạm vi dự định và script không ghi đè dữ liệu. Bắt đầu bằng dry run một mẫu và giới hạn chi phí.
4. Khóa `experiment_manifest.yaml`: bài báo/phiên bản, commit, nguồn dữ liệu và checksum, split/pair IDs, ngôn ngữ, model/provider/phiên bản, tham số suy luận (bài: temperature 0, top_p 1), prompt hash, context mode, số lượt chạy, concurrency, seed nếu có, giới hạn token, số lượng mẫu và ước tính chi phí. Xác minh model API thực sự hỗ trợ từng tham số, ghi khác biệt nếu không.
5. Lập `docs/reproduction_contract.md` phân biệt: **tái hiện đúng cấu hình**, **tái hiện với thay thế được khai báo**, **thí nghiệm thu nhỏ**, **demo thủ công**. Đề xuất phạm vi chạy theo ngân sách, rồi triển khai mức khả thi; chỉ hỏi nhóm khi cần thông tin thanh toán hoặc quyền truy cập không thể suy ra.

## 3. Giai đoạn B — Giải thích và hiện thực/chuẩn hóa pipeline

Đọc mã trước, tận dụng hiện thực gốc. Nếu mã thiếu/không chạy, viết adapter hoặc phục hồi tối thiểu và đánh dấu phần tự làm. Bảo toàn luồng logic của bài báo:

1. **Đầu vào:** cặp hàm vulnerable/fixed, metadata (project, file, CWE, pair ID), mã nguồn có số dòng; phân tích hai vế độc lập, không cho bản fixed/nhãn thật lọt vào prompt của bản vulnerable, hay ngược lại.
2. **MetaAgent:** định tuyến theo ngữ nghĩa, kích hoạt tập nền Static/Analyzer, Behavior, MemoryLayout và chuyên gia phù hợp (FormatString, FilePermission, AuthFlow, CryptoConfig, Concurrency, ErrorHandling, CodeInjection). Đối chiếu tên agent thực tế trong repo; không xây đủ agent bằng stub rồi tuyên bố triển khai đầy đủ.
3. **Detection → Aggregator:** mỗi agent xuất candidate có CWE, sink, line span, nguồn/trigger, chứng cứ; gộp trùng nhưng giữ khác CWE và đường kích hoạt; ghi trace theo agent. Detection ưu tiên không bỏ sót candidate, các bước sau mới lọc.
4. **TriggerPlanner:** với từng candidate, xây `hypothesis_conditions` và `trigger_path` source → bước trung gian → sink cùng dòng tham chiếu. Ghi guard như điều kiện phải kiểm tra; **không tự loại đường đi vì nhìn thấy guard** ở bước lập giả thuyết.
5. **AssumptionPruner:** kiểm tra từng điều kiện bằng ngữ cảnh của hàm/dự án; phân loại plausible/contradicted/unknown (và trạng thái tương ứng trong bản mã/bài báo); chỉ loại giả thuyết khi có chứng cứ mâu thuẫn làm vô hiệu đường kích hoạt; thiếu chứng cứ phải giữ trạng thái chưa chắc chắn, không bịa ra ngữ nghĩa API.
6. **FinalValidator:** kiểm tra CFG/data-flow/call graph hay context có thật, tính khả đạt của sink và guard trước sink. Bác bỏ nếu có chứng cứ protection ngăn **mọi** đường khả thi phù hợp giả thuyết; giữ candidate có đường hợp lý nhưng chưa bị bác bỏ, kèm mức bất định. Phân biệt `candidate`, `retained hypothesis`, `confirmed by ground truth`; đầu ra của mô hình không phải chứng minh khai thác thành công.
7. **Output:** JSON có version schema, mã mẫu/pair, quyết định, CWE, sink/line, điều kiện, đường đi, context evidence (file/line/commit), nguyên nhân giữ/bác, agent nguồn, chi phí, lỗi/timeout và bản ghi trung gian. Áp dụng schema validation, retry có giới hạn và trạng thái lỗi rõ ràng; không biến JSON lỗi thành dự đoán âm thầm.

Thử pipeline trên một cặp vulnerable/fixed nhỏ có nhãn đúng và một ví dụ false positive bị chặn bởi guard. Demo phải đi qua ít nhất một trace từ candidate → giả thuyết → kiểm tra điều kiện → quyết định cuối; thêm ví dụ ngữ cảnh ở hàm gọi nếu tìm được. Khi giải thích “multi-agent”, nêu rõ các vai trò là những lời gọi/luồng xử lý nào trong code, không cần nhiều model khác nhau hay nhiều máy chạy đồng thời.

## 4. Giai đoạn C — Tái hiện thực nghiệm

1. Trích nguyên văn **giao thức cần thiết** từ bài báo bằng diễn giải và trỏ số trang/bảng: ACL dùng **435 cặp** PrimeVul ở tập test; SVEN có **803 cặp tổng cộng**, split **8:1:1** (xác định đúng test IDs thực tế); arXiv cũ mô tả split SVEN khác, ghi lại thay đổi. Xác minh PrimeVul context được cung cấp cho bao nhiêu cặp và context SVEN được xây bằng công cụ nào. Không sử dụng nhãn thật/CWE oracle ở thí nghiệm thông thường.
2. Dùng một bản dữ liệu và một tập pair IDs **cố định** cho mọi phương pháp so sánh; chạy thử nhỏ để kiểm tra parser, nhãn, context, chi phí; sau đó chạy tập con có quy tắc lấy mẫu công khai hoặc toàn bộ test nếu đủ tài nguyên. Lưu IDs mẫu bị lỗi/timeout, số mẫu thành công và cách xử lý thiếu dữ liệu. Với chạy đủ quy mô, theo mô tả ACL, thử **3 lượt** và báo trung bình cùng biến thiên; nếu chỉ một lượt, ghi rõ.
3. Baseline tối thiểu là one-shot/CoT cùng backend, cùng đầu vào và cùng context; thêm Semgrep hoặc phương pháp có mã gốc khi có thể. Với baseline xuất bản GPTLens/VulTrial, chỉ nhận là “tái hiện” nếu thực thi giao thức tương ứng; nếu chỉ so sánh với số liệu in trong bài, ghi đó là **tham chiếu lịch sử, không phải chạy cùng điều kiện**. Không áp so sánh chi phí/chất lượng khác model mà không làm rõ.
4. Chạy và so sánh `ACC`, `precision`, `recall`, `F1`, `FPR = FP/(FP+TN)`, `P-C`, `P-R`, `VPS=P-C−P-R`; đặc biệt theo **ACL 2026**, `P-R` là cặp bị đảo nhãn: vulnerable→benign và fixed→vulnerable. Kiểm tra code metric có đúng định nghĩa; bản arXiv mô tả P-R không nhất quán, ghi rõ sự khác biệt. Báo confusion matrix, bảng per-CWE nếu số mẫu đủ và không dùng tỷ lệ với mẫu số bằng 0. Gắn cặp theo ID, không dựa vào thứ tự file.
5. Tối thiểu một **ablation** có đối chứng: full pipeline so với bỏ AssumptionPruner, bỏ FinalValidator, hoặc bỏ context; giữ cùng model, cùng IDs và config. Nếu làm RQ5 `oracle-CWE`, chỉ cung cấp CWE thật ở riêng thí nghiệm đó và ghi rõ đây là phân tích tầng validation, không được dùng để tuyên bố hiệu năng triển khai thực tế. Ghi candidate count qua từng giai đoạn, số TP/FP bị loại và FN phát sinh.
6. Lưu kết quả thô dạng JSONL/CSV, script tái tính toàn bộ bảng, lệnh chạy và log chi phí (API calls, tokens, thời gian, số lỗi). Báo khoảng tin cậy hoặc ít nhất số mẫu và phương sai nếu có nhiều lượt. Phân tích ít nhất 3 ca: true positive, false positive đã loại, false negative hoặc false positive còn sót; đối chiếu source/sink/guard với code thật, không suy đoán exploit ngoài bằng chứng.

## 5. Giai đoạn D — Điểm cộng và biện luận

Sau khi đã có baseline và full pipeline cùng một tập mẫu, chọn **một** hướng có đối chứng: (a) bổ sung context có chọn lọc theo giả thuyết so với context gốc/không context; (b) bộ dữ liệu mới gồm cặp vulnerable/fixed độc lập cùng loại CWE, có commit và nhãn kiểm chứng; (c) kiểm tra độ bền khi thiếu context. Dùng chung tập đánh giá, model và chi phí/giới hạn như thí nghiệm đối chứng. Ghi trước giả thuyết nghiên cứu, tiêu chí thành công, rủi ro leakage và cách đánh giá; chỉ kết luận nếu số liệu hỗ trợ.

Biện luận ưu/nhược: coverage nhờ nhiều góc kiểm tra; giảm báo cáo mang tính phỏng đoán nhờ điều kiện/đường đi và bảo vệ trước sink; độ nhạy với chất lượng context, false negative từ pruning, các giả định API không được chứng thực, độ trễ/token/API cost, tính phụ thuộc model và split, giới hạn của nhãn bộ dữ liệu. Tránh mô tả đây là máy quét bảo đảm an toàn.

## 6. Phân công 3 người và mốc nghiệm thu

| Thành viên | Trách nhiệm chính | Bằng chứng bàn giao | Trách nhiệm hỗ trợ |
|---|---|---|---|
| Người 1 — phương pháp & tài liệu | Đọc hai bản paper; bảng đối chiếu kiến trúc/metric; viết phần bối cảnh, phương pháp, ưu nhược; dẫn nguồn theo trang/bảng; làm slide tổng quan | `docs/source_audit.md`, sơ đồ pipeline, báo cáo phương pháp, phần slide | Review code pipeline và giải thích trace trong demo |
| Người 2 — hiện thực & demo | Kiểm toán repo/config/key; làm chạy được pipeline gốc hoặc adapter được ghi nhận; schema/log; ví dụ vulnerable/fixed và demo | mã + lệnh chạy + trace trung gian + video/kịch bản demo dự phòng | Review tính đúng đắn dữ liệu và metric |
| Người 3 — dữ liệu & thực nghiệm | Chốt split/pair IDs/context; baseline; thí nghiệm chính, ablation, metric, bảng biểu; theo dõi token/chi phí | manifest, scripts metric, kết quả thô, bảng so sánh, phần slide thực nghiệm | Review ngữ nghĩa candidate/guard cùng Người 1–2 |

Mỗi mốc cần review chéo ít nhất một người khác. Mốc 1: hoàn thành audit + manifest + ước lượng ngân sách; Mốc 2: demo pipeline một cặp và báo trace; Mốc 3: baseline + full pipeline cùng tập; Mốc 4: ablation/điểm cộng; Mốc 5: báo cáo, slide, chạy thử thuyết trình. Cả 3 phải tự giải thích được vai trò của từng giai đoạn, metric, một trường hợp hệ thống đúng và một trường hợp hệ thống sai.

## 7. Cấu trúc bàn giao và cách bạn làm việc

Đề xuất cấu trúc (tận dụng cấu trúc repo nếu đã có): `configs/`, `src/` hoặc mã gốc, `scripts/`, `tests/` cho parser/metric/cặp dữ liệu, `data/README.md` (không commit dữ liệu bị cấm), `results/raw/`, `results/tables/`, `docs/`, `slides/`, `.env.example`, `README.md`, `experiment_manifest.yaml`. Không chuyển key từ repository gốc vào code/file/log mới.

Khi bắt đầu: xuất bảng **tình trạng repo và nguồn**, **việc nào thực hiện được ngay**, **rào cản thật sự** và **ước tính chạy**; sau đó làm tuần tự Giai đoạn A→D. Sau mỗi mốc báo: file đã thay đổi, lệnh đã chạy, kết quả thực tế, số liệu chưa xác minh, bước kế tiếp. Tập trung tạo sản phẩm hoạt động; đừng thay mọi module bằng giả lập hay dừng ở skeleton. Nếu phụ thuộc API/chi phí không có, hoàn thành toàn bộ việc ngoại tuyến (audit, chuẩn dữ liệu, schema, metric, script baseline, demo với dữ liệu/đầu ra có provenance), ghi trạng thái rõ và hỏi đúng quyền/truy cập còn thiếu.

Tiêu chuẩn hoàn thành: người khác clone đúng commit, cung cấp key riêng, chạy theo README và tạo lại bảng từ kết quả thô; demo thấy từng bước của một cặp; slide ánh xạ được từng tiêu chí chấm vào file, số liệu hoặc trace; mọi chênh lệch với bài báo đều có giải thích và nguồn.

## 8. Kiến thức cần đọc theo tiến độ (chỉ tên chủ đề)

| Giai đoạn | Chủ đề cần đọc |
|---|---|
| Trước khi kiểm toán | C/C++ memory model; Python cơ bản; secure code review; CWE-125, CWE-476, CWE-787, CWE-416, CWE-78, CWE-862; Git/GitHub; đọc bài báo và phụ lục khoa học |
| Trước khi chuẩn hóa pipeline | Static analysis; source–sink–sanitizer; control-flow graph (CFG); data-flow graph (DFG); call graph; code property graph; taint analysis; path feasibility; dominance/guard dominance; program slicing; Joern |
| Trước khi chạy agent | LLM prompting; tool calling; multi-agent orchestration; structured JSON output; schema validation; prompt injection từ mã nguồn; API secret management; token accounting; rate limiting |
| Trước khi thực nghiệm | PrimeVul; SVEN; vulnerable–fixed pairs; train/validation/test split; data leakage; confusion matrix; precision/recall/F1/ACC/FPR; P-C/P-R/VPS; ablation study; experimental reproducibility |
| Trước khi báo cáo | Error analysis; threats to validity; statistical uncertainty; baseline fairness; slide design; live demo rehearsal; nguồn trích dẫn khoa học |

