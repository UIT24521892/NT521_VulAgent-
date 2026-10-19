# Slide mini seminar S01 — Stack-based Buffer Overflow

Bản nháp nội dung từng slide (Markdown-first). Mỗi `---` là một slide. Chỗ `[ẢNH 0x]` và `[OFFSET=…]` điền sau khi có kết quả demo. Thời lượng mục tiêu: **26 phút** gồm hỏi đáp (xem [PLAN.md mục 6](../PLAN.md)).

Quy ước: **Nội dung slide** (gạch đầu dòng ngắn để chiếu) + *Ghi chú nói* (người trình bày nói, không chiếu).

Nguồn kiến thức: [notes/01](../notes/01_hoc_nen_tang_va_cwe.md), [notes/02](../notes/02_gdb_va_phan_tich_binary.md), [cve/CVE-2015-7547.md](../cve/CVE-2015-7547.md). Mọi URL phải tra lại trước khi chiếu (xem CHECKLIST).

---

## Slide 1 — Tiêu đề

- **Stack-based Buffer Overflow (CWE-121)**
- Mini seminar S01 — NT521 Lập trình khai thác lỗ hổng
- Nhóm 3 — `[CHƯA CHỐT: tên A, B, C]`
- Ngày `[CHƯA CHỐT]`

*Ghi chú nói:* giới thiệu nhóm, 1 câu về mục tiêu: phân tích một lỗi tràn bộ đệm trên stack theo mạch source→sink→guard, demo trên CTF ret2win và một CVE thật (glibc).

---

## Slide 2 — (Mục 1) Lỗ hổng là gì & bối cảnh

- Buffer = vùng nhớ cố định; trên stack là **biến cục bộ** (vd `char buf[64]`)
- Overflow = ghi **nhiều hơn** sức chứa → đè dữ liệu kế bên
- Dữ liệu vào từ: người dùng, **tệp**, **mạng**
- Hay gặp: C/C++, **dịch vụ mạng**, thư viện hệ thống, firmware
- Tác động: từ crash tới **chiếm quyền điều khiển luồng thực thi**

*Ghi chú nói:* nêu ví dụ nhập chuỗi quá dài; nhấn mạnh lỗi nằm ở ngôn ngữ không kiểm tra biên tự động.

---

## Slide 3 — (Mục 2) Nguyên lý, điều kiện, dạng phổ biến

- **Sơ đồ stack minh họa** (địa chỉ cao ở trên): return address ← rbp đã lưu ← buf
- Ghi từ `buf` đi lên → chạm rbp đã lưu → **địa chỉ trả về**
- Điều kiện: (a) input tới được sink; (b) ghi **không giới hạn** theo kích thước đích; (c) buffer trên stack
- Dạng phổ biến: `strcpy`/`gets`/`scanf("%s")`, `read(fd,buf,n)` với n lớn, **off-by-one**, tính sai độ dài

> Sơ đồ chỉ minh họa — **offset thật phải đo trên binary** (xem slide demo).

*Ghi chú nói:* phân biệt "crash" ≠ "điều khiển luồng". Dùng sơ đồ trong [notes/01 mục 1](../notes/01_hoc_nen_tang_va_cwe.md).

---

## Slide 4 — (Mục 3) CWE-121 và họ hàng

- **CWE-121 Stack-based Buffer Overflow** — buffer bị ghi tràn nằm **trên stack**
- Cây: CWE-119 (rộng) → **CWE-787** Out-of-bounds Write → **CWE-121**
- **CWE ≠ CVE**: CWE là *loại* yếu điểm; CVE là *một lỗ hổng cụ thể* trong sản phẩm cụ thể
- Chủ đề S01 = đúng CWE-121

*Ghi chú nói:* trích định nghĩa MITRE nguyên văn (slide ghi ngắn, nói đầy đủ). Mở trang MITRE đọc mục Relationships trước khi chốt sơ đồ.

---

## Slide 5 — (Mục 4) Vị trí & nguyên nhân — ret2win

- Binary demo: **ret2win (ROP Emporium, x86-64, không strip)**
- `checksec`: **No canary · NX enabled · No PIE**
- Hàm **`pwnme`** (`0x4006e8`): **`read(0, buf, 0x38=56)`** vào **buffer 32 byte** (`buf` tại `rbp-0x20`)
- Nguyên nhân: đọc **56 byte** vào chỗ chứa **32 byte** → ghi vượt **24 byte**
- Hàm đích **`ret2win`** tại **`0x400756`** (gọi `system("/bin/cat flag.txt")`)
- [ẢNH 03] disassembly `pwnme` — khoanh `read` + `lea -0x20(%rbp)` (buffer) + `mov $0x38,%edx` (số byte đọc)

*Ghi chú nói:* đọc 56 vào 32 — chính dòng chữ binary tự in: "fit 56 bytes into 32 bytes of stack buffer".

---

## Slide 6 — (Mục 5) Chuỗi khai thác (4–5 bước)

1. Gửi input dài hơn buffer (56 byte)
2. Ghi tràn qua **32 byte buffer + 8 byte rbp đã lưu** → tới **địa chỉ trả về**
3. **offset = 40 byte** (đo từ disassembly: 32 + 8), rồi ghi đè bằng địa chỉ `ret2win` = **`0x400756`**
4. Hàm kết thúc → `ret` nhảy tới `ret2win()`
5. `ret2win()` gọi `system("/bin/cat flag.txt")` → in flag → **đạt mục tiêu**

- Payload: `b'A'*40 + p64(0x400770) + p64(0x400756)` — chèn **ret gadget `0x400770`** để căn lề stack 16 byte
- Vì **No PIE** nên địa chỉ `ret2win` cố định; **NX** không cản vì nhảy tới hàm có sẵn

*Ghi chú nói:* đây là "ret-to-function", không shellcode. Ret gadget giải thích ở slide 9.

---

## Slide 7 — (Mục 7) Demo — chuẩn bị & kiểm tra binary

- [ẢNH 01] `uname -m` = x86_64; `file ./ret2win`; `checksec`
- Môi trường: **Kali amd64 trên UTM (Emulate)** — được phép, cô lập
- [ẢNH 02] chạy input bình thường (mốc so sánh)

*Ghi chú nói:* nói rõ chạy trong VM emulate; đây là giới hạn (slide 13).

---

## Slide 8 — (Mục 7) Demo — đã điều khiển địa chỉ trả về

- offset = **40 byte** (từ disassembly: buffer 32 + saved rbp 8)
- [ẢNH 04] **Lần chạy đầu** (payload = `A*40 + p64(ret2win)`, chưa căn lề):
  - In ra **"Well done! Here's your flag:"** → đã nhảy vào `ret2win()`
  - Rồi **SIGSEGV** trong `system()` (stack lệch 16 byte)
- Bằng chứng: chương trình **chạy code của ret2win** = **đã điều khiển địa chỉ trả về**, mạnh hơn "chỉ crash"

> Phân biệt mức bằng chứng: ở đây là "đã đổi luồng thực thi", chưa phải "đạt mục tiêu" (flag chưa in vì system crash).

*Ghi chú nói:* đây là lý do phải căn lề — dẫn sang slide 9.

---

## Slide 9 — (Mục 7) Demo — đạt mục tiêu challenge

- **Lần chạy thứ 2** — thêm ret gadget `0x400770` căn lề:
  - Payload = `b'A'*40 + p64(0x400770) + p64(0x400756)`
- [ẢNH 05] exit code **0**, in ra flag: **`ROPE{a_placeholder_32byte_flag!}`** → **đạt mục tiêu**
- Vì sao cần ret gadget: `system()` dùng lệnh `movaps` đòi stack bội số 16 byte; một `ret` đẩy stack lệch 8 byte cho khớp
- Demo chạy lại **≥ 2 lần** ổn định (exit 0)

*Ghi chú nói:* câu chuyện 2 bước (control → align → flag) chính là điểm nhấn. Nếu demo trực tiếp lỗi → dùng ảnh/video dự phòng.

---

## Slide 10 — (Mục 6) CVE thật — CVE-2015-7547 (glibc)

| Mục | Nội dung |
|---|---|
| Sản phẩm | glibc (getaddrinfo), ảnh hưởng RHEL 6/7, Debian/Ubuntu/SUSE… |
| Phiên bản | **2.9–2.22**, vá từ **2.23** |
| CWE (NVD) | **CWE-119** (bản chất là 121, con của 119) |
| CVSS | v2 **6.8** / v3.0 **8.1 (High)**; Red Hat: **Critical** |

*Ghi chú nói:* nhấn: NVD gán 119, bản chất kỹ thuật là 121 — không tự sửa nhãn.

---

## Slide 11 — (Mục 6) CVE-2015-7547 — cơ chế & khắc phục

- `getaddrinfo()` truy vấn **song song A + AAAA**
- Buffer **2048 byte** cấp bằng `alloca()` trên stack
- Lỗi: **sai đồng bộ con trỏ/kích thước** ở phản hồi thứ hai → ghi tới ~63 KB dữ liệu đối phương
- Dữ liệu đối phương: **phản hồi DNS tạo riêng** (DNS độc hại / MITM)
- Khắc phục: **vá glibc ≥ 2.23**; workaround (giới hạn TCP ≤1023B) hạn chế; **tắt IPv6 vô dụng**
- Chỉ nghiên cứu/trình bày, **không tái hiện khai thác**

*Ghi chú nói:* so với ret2win: cùng "ghi vượt buffer stack", khác ở nguồn (mạng) và logic (con trỏ/kích thước).

---

## Slide 12 — (Mục 8) Khắc phục & phòng ngừa

- Gốc rễ: **giới hạn ghi theo kích thước đích** (`snprintf`, `fgets`, kiểm tra độ dài) — xem bài tập 3 đoạn
- Mã lỗi vs mã sửa: [notes/bai_tap_3_doan_ma](../notes/bai_tap_3_doan_ma/)
- Các lớp bảo vệ (bảng):

| Cơ chế | Tác dụng | Giới hạn | ret2win |
|---|---|---|---|
| Stack canary | Phát hiện ghi tràn tới return | Không chặn ghi biến trước canary | **Tắt** |
| NX | Stack không thực thi | Không chặn ret-to-function/ROP | **Bật** |
| ASLR/PIE | Ngẫu nhiên hóa địa chỉ | Có thể lộ qua lỗi khác | **PIE tắt** |

*Ghi chú nói:* bảo vệ **giảm** khả năng khai thác, không **xóa** lỗi.

---

## Slide 13 — (Mục 9) Điều kiện & giới hạn

| Hạng mục | Trạng thái |
|---|---|
| Input tới sink | Đã xác nhận (demo) |
| Offset đo trên binary | Đã xác nhận = **40** (buffer 32 + rbp 8) |
| Điều khiển địa chỉ trả về | Đã xác nhận (ảnh 04: in "Well done" rồi SIGSEGV) |
| Đạt mục tiêu (in flag) | Đã xác nhận (ảnh 05: exit 0, ra flag) |
| ASLR lúc chạy | Quan sát dưới **emulation**, không đại diện máy thật |
| CVE: tự tái hiện khai thác | **Không làm** (chỉ nghiên cứu) |

*Ghi chú nói:* thành thật về điều chưa kiểm chứng.

---

## Slide 14 — (Mục 10) Kết luận & tài liệu

- Lỗi tràn stack: ghi vượt buffer → đè địa chỉ trả về → đổi luồng thực thi
- Đã chứng minh trên ret2win (đạt mục tiêu); CVE-2015-7547 cho thấy tác động thật ở quy mô lớn
- Phòng ngừa: **giới hạn ghi** + các lớp bảo vệ
- Tài liệu: MITRE CWE-121/787/119; ROP Emporium; NVD/Red Hat/Google (CVE-2015-7547); GCC stack protector; Clang ASan

*Ghi chú nói:* 3 ý kết luận ngắn, không phóng đại. Ghi nguồn đã tra lại.
