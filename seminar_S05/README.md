# Mini seminar S05 — Return-to-libc

**Chủ đề:** phân tích kỹ thuật điều khiển luồng thực thi để sử dụng lại các hàm có sẵn trong thư viện hệ thống, thường khi stack không được thực thi; làm rõ liên hệ với tràn bộ đệm và các cơ chế bảo vệ.

- **Thời lượng:** 20–30 phút gồm hỏi đáp; dự kiến 14 slide, 26 phút.
- **Sản phẩm:** slide, demo CTF Pwnable lặp lại được và phân tích một CVE thực tế.
- **Trọng tâm:** S05 độc lập: return-to-libc, lỗi nền và các cơ chế bảo vệ. VulAgent là sản phẩm riêng.
- **Quy tắc:** [AGENT.md](../AGENT.md); yêu cầu và kế hoạch hiện hành ở [REQUIREMENTS.md](REQUIREMENTS.md), [PLAN.md](PLAN.md).

## Cách phân tích

**input → sink ghi vượt → dữ liệu điều khiển bị ảnh hưởng → điều kiện chuyển luồng → hàm/tham số theo ABI → kiểm tra bảo vệ → kết luận có bằng chứng.**

Return-to-libc là kỹ thuật tái sử dụng mã, không phải tên của lỗi ghi tràn. Lỗi tràn bộ đệm có thể tạo khả năng thay đổi địa chỉ trả về; khai thác còn phụ thuộc quyền kiểm soát input, địa chỉ đích, quy ước gọi hàm và các lớp bảo vệ.

## Tài liệu hiện hành

| Tài liệu | Nội dung |
|---|---|
| [PLAN.md](PLAN.md) | 10 mục của đề, kịch bản demo, 14 slide và các mốc thực hiện |
| [KNOWLEDGE.md](KNOWLEDGE.md) | Nền tảng stack/ABI, thư viện động, bảo vệ và câu hỏi tự kiểm tra |
| [CHECKLIST.md](CHECKLIST.md) | Điều kiện hoàn thành và bằng chứng cần thu mới cho S05 |
| [CVE-1999-0032](cve/CVE-1999-0032.md) | Ca CVE được chọn cho S05; ghi chú nguồn, quan hệ với ret2libc và khắc phục |

Các đầu ra `demo/`, `evidence/`, `slides/`, `notes/` của S05 sẽ được tạo khi thực hiện bước tương ứng trong kế hoạch. Chưa có kết quả chạy binary S05.

## Quyết định và trạng thái

| Hạng mục | Trạng thái |
|---|---|
| Chủ đề | **S05 — Return-to-libc**, chuẩn bị và thực hiện độc lập |
| Môi trường | Dự kiến Kali amd64 trên UTM **Emulate**. Cần kiểm tra kiến trúc, công cụ và binary thực tế cho S05 |
| Demo chính | **Dự kiến:** [ROP Emporium split x86_64](https://ropemporium.com/challenge/split.html). Trang challenge mô tả NX, hàm `system()` được import và chuỗi `/bin/cat flag.txt`; phải xác nhận trên binary thực tế |
| Cách gọi đúng demo | Tái sử dụng libc qua `system@plt` bằng ROP ngắn. Chỉ xác nhận đường gọi cụ thể sau disassembly/debugger; chưa chứng minh gọi trực tiếp địa chỉ libc, leak libc base hay vượt ASLR |
| Demo mở rộng | Direct ret2libc nếu đủ thời gian và đã xác minh đúng libc build/base tại runtime |
| CVE | **Chọn CVE-1999-0032** theo mức độ phù hợp S05; nguồn và giới hạn ở [ghi chú CVE](cve/CVE-1999-0032.md). Chỉ nghiên cứu và trình bày |
| Ngày seminar / thành viên | `[CHƯA CHỐT: ngày]`, `[CHƯA CHỐT: A=…, B=…, C=…]` |

## Hai đường gọi thư viện cần phân biệt

| Mức | Đích điều khiển luồng | Vai trò trong S05 |
|---|---|---|
| Gọi `system@plt` | Entry PLT của chương trình chuyển tới hàm thư viện, với tham số được chuẩn bị đúng ABI | Demo chính dự kiến: thấy rõ việc ghép hàm và dữ liệu dưới NX |
| Direct ret2libc | Địa chỉ hàm trong libc đang được nạp | Trọng tâm lý thuyết; phải biết đúng libc build, offset và base runtime trước khi khẳng định |

Việc demo `split` chạy thành công sẽ chỉ chứng minh chuỗi gọi đã quan sát trong cấu hình đó. Offset, địa chỉ và gadget phải được xác định trên binary thực tế.
