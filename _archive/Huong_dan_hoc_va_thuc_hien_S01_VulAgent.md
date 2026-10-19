# Kế hoạch học và thực hiện mini seminar S01 + đề tài VulAgent

**Chủ đề mini seminar:** S01 – Stack-based buffer overflow  
**Đề tài chính:** VulAgent – phát hiện lỗ hổng mã nguồn bằng quy trình lập và kiểm chứng giả thuyết  
**Thời lượng mini seminar:** 20–30 phút, gồm hỏi đáp  
**Cách dùng:** Cả nhóm học phần nền chung; từng người đào sâu phần được phân công. Đánh dấu checklist sau mỗi buổi làm việc.

## 1. Mục tiêu và mối liên hệ giữa hai phần

Hai phần sử dụng chung một cách phân tích: **đầu vào (source) → đường dữ liệu/đường thực thi → thao tác nhạy cảm (sink) → điều kiện để lỗi xảy ra → kiểm tra guard và ngữ cảnh → kết luận có bằng chứng**.

- **S01:** áp dụng cách phân tích này cho một lỗi tràn bộ đệm trên stack, một CVE thực tế và một challenge CTF trong môi trường được phép.
- **VulAgent:** hiện thực hoặc tái lập một phần pipeline dùng nhiều vai trò phân tích để nêu, kiểm tra và sàng lọc giả thuyết lỗ hổng; đánh giá bằng dữ liệu và metric.
- **Điểm nối hữu ích:** lưu lại cách nhóm phân tích thủ công mã vulnerable/fixed của S01 để thiết kế schema đầu ra và phần giải thích của prototype VulAgent. Không xem kết quả CTF là kết quả benchmark.

**Hai sản phẩm cần tách bạch:** (1) slide + demo S01; (2) mã pipeline + dữ liệu đánh giá + báo cáo VulAgent. CVE của S01 chỉ cần nghiên cứu và trình bày, không cần tái hiện khai thác.

## 2. Kiến thức nền: học theo thứ tự

| Ưu tiên | Chủ đề | Cần tự làm được | Dùng ở đâu |
|---|---|---|---|
| 1 | C căn bản: mảng, con trỏ, `char[]`, `sizeof`, độ dài chuỗi, ký tự `\0` | Tính dung lượng vùng đệm và lượng dữ liệu có thể ghi; chỉ ra lỗi off-by-one | S01 và ví dụ bộ nhớ của VulAgent |
| 1 | Bộ nhớ tiến trình: stack frame, biến cục bộ, heap, địa chỉ trả về | Vẽ stack frame **minh họa**, rồi xác nhận bố cục thực tế trong binary | Phân tích mã/binary S01 |
| 1 | Source–sink–guard | Chỉ ra input, sink, mọi phép kiểm tra trên đường tới sink; giải thích guard có chặn mọi đường hay không | Trọng tâm cả hai phần |
| 1 | CWE-121 và CWE-787 | Phân biệt tràn bộ đệm **trên stack** với loại ghi ngoài biên tổng quát; phân biệt CWE với CVE | S01; phân loại ca kiểm thử |
| 2 | CFG, data flow, call graph, reachability và feasibility | Vẽ CFG cho hàm nhỏ có `if`/`return`; nêu một đường có trên CFG nhưng không thực thi được | Điều kiện khai thác; kiểm chứng giả thuyết |
| 2 | Debugger và binary: kiến trúc, thanh ghi, stack, disassembly | Dùng GDB quan sát hàm lỗi, trạng thái trước/sau input, và kết quả; không suy kết quả chỉ từ crash | Demo S01 |
| 2 | Stack canary, NX, ASLR, PIE; kiểm tra biên và AddressSanitizer | Nói được mỗi cơ chế bảo vệ tác động ở đâu và giới hạn của nó; đề xuất sửa mã tận gốc | S01, khuyến nghị khắc phục |
| 2 | Python, Git, JSON/JSONL, schema, unit test | Ghi và đọc các lần chạy, kiểm tra định dạng đầu ra, lưu phiên bản cấu hình | Prototype VulAgent |
| 3 | CWE-125/416/476/78/862; program slicing, CPG/Joern | Phân tích khi gặp mẫu tương ứng; thử công cụ nếu pipeline cần ngữ cảnh dự án | Mở rộng VulAgent |
| 3 | Dataset, baseline, precision/recall/F1/FPR, metric theo cặp, ablation | Tính metric bằng tay trên tập nhỏ rồi đối chiếu script; so sánh cùng tập mẫu | Thực nghiệm VulAgent |

**Bài tập chung đầu tiên:** chọn 3 đoạn mã C ngắn gồm một đoạn có lỗi, một bản sửa, một đoạn trông nguy hiểm nhưng đã có guard. Mỗi người tự viết: source, sink, kích thước vùng đệm, điều kiện gây lỗi, guard và kết luận. Cả nhóm phản biện chéo trước khi chọn bài demo.

## 3. Kế hoạch mini seminar S01 theo đúng cấu trúc đề

| Mục yêu cầu | Kiến thức và việc phải chuẩn bị | Bằng chứng trên slide/demo |
|---|---|---|
| 1. Giới thiệu và bối cảnh | Buffer trên stack là gì; dữ liệu đi vào từ tệp, mạng hoặc người dùng; tác động có thể thay đổi theo chương trình | Ví dụ input quá dài, mục tiêu của chương trình |
| 2. Nguyên lý, điều kiện, dạng phổ biến | Sao chép/đọc vượt dung lượng, off-by-one, sai phép tính độ dài, ký tự `\0`; phân biệt crash với điều khiển luồng thực thi | Sơ đồ stack, số byte cấp phát và số byte có thể ghi |
| 3. CWE | CWE-121 là vùng đệm bị ghi tràn nằm trên stack; quan hệ với CWE-787; lý do chọn CWE | Trích định nghĩa MITRE và ánh xạ vào đúng vị trí lỗi |
| 4. Vị trí và nguyên nhân | Theo dấu input đến phép ghi; khi có source chỉ dòng lỗi; khi chỉ có binary chỉ hàm và lệnh liên quan | Ảnh source/disassembly đánh dấu sink, tham số và kích thước |
| 5. Nguyên lý và chuỗi khai thác | Các bước input → ghi vượt → thay đổi dữ liệu → quan sát kết quả; nêu điều kiện từng bước | Sơ đồ 4–5 bước bám sát chính challenge |
| 6. Ít nhất một CVE | Sản phẩm, thành phần, nguyên nhân, dữ liệu do đối phương kiểm soát, điều kiện, tác động, bản vá | Bảng tóm tắt và đường dẫn advisory/bản vá |
| 7. Demo CTF Pwnable | Chọn challenge hợp kiến trúc VM; phân tích binary và thực hiện trong môi trường cô lập, được phép | Input bình thường, vị trí lỗi, trạng thái debugger, kết quả challenge |
| 8. Khắc phục và phòng ngừa | Giới hạn ghi theo dung lượng đích; kiểm tra kết quả; ASan khi kiểm thử; canary/NX/ASLR/PIE | Mã lỗi cạnh mã đã sửa; bảng tác dụng của từng lớp bảo vệ |
| 9. Điều kiện và giới hạn | Input có tới sink không, độ kiểm soát input, bố cục stack, kiến trúc, bản vá và bảo vệ của binary | Bảng điều kiện: đã xác nhận / chưa xác nhận / ảnh hưởng |
| 10. Kết luận | Bài học từ challenge và CVE, mức tác động đã chứng minh, cách ngăn lỗi | 3 ý kết luận ngắn, không phóng đại kết quả |

### Gợi ý hai ví dụ để chốt sớm

- **Challenge:** [ROP Emporium – ret2win](https://ropemporium.com/challenge/ret2win.html). Mục tiêu của challenge là điều khiển địa chỉ trả về để gọi một hàm có sẵn. Nhóm phải phân tích binary thực tế; không dùng sơ đồ stack minh họa để khẳng định offset của binary.
- **CVE:** [CVE-2015-7547 trong glibc](https://access.redhat.com/articles/2161461), liên quan tràn bộ đệm trên stack khi xử lý phản hồi DNS qua `getaddrinfo()`. Đọc thêm [phân tích của nhóm nghiên cứu Google](https://security.googleblog.com/2016/02/cve-2015-7547-glibc-getaddrinfo-stack.html) và [bản vá glibc](https://sourceware.org/pipermail/libc-alpha/2016-February/068625.html). Xác nhận phạm vi phiên bản theo advisory của nhà cung cấp; các bản phân phối có thể backport bản vá.

**Máy của nhóm:** trên Kali chạy qua UTM ở Mac Apple Silicon, kiểm tra `uname -m` và `file ./ret2win` trước khi chọn binary. ROP Emporium cung cấp các kiến trúc khác nhau; nếu kiến trúc VM không khớp, cần chuẩn bị môi trường phù hợp từ đầu.

### Kịch bản demo và ảnh cần lưu

1. Kiểm tra tên binary, kiến trúc và các thuộc tính bảo vệ đang bật. **Ảnh 1:** lệnh kiểm tra cùng output.
2. Chạy input bình thường để có mốc so sánh. **Ảnh 2:** chương trình hoạt động bình thường.
3. Chỉ vị trí nhận input và vùng đệm đích trong source/disassembly. **Ảnh 3:** khoanh vùng lệnh và ghi kích thước.
4. Dùng debugger quan sát input làm thay đổi dữ liệu nào; ghi offset **đo trên binary này**. **Ảnh 4:** trạng thái trước/sau và giải thích ngắn.
5. Chạy lời giải challenge trong môi trường CTF. **Ảnh 5:** kết quả và lời giải thích vì sao kết quả xuất hiện.
6. Trình bày cách sửa phép đọc/ghi, sau đó giải thích các lớp bảo vệ. **Ảnh/slide 6:** mã lỗi so với mã sửa và bảng bảo vệ.

**Mức bằng chứng cần nói rõ:** “có ghi vượt”, “chương trình crash”, “đã thay đổi địa chỉ trả về”, “đạt mục tiêu challenge” là bốn nhận định khác nhau. Chỉ phát biểu điều nhóm đã kiểm chứng.

### Bố cục và thời gian

Khoảng **12–14 slide**: 2 slide nền tảng; 2 slide nguyên lý/CWE; 2 slide CVE; 4–5 slide phân tích và demo; 2 slide sửa lỗi/giới hạn; 1 slide kết luận/tài liệu. Tập theo nhịp **6 phút nền tảng + 4 phút CVE + 10 phút mã và demo + 4 phút khắc phục/kết luận + 2 phút hỏi đáp = 26 phút**.

## 4. Kế hoạch đề tài chính VulAgent

### 4.1. Đọc paper để hiểu phương pháp

Đọc [bản ACL Findings 2026](https://aclanthology.org/2026.findings-acl.928/) làm mốc trích dẫn chính; đối chiếu [bản arXiv 2509.11523](https://arxiv.org/abs/2509.11523) khi cần. Thứ tự đọc: **hình kiến trúc → một ví dụ xuyên suốt → nhiệm vụ và input/output từng agent → thiết kế dữ liệu/metric → kết quả/ablation → phụ lục prompt**.

Sau khi đọc, cả nhóm phải trả lời bằng một mẫu mã duy nhất:

1. Agent phân tích phát hiện sink nào và nêu nghi vấn gì?
2. TriggerPlanner xây điều kiện và đường kích hoạt ra sao?
3. AssumptionPruner kiểm tra giả định nào bằng context nào?
4. FinalValidator xem guard/cơ chế bảo vệ nào trước kết luận?
5. Nếu context thiếu, kết luận có thể sai theo hướng nào?

Tên giai đoạn, schema, cách chia dữ liệu và metric cần trích đúng **phiên bản paper nhóm chọn**. File kiến thức ban đầu lưu ý có chỗ mô tả P-R và split SVEN khác nhau giữa bản arXiv và ACL; đối chiếu tài liệu và code trước khi lập báo cáo.

### 4.2. Prototype tối thiểu cần có

- Input: một đơn vị mã và context tương ứng, có ID ổn định; biết nhãn thật chỉ ở bước đánh giá.
- Output phân tích: sink, CWE nghi vấn, điều kiện giả thuyết, trigger path, chứng cứ/guard, quyết định cuối và trạng thái `unknown` khi thiếu dữ liệu.
- Kiểm tra JSON schema; log lỗi phân tích cú pháp riêng, không tự biến output lỗi thành nhãn `benign`.
- Chạy một cặp vulnerable/fixed từ đầu tới cuối và lưu output từng bước.
- Ghi model/prompt/config/ngày chạy, số token hoặc chi phí; không đưa API key vào repo hay log.

**Mốc hoàn thành prototype:** người khác có thể mở một ca và lần ngược từ kết luận về source, sink, guard và bằng chứng mà hệ thống đã dùng.

### 4.3. Thực nghiệm và báo cáo

- Chốt danh sách mẫu và cách chia dữ liệu trước khi chạy. Đảm bảo bản vulnerable và fixed không bị dùng để tiết lộ nhãn cho nhau trong prompt.
- Tính ACC, precision, recall, F1, FPR và metric theo cặp đúng định nghĩa đã chọn; kiểm tra script bằng một bảng TP/FP/TN/FN nhỏ tính tay.
- Chạy baseline và prototype trên cùng ID mẫu, cùng cấu hình có thể so sánh; đánh dấu rõ số trích từ paper là tham chiếu lịch sử.
- Ablation: bỏ đúng một thành phần, giữ nguyên mẫu, model và prompt còn lại khi có thể.
- Phân tích ít nhất 3 ca: TP, một FP được loại nhờ kiểm chứng, và một FN hoặc FP còn sót. Chỉ ra source/sink/guard trên code thật.
- Ghi giới hạn: chất lượng nhãn, thiếu context, nhiễm dữ liệu huấn luyện, tính biến động của model và kích thước mẫu.

## 5. Lộ trình thực hiện 7 tuần có đầu ra rõ ràng

Nếu hạn nộp gần, có thể gộp tuần 1–2 hoặc 4–5; giữ nguyên thứ tự các mốc kiểm chứng.

| Thời điểm | Học và làm | Đầu ra kiểm tra được |
|---|---|---|
| Tuần 1 | Học nền C, stack, CWE-121/787, source–sink–guard, CFG; chọn challenge/CVE; kiểm tra kiến trúc VM | 3 đoạn mã được phân tích chéo; challenge chạy được trên môi trường chọn |
| Tuần 2 | Phân tích binary và CVE, thu ảnh demo, làm slide nháp; đọc hình kiến trúc và một ví dụ trong paper | Bản nháp seminar và demo lặp lại được; sơ đồ luồng VulAgent bằng lời nhóm tự giải thích |
| Tuần 3 | Tập thuyết trình S01; dựng repo Python, schema và pipeline chạy một cặp vulnerable/fixed | Seminar 20–30 phút; log đầy đủ một cặp qua từng giai đoạn |
| Tuần 4 | Chốt dữ liệu, IDs, baseline và công thức metric; kiểm tra rò rỉ nhãn | Manifest mẫu, script metric kiểm tra bằng tay, bảng baseline đầu tiên |
| Tuần 5 | Chạy thí nghiệm chính theo cấu hình đã khóa; theo dõi log, token, lỗi | Bảng kết quả có thể tính lại từ file dự đoán |
| Tuần 6 | Ablation và phân tích FP/FN; rà soát bản paper được trích | Bảng ablation và 3 ca giải thích chi tiết |
| Tuần 7 | Viết báo cáo, hoàn tất demo, diễn tập hỏi đáp | Báo cáo, slide, mã nguồn, manifest và kịch bản demo dự phòng |

## 6. Phân công cho nhóm 3 người

| Vai trò chính | Học sâu và làm | Cả nhóm vẫn phải nắm |
|---|---|---|
| A – lỗ hổng và seminar | C/stack, debugger, CWE/CVE, phân tích và demo S01 | Luồng source–sink–guard và ý chính pipeline |
| B – phương pháp và hiện thực | Paper, CFG/data flow, agent, JSON schema, context retrieval, mã pipeline | Lỗi S01 và ý nghĩa từng metric |
| C – dữ liệu và đánh giá | PrimeVul/SVEN, metric, baseline, ablation, error analysis | Đọc được một giả thuyết lỗ hổng và phản biện guard |

Ba buổi cả nhóm nên cùng làm: **(1)** phân tích một cặp vulnerable/fixed; **(2)** tìm guard có thật sự chặn mọi đường tới sink; **(3)** xem một FP và chỉ ra giả định sai. Mỗi tuần cập nhật một bảng chung gồm: việc đã xong, bằng chứng, vướng mắc, người phụ trách và mốc tiếp theo.

## 7. Checklist nộp và tự kiểm tra

### Mini seminar S01

- [ ] Mọi mục 1–10 của đề đều có vị trí trong slide hoặc phần nói.
- [ ] CWE-121 được giải thích và gắn với đúng vùng đệm stack của ca minh họa.
- [ ] Có sơ đồ input → sink → ghi vượt → hậu quả, cùng bằng chứng trong code/binary.
- [ ] CVE có sản phẩm, nguyên nhân, tác động, điều kiện và bản vá; nguồn tham khảo rõ.
- [ ] Demo challenge chạy được ít nhất hai lần liên tiếp trên môi trường đã chốt.
- [ ] Ảnh minh chứng có chú thích giải thích điều ảnh chứng minh.
- [ ] Phân biệt crash với bằng chứng điều khiển luồng thực thi.
- [ ] Có mã sửa lỗi và phân tích canary/NX/ASLR/PIE theo binary cụ thể.
- [ ] Tổng thời gian có hỏi đáp nằm trong 20–30 phút.

### VulAgent

- [ ] Nhóm diễn giải được vai trò từng giai đoạn bằng một ca mã nguồn thật.
- [ ] Prototype chạy trọn một cặp vulnerable/fixed và lưu bằng chứng trung gian.
- [ ] Schema, parse error và trường hợp thiếu context được xử lý rõ.
- [ ] Tập mẫu, phiên bản paper/metric, cấu hình và ngày chạy được ghi lại.
- [ ] Metric được kiểm tra bằng tay trên mẫu nhỏ; baseline dùng cùng tập mẫu.
- [ ] Có một ablation đúng điều kiện so sánh và ít nhất 3 ca error analysis.
- [ ] Báo cáo nêu phần nhóm thực sự hiện thực, phần dùng lại và giới hạn kết quả.

## 8. Tài liệu đọc theo nhu cầu

- [MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html) và [CWE-787](https://cwe.mitre.org/data/definitions/787.html): định nghĩa và ví dụ.
- [ROP Emporium ret2win](https://ropemporium.com/challenge/ret2win.html): challenge và mục tiêu của demo.
- [Red Hat: CVE-2015-7547](https://access.redhat.com/articles/2161461), [Google Security Blog](https://security.googleblog.com/2016/02/cve-2015-7547-glibc-getaddrinfo-stack.html): ca CVE.
- [GCC stack protector](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html), [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html): bảo vệ và tìm lỗi.
- [VulAgent bản ACL](https://aclanthology.org/2026.findings-acl.928/) và [bản arXiv](https://arxiv.org/abs/2509.11523): phương pháp và thực nghiệm.

**Ưu tiên khi thiếu thời gian:** hoàn thành ca phân tích thủ công, demo S01 và pipeline chạy một cặp trước; học Joern/CPG, program slicing sâu và thống kê nâng cao khi những phần đó thực sự phục vụ câu hỏi thực nghiệm của nhóm.
