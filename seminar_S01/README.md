# Mini seminar S01 — Stack-based buffer overflow

- **Thời lượng:** 20–30 phút gồm hỏi đáp (dự kiến 26 phút)
- **Sản phẩm:** slide 12–14 trang + demo CTF Pwnable + một CVE thực tế
- **Phạm vi:** chỉ S01. Đề tài VulAgent ở [../vulagent/](../vulagent/), không trộn vào đây.
- **Quy tắc chung:** [../AGENT.md](../AGENT.md)

## Cách phân tích xuyên suốt

**input (source) → đường dữ liệu/thực thi → thao tác nhạy cảm (sink) → điều kiện lỗi xảy ra → kiểm tra guard/ngữ cảnh → kết luận có bằng chứng.**

CVE chỉ cần nghiên cứu và trình bày, không tái hiện khai thác.

## Nội dung thư mục

| Đường dẫn | Dùng để |
|---|---|
| [PLAN.md](PLAN.md) | Kế hoạch: 10 mục của đề, kịch bản demo, bố cục slide, lịch 3 tuần |
| [KNOWLEDGE.md](KNOWLEDGE.md) | Kiến thức cần học theo thứ tự ưu tiên + bài tập đầu tiên |
| [CHECKLIST.md](CHECKLIST.md) | Checklist nộp và tự kiểm tra |
| `slides/` | Slide và nguồn |
| `demo/` | Binary challenge, lệnh/script demo, kịch bản dự phòng |
| `cve/` | Ghi chú CVE, advisory, bản vá |
| `evidence/` | Ảnh minh chứng 1–6 và chú thích |
| `notes/` | Phân tích thủ công, bài tập 3 đoạn mã, nháp |

## Quyết định đã chốt / chưa chốt

| Hạng mục | Gợi ý trong tài liệu gốc | Trạng thái |
|---|---|---|
| Challenge | [ROP Emporium ret2win](https://ropemporium.com/challenge/ret2win.html) | `[CHƯA CHỐT]` — cần khớp kiến trúc VM |
| CVE | [CVE-2015-7547 (glibc getaddrinfo)](https://access.redhat.com/articles/2161461) | `[CHƯA CHỐT]` |
| Môi trường | Kali chạy qua UTM trên Mac Apple Silicon | **Chốt 2026-10-08:** dựng VM **Kali amd64 (x86_64)** qua UTM ở chế độ **Emulate** để demo ret2win bản x86_64. Lý do: debug GDB thuận tay, quan sát bảo vệ gần máy thật hơn so với qemu-user; chấp nhận chạy chậm do full-system emulation trên Apple Silicon. (Kali aarch64 cũ không khớp binary; ROP Emporium không có bản aarch64 — tra [ret2win](https://ropemporium.com/challenge/ret2win.html), [guide](https://ropemporium.com/guide.html) ngày 2026-10-05.) **Đã xác minh 2026-10-12:** VM cài xong, `uname -m` = `x86_64`. (Chạy chậm do emulation — chấp nhận được.) |
| Ngày seminar | — | `[CHƯA CHỐT]` |
| Người phụ trách chính | Vai trò A | `[CHƯA CHỐT: tên]` |
