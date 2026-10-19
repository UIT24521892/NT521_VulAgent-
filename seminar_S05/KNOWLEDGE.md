# Kiến thức cần học cho S05

Học theo thứ tự dưới đây. Mục tiêu là giải thích được luồng điều khiển và điều kiện tái sử dụng hàm thư viện, rồi đối chiếu với bằng chứng của binary S05. Kế hoạch thực hành ở [PLAN.md](PLAN.md).

## 1. Nền tảng bắt buộc

| Chủ đề | Cần tự làm được | Dùng trong seminar |
|---|---|---|
| C, mảng, con trỏ và độ dài | Phân biệt dung lượng đích với số byte có thể ghi; theo dấu input đến sink và guard | Chỉ ra nguyên nhân ghi vượt trước khi bàn kỹ thuật khai thác |
| Stack, `call`, `ret` | Giải thích địa chỉ trở về trên stack, tác động của `ret` lên luồng thực thi và stack pointer | Sơ đồ luồng bình thường so với luồng bị thay đổi |
| Crash và quyền điều khiển | Phân biệt ghi vượt, crash, thay đổi địa chỉ trả về, gọi đúng hàm, đạt mục tiêu challenge | Kết luận đúng mức bằng chứng |
| CWE và kỹ thuật khai thác | Phân biệt CWE-121/CWE-787 là loại lỗi bộ nhớ với ret2libc/ROP là cách khai thác | Ánh xạ đúng lỗi nền với chủ đề S05 |
| Debugger và disassembly | Xác nhận kiến trúc, hàm nhận input, vị trí ghi, offset, đích chuyển luồng và tham số | Thu bằng chứng mới cho `split`; mọi offset/gadget đều đo trên binary này |

Stack frame chỉ là sơ đồ minh họa cho đến khi được đối chiếu với compiler, binary và trạng thái runtime đang dùng. Không suy ra khả năng điều khiển từ một lần SIGSEGV.

## 2. ABI: chuẩn bị lời gọi hàm

| Nội dung | x86 32-bit, `cdecl` | Linux System V AMD64 |
|---|---|---|
| Tham số integer/pointer | Truyền trên stack; caller thường dọn tham số | Sáu tham số đầu qua `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9`; tham số tiếp theo dùng stack |
| Giá trị trả về cơ bản | `EAX` | `RAX` |
| Điều cần kiểm tra | Thứ tự tham số, địa chỉ trở về và trạng thái stack sau lời gọi | Tham số đầu trong `RDI`, stack alignment và trạng thái sau lời gọi |

Với lời gọi thông thường của AMD64, stack căn theo biên 16 byte ngay trước `call`; tại entry hàm, `(RSP + 8)` chia hết cho 16. Chuyển bằng `ret` vẫn phải tạo trạng thái phù hợp với ABI của hàm đích. Dùng debugger kiểm tra thay vì mặc định mọi crash trong libc đều do alignment. Nguồn: [System V AMD64 psABI, Function Calling Sequence](https://gitlab.com/x86-psABIs/x86-64-ABI/-/blob/master/x86-64-ABI/low-level-sys-info.tex), [LSB IA-32 ELF/ABI](https://refspecs.linuxfoundation.org/LSB_5.0.0/LSB-Core-IA32/LSB-Core-IA32/elf-ia32.html).

`system()` là hàm thư viện C, khác lời gọi hệ thống bằng `syscall`. Demo dự kiến dùng đối số là chuỗi có sẵn để đọc flag của challenge; không cần đổi mục tiêu thành mở shell.

## 3. Từ hàm chương trình đến thư viện động

- **`system@plt`:** entry PLT nằm trong executable; cơ chế liên kết động dùng GOT và resolver để chuyển tới implementation trong thư viện. Đây là đường gọi thư viện cần quan sát ở demo chính.
- **Direct ret2libc:** chuyển tới địa chỉ trong libc đang nạp. Phải phân biệt offset trong một libc build với địa chỉ runtime sau khi thư viện được đặt vào không gian địa chỉ.

ROP kết hợp các đoạn mã có sẵn để chuẩn bị trạng thái và chuyển luồng. Trên AMD64, cần hiểu vì sao việc chuẩn bị thanh ghi tham số xuất hiện trong demo tái sử dụng hàm thư viện. Tài liệu nền về PLT/GOT và lazy binding: [ROP Emporium guide, Appendix A](https://ropemporium.com/guide.html#appendix-a).

Với `split`, nhiệm vụ dự kiến là xác nhận import `system()`, chuỗi dữ liệu, đích PLT và ABI trên binary thực. Gọi được `system@plt` không tự chứng minh đã biết libc base hay đã vượt ASLR. Mô tả challenge: [ROP Emporium split](https://ropemporium.com/challenge/split.html).

Thực hành mở rộng: [SEED Return-to-libc Attack Lab](https://seedsecuritylabs.org/Labs_20.04/Software/Return_to_Libc/) để học direct ret2libc; đây là lab theo môi trường SEED Ubuntu 20.04, không thay cho demo CTF và chưa xác minh tương thích Kali của nhóm. Có thể đối chiếu bài “Return to libc” trong [pwn.college — Return Oriented Programming](https://pwn.college/pwndamentals~cfe9c1cb/return-oriented-programming/), cần xác nhận tài khoản/quyền truy cập và môi trường nền tảng trước khi chọn.

## 4. Guard và các lớp bảo vệ

| Cơ chế | Tác dụng cần giải thích | Giới hạn cần nêu |
|---|---|---|
| Kiểm tra biên/độ dài | Ngăn phép ghi vượt dung lượng đích trên mọi đường tới sink | Phải xét cả kích thước thực, con trỏ và giá trị trả về của hàm đọc |
| NX/DEP | Ngăn thực thi ở trang dữ liệu không có quyền execute | Mã thư viện và mã chương trình vẫn có thể thực thi; NX không sửa lỗi ghi vượt |
| Stack canary | Phát hiện một số dạng ghi đè stack trước khi hàm trả về | Phụ thuộc hàm có được bảo vệ và dữ liệu nào bị ghi đè |
| ASLR | Ngẫu nhiên hóa vị trí các vùng được hỗ trợ, gồm thư viện | Trạng thái runtime và cách khởi chạy phải được ghi nhận; không suy ra từ riêng kết quả `checksec` |
| PIE | Cho phép executable được bố trí ở base thay đổi khi ASLR áp dụng | Cần phân biệt base executable với base libc |
| RELRO | Hạn chế sửa các vùng relocation/GOT tùy mức bảo vệ | Không đồng nghĩa mọi lời gọi qua PLT hoặc mọi ROP đều bị chặn |
| Sửa mã và kiểm thử | Giới hạn ghi đúng dung lượng, xử lý lỗi, dùng ASan khi kiểm thử | Đây là biện pháp xử lý lỗi nền; không thay bằng chỉ bật bảo vệ |

CET/shadow stack và CFI là phần mở rộng khi còn thời gian: tập trung mục tiêu bảo vệ luồng điều khiển, không khẳng định binary/VM đang hỗ trợ khi chưa kiểm tra.

## 5. CVE và tự kiểm tra

Đọc [ghi chú CVE-1999-0032](cve/CVE-1999-0032.md), phân biệt lỗi được hồ sơ CVE mô tả với kỹ thuật trong công bố nghiên cứu. Khi dùng ca lịch sử phải nêu đúng điều kiện nền tảng và phạm vi bảo vệ; không tái hiện CVE.

- [ ] Giải thích được vì sao NX không ngăn mọi cách sử dụng lại mã.
- [ ] Vẽ được hai đường gọi `system@plt` và direct ret2libc, nêu điều kiện địa chỉ và ABI của từng đường.
- [ ] Phân biệt được PLT entry, GOT entry, libc offset và địa chỉ libc runtime.
- [ ] Chỉ được tham số và alignment tại entry hàm thư viện bằng debugger.
- [ ] Nêu được bảo vệ thực tế của binary S05 và bằng chứng tương ứng.
- [ ] Phân biệt được lỗi tràn stack trong CVE với kỹ thuật khai thác đang nghiên cứu.
