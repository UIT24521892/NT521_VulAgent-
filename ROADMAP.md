# ROADMAP — kế hoạch tổng và trạng thái

Cập nhật lần cuối: 2026-10-19. Hạn nộp: `[CHƯA CHỐT: ngày seminar]`, `[CHƯA CHỐT: ngày nộp đề tài]`.

## Trạng thái hiện tại

- **Trọng tâm:** Mini seminar **S05 — Return-to-libc (ret2libc)** → [seminar_S05/](seminar_S05/). Đổi theo mô tả chủ đề của người dùng ngày 2026-10-19: tái sử dụng hàm thư viện khi stack bị hạn chế thực thi, liên hệ buffer overflow và bảo vệ.
- **Phạm vi:** S05 độc lập; kiến thức, challenge, CVE và bằng chứng được chọn cho chủ đề ret2libc.
- **Tạm hoãn:** VulAgent → [vulagent/](vulagent/) (đã có tài liệu tham chiếu, chưa có mã)
- **Việc tiếp theo:** kiểm tra challenge `split` x86_64 trên Kali/UTM và thu bằng chứng gọi hàm thư viện; xem [seminar_S05/PLAN.md](seminar_S05/PLAN.md#0-việc-cần-làm-ngay). Phiên này mới đổi kế hoạch, chưa chạy demo S05.

## Hai nhánh song song nhưng tách biệt

| Nhánh | Kế hoạch | Checklist | Khi nào làm |
|---|---|---|---|
| Seminar S05 | [PLAN](seminar_S05/PLAN.md) (3 mốc; gộp nếu hạn gần) | [CHECKLIST](seminar_S05/CHECKLIST.md) | Ngay bây giờ |
| VulAgent | [PLAN](vulagent/PLAN.md) (tuần 2–7) | [CHECKLIST](vulagent/CHECKLIST.md) | Sau khi seminar S05 xong hoặc khi nhóm đổi ưu tiên |

## Lịch dự kiến (đã đổi nhánh seminar sang S05)

Mốc "Tuần" đếm từ ngày bắt đầu `[CHƯA CHỐT]`. Nếu hạn gần có thể gộp tuần 1–2 hoặc 4–5; giữ nguyên thứ tự các mốc kiểm chứng.

| Tuần | Seminar S05 | VulAgent |
|---|---|---|
| 1 | Ôn stack; học ABI, NX, libc/PLT/GOT; kiểm tra `split` x86_64 trên VM đã có | — (chỉ đọc tài liệu nếu còn thời gian) |
| 2 | Đo offset mới, chứng minh gọi hàm thư viện; phân tích CVE; thu ảnh/log S05, slide nháp | Đọc hình kiến trúc + một ví dụ trong paper; audit repo |
| 3 | Tập thuyết trình, **seminar** | Dựng repo, schema, pipeline chạy một cặp vuln/fixed |
| 4 | — | Chốt dữ liệu, IDs, baseline, công thức metric; kiểm tra rò rỉ nhãn |
| 5 | — | Thí nghiệm chính theo cấu hình đã khóa |
| 6 | — | Ablation, phân tích FP/FN, rà soát bản paper trích |
| 7 | — | Báo cáo, slide, demo dự phòng, diễn tập hỏi đáp |

Chi tiết đầu ra từng tuần nằm trong PLAN của mỗi nhánh.

## Nhật ký

| Ngày | Việc đã xong | Bằng chứng | Vướng mắc | Bước tiếp |
|---|---|---|---|---|
| 2026-10-05 | Tách 2 phần, tạo AGENT.md, kế hoạch S01 và VulAgent, sắp xếp thư mục | các file `PLAN.md` | Chưa có hạn nộp, tên thành viên, kiến trúc VM | Chốt challenge/CVE, kiểm tra `uname -m` trên VM |
| 2026-10-08 | Chốt môi trường demo S01: dựng VM Kali amd64 (x86_64) qua UTM Emulate thay vì qemu-user | [seminar_S01/README.md](seminar_S01/README.md) bảng quyết định | Chưa cài xong VM; chưa có hạn nộp, tên thành viên | Cài Kali amd64, xác minh `uname -m`=x86_64, tải ret2win x86_64, lưu ảnh 01 |
| 2026-10-11 | Kiểm chứng CVE-2015-7547 qua NVD API (CWE-119, CVSS v2 6.8/v3 8.1, phiên bản 2.9–2.22 vá từ 2.23); tạo bài tập 3 đoạn mã C + phân tích source–sink–guard; tạo khung ghi chú GDB x86_64 | [cve/CVE-2015-7547.md](seminar_S01/cve/CVE-2015-7547.md), [notes/bai_tap_3_doan_ma/](seminar_S01/notes/bai_tap_3_doan_ma/), [notes/02_gdb_va_phan_tich_binary.md](seminar_S01/notes/02_gdb_va_phan_tich_binary.md) | Google blog render JS chưa đọc được thân bài; VM đang cài | Cài xong VM → tải ret2win, đo offset; mỗi thành viên tự điền bảng bài tập rồi review chéo |
| 2026-10-12 | Cài Kali amd64; phân tích ret2win (buffer 32, read 56, offset 40, ret2win=0x400756); **khai thác THÀNH CÔNG** — exploit 2 bước (control → ret gadget 0x400770 căn lề → flag `ROPE{a_placeholder_32byte_flag!}`, exit 0); dựng slide 14 trang điền số liệu thật; soạn evidence/README | [demo/exploit.py](seminar_S01/demo/exploit.py), [slides/S01_slides.md](seminar_S01/slides/S01_slides.md), [evidence/README.md](seminar_S01/evidence/README.md) | VM chậm; còn ~24h | Lưu ảnh PNG 01–05 vào evidence/; chụp ảnh 02 (chạy bình thường); làm slide 06 (mã sửa+bảng bảo vệ); chạy demo lần 2 xác nhận; tập bấm giờ |
| 2026-10-12 | Lưu đủ 5 ảnh PNG (01–05) vào evidence/; **xuất PowerPoint `S01_seminar.pptx` 14 slide** (nhúng 5 ảnh, sơ đồ stack, cây CWE, bảng CVE/bảo vệ/giới hạn); validate PASSED | [slides/S01_seminar.pptx](seminar_S01/slides/S01_seminar.pptx), [slides/build_deck.js](seminar_S01/slides/build_deck.js), [evidence/](seminar_S01/evidence/) | Chưa render QA hình (máy thiếu LibreOffice); slide đang KHÔNG dấu tiếng Việt | Mở .pptx trong PowerPoint kiểm tra; (tùy chọn) thêm dấu tiếng Việt; chạy demo lần 2; tập bấm giờ; tra lại URL |
| 2026-10-19 | Đổi seminar sang S05 ret2libc; tạo bộ kế hoạch/yêu cầu/kiến thức/checklist mới; cập nhật trọng tâm, giữ nguyên S01; đối chiếu nguồn chính của challenge/CVE | [seminar_S05/PLAN.md](seminar_S05/PLAN.md), [seminar_S05/REQUIREMENTS.md](seminar_S05/REQUIREMENTS.md), [seminar_S05/CHECKLIST.md](seminar_S05/CHECKLIST.md) | Chưa chốt ngày/thành viên; chưa tải/chạy `split`, chưa có slide/ảnh S05; gọi qua PLT không chứng minh đã tìm libc base | Kiểm tra binary S05 trong Kali amd64/UTM; đo offset, kiểm tra bảo vệ và ABI; ghi bằng chứng mới |
| 2026-10-19 | Chốt phạm vi S05 độc lập theo yêu cầu; bỏ liên kết và nội dung kế thừa khỏi bộ tài liệu hiện hành; chọn CVE-1999-0032, đối chiếu NVD, FreeBSD-SA-96:18 và công bố return-into-libc của Solar Designer | [PLAN](seminar_S05/PLAN.md), [ghi chú CVE](seminar_S05/cve/CVE-1999-0032.md), [CHECKLIST](seminar_S05/CHECKLIST.md) | Chưa chạy challenge hoặc CVE; chưa có slide/ảnh S05; chưa đọc diff bản vá lịch sử | Kiểm tra môi trường demo S05; chuẩn bị hai slide CVE với nguồn và giới hạn đã ghi |
| 2026-10-19 | Khởi tạo Git nhánh `main`, cấu hình `origin` theo repo người dùng cung cấp; thêm `.gitignore` cho dependency, cache và cấu hình bí mật cục bộ; rà nội dung trước commit, chưa phát hiện key/token thật | [.gitignore](.gitignore); repo đích [UIT24521892/NT521_VulAgent-](https://github.com/UIT24521892/NT521_VulAgent-) | Repo đích trống, đã xác nhận quyền push; chưa thay đổi trạng thái hoàn thành của S05 | Tạo commit đầu tiên, push lên `origin/main` và đối chiếu commit trên GitHub |
| 2026-10-19 | Thêm README gốc, làm rõ VulAgent là đồ án chính và S05 là mini seminar; liên kết tới tài liệu từng phần. Commit khởi tạo `e0f24d1` đã push thành công và khớp `origin/main` | [README.md](README.md); lịch sử Git nhánh `main` | Không có vướng mắc về tài liệu tổng quan | Tiếp tục kế hoạch mini seminar S05 |
