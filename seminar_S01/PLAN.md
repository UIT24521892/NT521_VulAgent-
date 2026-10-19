# Kế hoạch mini seminar S01 — Stack-based buffer overflow

Yêu cầu chuẩn của đề: [REQUIREMENTS.md](REQUIREMENTS.md). Nguồn: tách từ [../_archive/Huong_dan_hoc_va_thuc_hien_S01_VulAgent.md](../_archive/Huong_dan_hoc_va_thuc_hien_S01_VulAgent.md). Quy tắc: [../AGENT.md](../AGENT.md).

## 0. Việc cần làm ngay

1. [ ] Chốt ngày seminar, tên thành viên, người phụ trách chính.
2. [ ] Trên Kali/UTM chạy `uname -m` và xác nhận kiến trúc VM (ARM64 hay x86-64).
3. [ ] Tải ROP Emporium `ret2win` đúng kiến trúc, chạy `file ./ret2win` — lưu output vào [evidence/](evidence/).
4. [ ] Làm **bài tập chung đầu tiên** (mục 2) và lưu vào [notes/](notes/).
5. [ ] Đọc advisory CVE-2015-7547, tạo [cve/CVE-2015-7547.md](cve/) theo mẫu ở mục 4.
6. [ ] Chốt challenge + CVE (xem README), ghi vào bảng quyết định.

## 1. Mục tiêu

Áp dụng cách phân tích source → sink → điều kiện → guard → kết luận cho một lỗi tràn bộ đệm trên stack, một CVE thực tế và một challenge CTF trong môi trường được phép. Đầu ra: slide + demo lặp lại được. CVE chỉ nghiên cứu và trình bày.

## 2. Học nền theo thứ tự

Chi tiết trong [KNOWLEDGE.md](KNOWLEDGE.md).

**Bài tập chung đầu tiên:** chọn 3 đoạn mã C ngắn: (1) một đoạn có lỗi, (2) bản sửa, (3) đoạn trông nguy hiểm nhưng đã có guard. Mỗi người tự viết: source, sink, kích thước vùng đệm, điều kiện gây lỗi, guard, kết luận. Cả nhóm phản biện chéo **trước khi chọn bài demo**. Lưu ở `notes/bai_tap_3_doan_ma/`.

## 3. Kế hoạch theo 10 mục của đề

| Mục yêu cầu | Kiến thức và việc phải chuẩn bị | Bằng chứng trên slide/demo |
|---|---|---|
| 1. Giới thiệu lỗ hổng và **bối cảnh sử dụng** | Buffer trên stack là gì; dữ liệu vào từ tệp, mạng hoặc người dùng; lỗi thường gặp ở đâu (C/C++, dịch vụ mạng, thư viện hệ thống, firmware); tác động thay đổi theo chương trình | Ví dụ input quá dài, mục tiêu của chương trình, một vài bối cảnh thực tế |
| 2. Nguyên lý, điều kiện, dạng phổ biến | Sao chép/đọc vượt dung lượng, off-by-one, sai phép tính độ dài, ký tự `\0`; phân biệt crash với điều khiển luồng thực thi | Sơ đồ stack, số byte cấp phát và số byte có thể ghi |
| 3. CWE và liên hệ với chủ đề được phân công | CWE-121 là vùng đệm bị ghi tràn nằm trên stack; quan hệ với CWE-787; lý do chọn CWE; **liên hệ với chủ đề S01** (stack-based buffer overflow chính là CWE-121) | Trích định nghĩa MITRE và ánh xạ vào đúng vị trí lỗi |
| 4. Vị trí và nguyên nhân | Theo dấu input đến phép ghi; có source thì chỉ dòng lỗi, chỉ có binary thì chỉ hàm và lệnh liên quan | Ảnh source/disassembly đánh dấu sink, tham số, kích thước |
| 5. Nguyên lý và chuỗi khai thác | Input → ghi vượt → thay đổi dữ liệu → quan sát kết quả; nêu điều kiện từng bước | Sơ đồ 4–5 bước bám sát chính challenge |
| 6. Ít nhất một CVE | Sản phẩm bị ảnh hưởng, thành phần, nguyên nhân, dữ liệu do đối phương kiểm soát, **điều kiện khai thác**, tác động, **biện pháp khắc phục** (bản vá, cấu hình giảm thiểu nếu có). Chỉ nghiên cứu/trình bày, không cần tái hiện | Bảng tóm tắt và đường dẫn advisory/bản vá |
| 7. Demo CTF Pwnable | Chọn challenge hợp kiến trúc VM; phân tích binary, thực hiện trong môi trường **được cấp phép, cô lập, an toàn** | Input bình thường, vị trí lỗi, trạng thái debugger, kết quả challenge |
| 8. Khắc phục và phòng ngừa | Giới hạn ghi theo dung lượng đích; kiểm tra kết quả; ASan khi kiểm thử; canary/NX/ASLR/PIE | Mã lỗi cạnh mã đã sửa; bảng tác dụng từng lớp bảo vệ |
| 9. Điều kiện và giới hạn | Input có tới sink không, độ kiểm soát input, bố cục stack, kiến trúc, bản vá và bảo vệ của binary | Bảng: đã xác nhận / chưa xác nhận / ảnh hưởng |
| 10. Kết luận | Bài học từ challenge và CVE, mức tác động đã chứng minh, cách ngăn lỗi | 3 ý kết luận ngắn, không phóng đại |

## 4. Hai ví dụ gợi ý để chốt sớm

- **Challenge:** [ROP Emporium – ret2win](https://ropemporium.com/challenge/ret2win.html). Mục tiêu: điều khiển địa chỉ trả về để gọi một hàm có sẵn. Phải phân tích binary thực tế; **không dùng sơ đồ stack minh họa để khẳng định offset** của binary.
- **CVE:** [CVE-2015-7547 trong glibc](https://access.redhat.com/articles/2161461) — tràn bộ đệm stack khi xử lý phản hồi DNS qua `getaddrinfo()`. Đọc thêm [phân tích của Google](https://security.googleblog.com/2016/02/cve-2015-7547-glibc-getaddrinfo-stack.html) và [bản vá glibc](https://sourceware.org/pipermail/libc-alpha/2016-February/068625.html). Xác nhận phạm vi phiên bản theo advisory của nhà cung cấp; các bản phân phối có thể backport.

**Máy của nhóm:** Kali qua UTM trên Mac Apple Silicon. Kiểm tra `uname -m` và `file ./ret2win` **trước khi chọn binary**. ROP Emporium có nhiều kiến trúc; nếu không khớp VM, chuẩn bị môi trường phù hợp từ đầu.

**Mẫu ghi chú CVE** (`cve/CVE-xxxx-xxxx.md`): sản phẩm & thành phần | CWE | nguyên nhân gốc | dữ liệu do đối phương kiểm soát | điều kiện kích hoạt | tác động | phiên bản bị ảnh hưởng | bản vá (link + thay đổi) | nguồn tham khảo (đã xác nhận ngày).

## 5. Kịch bản demo và ảnh cần lưu

| # | Bước | Ảnh lưu vào `evidence/` |
|---|---|---|
| 1 | Kiểm tra tên binary, kiến trúc, thuộc tính bảo vệ đang bật | `01_kiem_tra_binary.png` — lệnh + output |
| 2 | Chạy input bình thường để có mốc so sánh | `02_chay_binh_thuong.png` |
| 3 | Chỉ vị trí nhận input và vùng đệm đích trong source/disassembly | `03_sink_va_buffer.png` — khoanh lệnh, ghi kích thước |
| 4 | Debugger: input làm thay đổi dữ liệu nào; ghi offset **đo trên binary này** | `04_debugger_truoc_sau.png` — trạng thái trước/sau |
| 5 | Chạy lời giải challenge trong môi trường CTF | `05_ket_qua_challenge.png` + giải thích vì sao có kết quả |
| 6 | Cách sửa phép đọc/ghi, rồi các lớp bảo vệ | `06_ma_loi_vs_ma_sua.png` + bảng bảo vệ |

**Mức bằng chứng:** "có ghi vượt", "chương trình crash", "đã thay đổi địa chỉ trả về", "đạt mục tiêu challenge" là bốn nhận định khác nhau. Chỉ nói điều đã kiểm chứng.

Dự phòng: quay video hoặc chuẩn bị bộ ảnh + lệnh để trình bày nếu demo trực tiếp lỗi.

## 6. Bố cục và thời gian

Khoảng **12–14 slide**: 2 nền tảng; 2 nguyên lý/CWE; 2 CVE; 4–5 phân tích và demo; 2 sửa lỗi/giới hạn; 1 kết luận/tài liệu.

Đối chiếu khoảng gợi ý của đề ([REQUIREMENTS.md](REQUIREMENTS.md)):

| Phần | Đề gợi ý | Kế hoạch (phút) |
|---|---|---|
| Kiến thức nền tảng và CWE (mục 1–3) | 5–6 | 6 |
| Phân tích CVE (mục 6) | 3–4 | 4 |
| Phân tích mã/binary và demo CTF (mục 4, 5, 7) | 8–12 | 10 |
| Khắc phục, phòng ngừa, giới hạn, kết luận (mục 8–10) | 3–5 | 4 |
| Hỏi đáp | 2–3 | 2 |
| **Tổng** | 21–30 | **26** |

Dự trữ: nếu bị giới hạn 20 phút thì rút demo/CVE xuống mức đề cho phép tối thiểu (5+3+8+3+2 = 21, cần cắt thêm ~1 phút ở phần nền).

## 7. Lịch 3 tuần và đầu ra

Nếu hạn gần có thể gộp tuần 1–2. Mốc "tuần" đếm từ ngày bắt đầu `[CHƯA CHỐT]`.

| Tuần | Học và làm | Đầu ra kiểm tra được | Xong |
|---|---|---|---|
| 1 | Học nền C, stack, CWE-121/787, source–sink–guard, CFG; chọn challenge/CVE; kiểm tra kiến trúc VM | 3 đoạn mã được phân tích chéo; challenge chạy được trên môi trường chọn | [ ] |
| 2 | Phân tích binary và CVE, thu ảnh demo, làm slide nháp | Bản nháp seminar; demo lặp lại được | [ ] |
| 3 | Tập thuyết trình (bấm giờ 20–30 phút), diễn tập hỏi đáp | Seminar hoàn chỉnh; demo chạy ≥ 2 lần liên tiếp | [ ] |

## 8. Phân công (S01)

| Vai trò | Việc |
|---|---|
| A (chính) | C/stack, debugger, CWE/CVE, phân tích và demo |
| B | Nắm lỗi S01; hỗ trợ sơ đồ/slide; review logic source–sink–guard |
| C | Phản biện chéo bài tập, rà soát nguồn và độ chính xác phát biểu |

Ba buổi cả nhóm cùng làm: (1) phân tích một cặp vulnerable/fixed; (2) tìm guard có thật sự chặn mọi đường tới sink; (3) xem một ca false positive và chỉ ra giả định sai *(buổi 3 chủ yếu phục vụ VulAgent nhưng thực hành chung cách phân tích)*. Mỗi tuần cập nhật bảng chung: việc đã xong, bằng chứng, vướng mắc, người phụ trách, mốc tiếp theo — ghi vào nhật ký [../ROADMAP.md](../ROADMAP.md).

## 9. Tài liệu đọc

- [MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html), [CWE-787](https://cwe.mitre.org/data/definitions/787.html)
- [ROP Emporium ret2win](https://ropemporium.com/challenge/ret2win.html)
- [Red Hat: CVE-2015-7547](https://access.redhat.com/articles/2161461), [Google Security Blog](https://security.googleblog.com/2016/02/cve-2015-7547-glibc-getaddrinfo-stack.html)
- [GCC stack protector](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html), [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)

**Ưu tiên khi thiếu thời gian:** hoàn thành ca phân tích thủ công và demo S01 trước; bỏ phần mở rộng.
