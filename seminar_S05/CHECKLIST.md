# Checklist mini seminar S05

Chỉ đánh dấu khi có đầu ra S05 tương ứng. Tài liệu, challenge, CVE và bằng chứng được chuẩn bị độc lập cho return-to-libc. Kế hoạch chi tiết: [PLAN.md](PLAN.md).

## Tài liệu và phạm vi

- [x] Có [REQUIREMENTS.md](REQUIREMENTS.md) ghi mô tả S05 và giữ đủ 10 mục yêu cầu chung; [PLAN.md](PLAN.md) cập nhật nội dung, demo, thời lượng và tiến độ.
- [x] Có [README.md](README.md) cho S05, ghi chủ đề, trạng thái quyết định và giới hạn demo dự kiến.
- [x] Có [KNOWLEDGE.md](KNOWLEDGE.md) về stack/ABI, PLT/GOT/libc và cơ chế bảo vệ.
- [x] Có checklist riêng cho S05; chưa đánh dấu kết quả demo, ảnh hay slide chưa làm.
- [x] Chọn CVE-1999-0032 theo mức độ phù hợp với S05; có ghi chú đối chiếu nguồn và giới hạn.
- [ ] 10 mục của đề có vị trí trong slide hoặc phần nói.
- [ ] Ngày seminar, thành viên và phân công đã chốt.
- [ ] Chốt challenge sau khi kiểm tra khả năng chạy và phạm vi demo.

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

- [ ] Giải thích ret2libc là kỹ thuật sử dụng lại mã; CWE-121/CWE-787 mô tả lỗi nền, không phải tên kỹ thuật.
- [ ] Đối chiếu `system@plt` và direct ret2libc; phát biểu đúng mức demo đã thực hiện.
- [ ] Làm rõ vì sao NX hạn chế mã trên stack và vì sao điều kiện sử dụng lại mã vẫn cần xem xét.
- [ ] CVE có sản phẩm, nguyên nhân, điều kiện, tác động, bản vá và nguồn; không tái hiện khai thác.
- [ ] CVE-1999-0032: trình bày rõ cách đối chiếu hồ sơ CVE với công bố return-into-libc, điều kiện lịch sử và bản vá theo nhà cung cấp.
- [ ] Có phân tích sửa lỗi tận gốc và vai trò/giới hạn của guard, canary, NX, ASLR, PIE, RELRO.
- [ ] Hoàn thành slide S05 dự kiến 14 trang; rà nguồn và kiểm tra hiển thị tiếng Việt.
- [ ] Mỗi kết luận chỉ rõ điều đã xác nhận, giả định và phần chưa xác minh.
- [ ] Review chéo bởi thành viên khác; diễn tập có hỏi đáp trong 20–30 phút (mục tiêu 26 phút).
- [ ] Cập nhật nhật ký dự án bằng file/bằng chứng thực tế và bước tiếp theo.
