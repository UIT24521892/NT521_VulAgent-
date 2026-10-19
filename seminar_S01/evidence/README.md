# Ảnh minh chứng demo ret2win

Môi trường (ghi chung cho mọi ảnh): **Kali Linux amd64 trên UTM (chế độ Emulate) / Mac Apple Silicon**. `uname -m` = `x86_64`. Ngày chạy: **2026-10-12**. Binary: `ret2win` (ROP Emporium, x86-64, not stripped, BuildID `19abc0b3bb228157af55b8e16af7316d54ab0597`).

> Việc còn phải làm: **lưu các ảnh PNG thật** vào thư mục này đúng tên bên dưới (chụp màn hình trong VM). Mỗi dòng dưới đây là chú thích sẽ đi kèm ảnh.

| Ảnh | Chứng minh điều gì | Lệnh / thao tác |
|---|---|---|
| `01_kiem_tra_binary.png` | Đúng binary, đúng kiến trúc, và các lớp bảo vệ đang bật/tắt | `uname -m` · `file ./ret2win` · `checksec --file=./ret2win` → **No canary · NX enabled · No PIE**, not stripped |
| `02_chay_binh_thuong.png` | Chương trình chạy bình thường với input ngắn (mốc so sánh) — **CHƯA CHỤP** | `echo "hello" \| ./ret2win` → in banner, thoát bình thường, không crash |
| `03_sink_va_buffer.png` | Vị trí sink và kích thước buffer trong binary | gdb: `disassemble pwnme` → `read(0, buf, 0x38=56)` vào `buf` tại `rbp-0x20` (**32 byte**); `info functions` → `ret2win` = `0x400756` |
| `04_debugger_truoc_sau.png` | **Đã điều khiển địa chỉ trả về** (không chỉ crash) | `python3 exploit.py` **lần đầu** (payload `A*40 + p64(0x400756)`, chưa căn lề): in **"Well done! Here's your flag:"** rồi **SIGSEGV** trong `system()` → đã nhảy vào `ret2win()` |
| `05_ket_qua_challenge.png` | **Đạt mục tiêu challenge** (in flag) | `python3 exploit.py` **lần hai** (thêm ret gadget `0x400770` căn lề): exit code **0**, in **`ROPE{a_placeholder_32byte_flag!}`** |
| `06_ma_loi_vs_ma_sua.png` | Cách sửa tận gốc + bảng bảo vệ theo binary | Mã lỗi vs mã sửa (xem [../notes/bai_tap_3_doan_ma/](../notes/bai_tap_3_doan_ma/)); bảng canary/NX/ASLR/PIE với trạng thái thật của ret2win |

## Bốn mức bằng chứng (phát biểu đúng mức)

1. **Có ghi vượt** — đọc 56 byte vào buffer 32 byte (thấy trong disassembly, ảnh 03).
2. **Crash** — SIGSEGV (ảnh 04).
3. **Đã điều khiển địa chỉ trả về** — chương trình chạy code của `ret2win()`, in "Well done" (ảnh 04). Mạnh hơn (2).
4. **Đạt mục tiêu challenge** — in flag, exit 0 (ảnh 05).

Ảnh 04 chứng minh tới mức (3); chỉ ảnh 05 mới chứng minh mức (4). Không gộp hai mức.

## Phân tích offset (đo trên binary này)

```
buffer:     32 byte  (buf tại rbp-0x20)
saved rbp:   8 byte
----------------------------
offset tới địa chỉ trả về = 40 byte
```
Suy ra từ disassembly `pwnme` (đo trên chính binary demo), không lấy từ sơ đồ minh họa.
