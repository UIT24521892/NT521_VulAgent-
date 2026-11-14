# Checklist mini seminar S05

Cập nhật: **2026-11-02** — đã mở rộng tài liệu kiến thức nền; ghi chú CVE có phân tích mã nguồn và bản vá; chưa có bài làm, binary, log/ảnh hoặc slide S05 trong thư mục hiện tại.

Chỉ đánh dấu khi có đầu ra S05 tương ứng. Tài liệu, challenge, CVE và bằng chứng được chuẩn bị độc lập cho return-to-libc. Kế hoạch chi tiết: [PLAN.md](PLAN.md).

**Quy ước:** mục “có tài liệu” xác nhận nội dung đã được biên soạn. Mục “giải thích/làm được” chỉ đánh dấu sau khi nhóm tự kiểm tra hoặc có bài làm được review; việc đã viết tài liệu chưa xác nhận nhóm đã học xong.

## Tài liệu và phạm vi

- [x] Có [REQUIREMENTS.md](REQUIREMENTS.md) ghi mô tả S05 và giữ đủ 10 mục yêu cầu chung; [PLAN.md](PLAN.md) cập nhật nội dung, demo, thời lượng và tiến độ.
- [x] Có [README.md](README.md) cho S05, ghi chủ đề, trạng thái quyết định và giới hạn demo dự kiến.
- [x] Có [KNOWLEDGE.md](KNOWLEDGE.md) mở rộng kiến thức nền; các nội dung đã chuẩn bị được liệt kê ở phần dưới.
- [x] Có checklist riêng cho S05; chưa đánh dấu kết quả demo, ảnh hay slide chưa làm.
- [x] 10 mục của đề có vị trí trong slide hoặc phần nói: [slides/noi_dung_chi_tiet.md](slides/noi_dung_chi_tiet.md) ánh xạ 10 mục → 14 slide, kèm lời giảng. Chưa dựng file slide trình chiếu.
- [ ] Ngày seminar, thành viên và phân công đã chốt.
- [ ] Chốt challenge sau khi kiểm tra khả năng chạy và phạm vi demo.

## Kiến thức nền: tài liệu đã chuẩn bị

Đối chiếu [KNOWLEDGE.md](KNOWLEDGE.md), cập nhật ngày 2026-10-21:

- [x] Mục 1.1: giải thích mảng/con trỏ, `sizeof`, `strlen`, dung lượng buffer và byte kết thúc `\0`.
- [x] Mục 1.2: có ví dụ C lỗi/bản sửa, bảng source–sink–guard và cách giới hạn `read()` khi xử lý chuỗi.
- [x] Mục 1.3–1.4: có sơ đồ stack frame, giải thích `call`/`ret`, saved return address và các mức bằng chứng từ ghi vượt đến đạt mục tiêu.
- [x] Mục 1.5: làm rõ CWE phân loại lỗi nền của ca phân tích; CWE-121 áp dụng khi có lỗi tràn buffer trên stack, không phải nhãn của ret2libc; mục 1.4 phân biệt thêm gọi qua PLT.
- [x] Mục 1.6: có hướng dẫn đọc disassembly/debugger và lưu ý về randomization trong GDB.
- [x] Mục 2–3: giải thích ABI x86/AMD64, `RDI`, alignment, `system()`/`syscall`, PLT/GOT và địa chỉ libc runtime.
- [x] Mục 4–6: có bảng tác dụng/giới hạn của bảo vệ, nguồn tham khảo, câu hỏi tự kiểm tra, bài tập và khung nói 5–6 phút.

## Học nền và bài tập chung

Học theo [KNOWLEDGE.md](KNOWLEDGE.md); lưu bài làm và kết quả review vào `notes/` khi thực hiện theo [PLAN.md mục 2](PLAN.md#2-học-nền-và-bài-tập-chung).

- [ ] Phân biệt được dung lượng buffer, độ dài C string, byte `\0` và số byte `read()` thực sự trả về.
- [ ] Giải thích được vì sao `sizeof` của con trỏ hoặc tham số mảng không cho dung lượng vùng đích.
- [ ] Lập bảng source–sink–guard cho `show_name` và `show_name_checked`; giải thích guard chặn input quá dài trước sink.
- [ ] Hoàn thành bài tập input dài 0, 15, 16 và 20 byte: tính số byte cần chép, xét guard và đường đi tới sink.
- [ ] Vẽ stack frame minh họa; giải thích `RIP`, `RSP`, `RBP`, `call`/`ret` và vì sao kích thước buffer chưa cho offset.
- [ ] Phân biệt được ghi vượt, crash, thay đổi saved return address, điều khiển đích và đạt mục tiêu challenge.
- [ ] Phân biệt được CWE/CVE, ret2libc, ret2plt và ROP; nêu điều kiện còn thiếu để từ lỗi bộ nhớ gọi được hàm thư viện.
- [ ] Vẽ hai sơ đồ ABI x86 cdecl và System V AMD64; đánh dấu con trỏ đối số, địa chỉ tiếp tục và alignment tại entry hàm.
- [ ] Phân biệt được PLT entry, địa chỉ GOT entry, giá trị trong GOT, libc offset và địa chỉ libc runtime.
- [ ] Giải thích được mỗi lớp guard/canary/NX/ASLR/PIE/RELRO tác động ở bước nào và giới hạn tương ứng.
- [ ] Trả lời các câu hỏi tự kiểm tra; review chéo bài làm và tập nói phần nền trong 5–6 phút.

## CVE và nguồn tham khảo

**Cấu trúc (chốt 2026-11-02):** ca chính **CVE-2018-5767 (Tenda AC15, 2018)**; bước đệm **CVE-1999-0032 (lpr, 1996)** trình bày ~1 slide. Cùng lỗi nền CWE-121 và kỹ thuật ret2libc.

### Ca chính — CVE-2018-5767

- [x] (2026-11-02) Có [ghi chú riêng](cve/CVE-2018-5767.md): hồ sơ NVD (RCE từ xa, CVSS 9.8, CWE-20), hàm `R7WebsSecurityHandler`, đường `strstr`+`sscanf`+Cookie, cơ chế NX + gadget đặt `r0`, ràng buộc byte null, kịch bản giảng 2 slide, bảng mức bằng chứng và giới hạn.
- [x] Đối chiếu NVD API, advisory Fidus (Full Disclosure), CIRCL và seebug; đã ghi rõ **chưa đọc được writeup gốc** (trang Fidus đã gỡ, offset bị redact) nên format `sscanf`/kích thước buffer/gadget cụ thể chưa xác minh.
- [ ] Nếu tìm lại được writeup gốc: bổ sung ảnh/dẫn mã trực tiếp và xác minh chi tiết ASLR/gadget.
- [ ] Chuẩn bị 2 slide 2018 (lỗi + vì sao vẫn RCE dù có NX), nối về demo và về ca 1997.

### Bước đệm — CVE-1999-0032

- [x] Có [ghi chú riêng](cve/CVE-1999-0032.md) đối chiếu hồ sơ CVE, advisory và công bố return-into-libc.
- [x] Ghi chú đã có sản phẩm, nguyên nhân, điều kiện, tác động, phạm vi bản vá FreeBSD và giới hạn khi liên hệ với ret2libc.
- [x] (2026-11-02) Phân tích mã `lpr.c` 4.3BSD theo ba chặng `-C` → `card('C', class)` → vòng `while` trong `card()`, ngưỡng ghi vượt suy từ mã; diff bản vá FreeBSD 2.1.5 → 2.1.6; kịch bản giảng 2 slide; rà soát tài liệu docx: [ghi chú CVE mục 4–11](cve/CVE-1999-0032.md#4-đi-qua-mã-nguồn-ba-chặng-chỉ-tay-vào-đâu).
- [ ] Chuẩn bị 1 slide bước đệm theo khung "Khi trình bày" trong ghi chú (giữ đủ 5 ý, nói sơ không cụt); câu chuyển nối sang CVE-2018-5767.
- [x] Rà lại nguồn và phạm vi phát biểu (NVD API, CVE API, FreeBSD-SA-96:18, AUSCERT qua CIAC H-08, Bugtraq 1997); bản vá cấp dòng mã đã đọc từ mã hai bản phát hành FreeBSD.
- [ ] Cập nhật tài liệu docx theo bảng rà soát ở [mục 11 ghi chú CVE](cve/CVE-1999-0032.md#11-rà-soát-tài-liệu-học-s05_tai_lieu_hoc_va_trinh_baydocx-bản-2026-11-01) và tập giảng lại phần CVE cho một thành viên khác.

## Phân tích và demo S05

- [ ] Chạy trong VM cô lập, với challenge được phép; ghi ngày, kiến trúc, công cụ và cách khởi chạy.
- [ ] Tải đúng binary `split` x86_64 từ nguồn chính; lưu nguồn, tên/phiên bản hoặc hash của binary.
- [ ] Xác minh kiến trúc và bảo vệ NX/canary/PIE/RELRO trên binary thực; ghi ASLR runtime riêng.
- [ ] Có input bình thường làm mốc so sánh và phân tích input → sink → ghi vượt → điều kiện chuyển luồng.
- [ ] Đo offset và tìm địa chỉ/gadget trên chính binary `split` đang dùng.
- [ ] Xác nhận chuỗi dữ liệu, import `system()` và đường gọi qua `system@plt` bằng disassembly/debugger.
- [ ] Quan sát tham số `RDI`, alignment và entry hàm thư viện; giải thích đúng vai trò của ABI.
- [ ] Phân biệt các mức: ghi vượt, crash, thay đổi địa chỉ trả về, gọi đúng hàm và đạt mục tiêu challenge.
- [ ] Demo đạt mục tiêu ít nhất hai lần liên tiếp trên cấu hình đã ghi; lưu lệnh và output thực tế.
- [ ] Có ảnh minh chứng S05 kèm chú thích ảnh chứng minh điều gì, lệnh nào và ngày nào.
- [ ] Có phương án dự phòng bằng video hoặc ảnh S05 và lời dẫn tương ứng.
- [ ] Nếu làm direct ret2libc: xác minh đúng libc build, offset, base/địa chỉ runtime và cấu hình ASLR; chỉ nhận định trong phạm vi đã đo.

## Nội dung trình bày và nộp

- [ ] Phần CWE xác định lỗi nền của ca demo/CVE và căn cứ phân loại; chỉ gán CWE-121 khi xác nhận tràn buffer trên stack, giải thích riêng ret2libc là kỹ thuật tái sử dụng mã.
- [ ] Đối chiếu `system@plt` và direct ret2libc; phát biểu đúng mức demo đã thực hiện.
- [ ] Làm rõ vì sao NX hạn chế mã trên stack và vì sao điều kiện sử dụng lại mã vẫn cần xem xét.
- [ ] Mỗi CVE có sản phẩm, nguyên nhân, điều kiện, tác động, khắc phục và nguồn theo ghi chú; không tái hiện khai thác (nhất là firmware Tenda thật).
- [ ] CVE-2018-5767 (ca chính): chỉ được hàm `R7WebsSecurityHandler`, đường `sscanf`/Cookie; giải thích vì sao NX bật vẫn RCE (gadget đặt `r0` + hàm libc); nối rõ với demo và với ràng buộc byte 0 của 1997.
- [ ] CVE-1999-0032 (bước đệm): nói đủ 5 ý, nêu đây là nơi return-into-libc ra đời; không sa đà chi tiết cấp dòng mã.
- [ ] Nói xuyên suốt: cùng CWE-121 + ret2libc, 1996 cục bộ → 2018 từ xa; demo x86_64 cùng cơ chế với CVE ARM, không đánh đồng kiến trúc.
- [ ] Có phân tích sửa lỗi tận gốc và vai trò/giới hạn của guard, canary, NX, ASLR, PIE, RELRO.
- [ ] Hoàn thành slide S05 dự kiến 14 trang; rà nguồn và kiểm tra hiển thị tiếng Việt. (Đã có nội dung chi tiết + lời giảng ở [slides/noi_dung_chi_tiet.md](slides/noi_dung_chi_tiet.md); chưa xuất file trình chiếu.)
- [ ] Mỗi kết luận chỉ rõ điều đã xác nhận, giả định và phần chưa xác minh.
- [ ] Review chéo bởi thành viên khác; diễn tập có hỏi đáp trong 20–30 phút (mục tiêu 26 phút).
- [ ] Cập nhật nhật ký dự án bằng file/bằng chứng thực tế và bước tiếp theo.
