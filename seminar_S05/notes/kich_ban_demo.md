# Kịch bản demo S05 — `split` x86_64, kể theo "vì sao"

Mục đích: demo không chỉ ra flag mà làm người xem hiểu **vì sao mỗi bước**, **vì sao tại chỗ đó có thứ đó**, **nhìn vào đâu để biết là thật**. Khớp bảng bằng chứng ở [../PLAN.md](../PLAN.md) mục 5 và bố cục slide mục 6.

Quy ước: `[ĐO: …]` = số/địa chỉ phải lấy trên binary đang dùng, chưa được điền ở đây (không bịa). Mọi nhận định đánh dấu mức bằng chứng: ghi vượt / crash / chiếm luồng / gọi hàm libc đúng đối số / đạt mục tiêu CTF.

Môi trường: Kali amd64 trên UTM (Emulate). Xác nhận `uname -m = x86_64` trước khi chạy. Công cụ: `gdb`+`pwndbg|gef`, `pwntools`, `checksec`, `ROPgadget|ropper`.

---

## Trước demo — xác nhận một lần (không chiếu, để chốt số liệu)

- [ ] `uname -m` → `[ĐO]`; `file split` → `[ĐO]`; `sha256sum split` → `[ĐO]`
- [ ] `checksec --file=split` → NX `[ĐO: bật?]`, PIE `[ĐO]`, Canary `[ĐO]`, RELRO `[ĐO]`
- [ ] Trạng thái ASLR tiến trình ngoài GDB: `cat /proc/sys/kernel/randomize_va_space` → `[ĐO]`
- [ ] `system@plt` = `[ĐO]`; chuỗi lệnh (`/bin/cat flag.txt`) tại `[ĐO]`; gadget `pop rdi; ret` tại `[ĐO]`
- [ ] Offset tới saved RIP = `[ĐO]` (xác nhận bằng cyclic)

---

## Bước 1 — Môi trường & bảo vệ  → evidence/01_moi_truong_va_bao_ve.png
- **Thao tác:** `file split`, `checksec`, đọc ASLR tiến trình.
- **Vì sao làm:** trước khi khai thác phải biết *luật chơi*. Chính các bảo vệ quyết định được phép làm gì. Đây cũng là bước trả lời câu hỏi lớn nhất của buổi.
- **Người xem thấy / học:** NX **bật** nghĩa là stack không thực thi → **không thể** chèn shellcode chạy trên stack. Từ đó mới sinh ra ý tưởng ret2libc: *đừng mang mã mới, hãy dùng lại mã đã có quyền thực thi* (hàm trong chương trình/thư viện).
- **Bằng chứng:** ảnh checksec. Mức: mô tả cấu hình, chưa phải khai thác.

## Bước 2 — Chạy bình thường  → evidence/02_chay_binh_thuong.png
- **Thao tác:** chạy `./split`, nhập input ngắn hợp lệ.
- **Vì sao làm:** cho người xem thấy hành vi "đúng" để lát nữa đối chiếu hành vi "bị bẻ". Không có mốc này thì crash về sau vô nghĩa.
- **Người xem thấy / học:** chương trình đọc input vào một buffer rồi kết thúc bình thường — chưa có gì bất thường.
- **Bằng chứng:** ảnh chạy thường.

## Bước 3 — Sink & stack: lỗi nằm ở đâu  → evidence/03_sink_va_stack.png
- **Thao tác:** disassemble hàm đọc input; chỉ ra lệnh đọc (sink) và dung lượng buffer; không có guard độ dài.
- **Vì sao làm:** tách bạch **lỗi nền** (ghi vượt buffer, CWE-121) với **kỹ thuật khai thác** (ret2libc). Người xem phải thấy lỗi *trước*, kỹ thuật *sau*.
- **Người xem thấy / học:** input dài hơn buffer sẽ tràn sang các ô phía trên, trong đó có **saved return address** — ô quyết định "chạy tiếp ở đâu khi hàm return".
- **Vì sao tại chỗ đó có thứ đó:** giải thích layout stack frame: `[buffer][saved RBP][saved RIP]`. `ret` lấy giá trị tại saved RIP để nạp vào RIP → ai ghi được ô đó, người đó chọn luồng.
- **Bằng chứng:** ảnh disassembly + sơ đồ stack (nhãn **minh họa**).

## Bước 4 — Đo offset & chiếm luồng  → evidence/04_dieu_khien_luong_va_abi.png
- **Thao tác:** gửi cyclic pattern; đọc giá trị trong RIP/RSP lúc crash; suy ra offset `[ĐO]`; gửi lại payload đặt địa chỉ "mốc" (vd 0x4141…) để xác nhận điều khiển đúng 8 byte.
- **Vì sao làm:** phải ghi đè **đúng** ô saved RIP. Đo để biết cần bao nhiêu byte đệm — không đoán.
- **Người xem thấy / học:** RIP = giá trị do ta đặt → đây là mốc **"chiếm được luồng"** (khác với chỉ "crash"). Nói rõ sự khác biệt này.
- **Vì sao chuyển sang ABI ngay đây:** giờ ta điều khiển được RIP, nhưng muốn gọi `system("…")` còn phải đặt *đối số*. x86_64 System V: đối số 1 ở **RDI**, không phải trên stack như x86 cdecl → không thể nhét chuỗi ngay sau địa chỉ hàm.
- **Bằng chứng:** ảnh RIP mang giá trị ta đặt. Mức: chiếm luồng (chưa gọi hàm đúng đối số).

## Bước 5 — Gadget, PLT & gọi system đúng đối số  → evidence/05_goi_ham_libc.png
- **Thao tác:** tìm gadget `pop rdi; ret` `[ĐO]`; ghép payload `[đệm][pop rdi;ret][addr chuỗi][system@plt]`; đặt breakpoint tại `system@plt`, single-step tới đó.
- **Vì sao mỗi phần tử payload có mặt:**
  - `pop rdi; ret`: lấy 8 byte kế tiếp trên stack **bơm vào RDI** → giải quyết yêu cầu ABI ở bước 4.
  - `addr chuỗi /bin/cat flag.txt`: `system` cần **con trỏ tới chuỗi lệnh**; chuỗi này đã nằm sẵn trong binary nên chỉ việc trỏ tới — minh hoạ "tái sử dụng dữ liệu có sẵn", song hành với "tái sử dụng mã có sẵn".
  - `system@plt`: ta nhảy vào **entry PLT của chương trình**, nơi chuyển tiếp tới hàm thư viện.
- **Người xem thấy / học:** tại breakpoint, kiểm tra `RDI` đang trỏ tới chuỗi lệnh đúng (`x/s $rdi`), và luồng đang ở trong mã thực thi của `system`. Mức: **gọi được hàm thư viện với đối số đúng.**
- **Vì sao đôi khi thêm một `ret`:** nếu RSP lệch 16-byte, lệnh `movaps` trong prologue `system` sẽ fault. Thêm một gadget `ret` để căn lề. Đây là bài học "tại sao cùng payload mà máy này chạy máy kia lỗi".
- **Ranh giới trung thực (quan trọng):** tới đây **chưa** chứng minh ta tính được địa chỉ hàm trong libc hay vượt ASLR của libc — ta mới dùng `system@plt` do chương trình đã import. Phân biệt ret2plt vs direct ret2libc.
- **Bằng chứng:** ảnh RDI + điểm dừng trong system.

## Bước 6 — Đạt mục tiêu challenge, lặp 2 lần  → evidence/06_ket_qua_challenge.png
- **Thao tác:** chạy `exploit.py` **ngoài** GDB, lấy nội dung `flag.txt`; chạy lại lần 2.
- **Vì sao làm:** mục tiêu CTF là mức bằng chứng cao nhất; lặp 2 lần để chứng tỏ ổn định, không phải may rủi.
- **Người xem thấy / học:** flag thật, hai lần. Mức: **đạt mục tiêu CTF.**
- **Bằng chứng:** ảnh + log 2 lần chạy (lưu exit status/lỗi nếu có).

## Bước 7 — Vì sao nó sửa được & bảo vệ chặn ở đâu
- **Thao tác:** nêu bản sửa lỗi gốc (kiểm tra độ dài khi đọc input); bảng NX/canary/ASLR/PIE/RELRO chặn ở bước nào.
- **Vì sao làm:** đóng vòng "lỗi → khai thác → phòng thủ". Mỗi lớp bảo vệ ứng với *một bước cụ thể* ở trên (vd canary chặn bước 4; PIE/ASLR làm địa chỉ bước 5 không cố định; NX đã buộc ta chọn ret2libc ở bước 1).
- **Người xem học:** vì sao ưu tiên **sửa lỗi gốc**; vì sao NX một mình không đủ.
- **Bằng chứng:** mã lỗi/sửa + bảng.

---

## Dự phòng
Nếu VM emulation quá chậm khi demo trực tiếp: dùng bộ ảnh/log đã lưu ở `evidence/` và kể theo đúng 7 bước trên (video nếu có). Trạng thái đã xác minh/chưa xác minh ghi ở bảng mục 9 PLAN.
