# Giải thích demo `split` cho người nghe — "dùng gì, vì sao" & "đo gì, vì sao"

Viết cho: khán giả seminar / bạn cùng nhóm chưa quen pwn. Dùng làm speaker notes
cho slide demo (mục 7–10). Số liệu bám kết quả thật đã đo 2026-11-05
(xem [../demo/ket_qua_demo.md](../demo/ket_qua_demo.md)).

Ý tưởng gốc xuyên suốt: **ta chỉ ghi được dữ liệu lên stack qua lỗi tràn, nhưng
muốn chương trình tự chạy `system("/bin/cat flag.txt")`.** Mọi thứ trong exploit
và mọi phép đo đều để biến "ghi được dữ liệu" thành "gọi được hàm với đối số đúng".

---

## PHẦN 1 — Exploit dùng gì, vì sao

| Thành phần | Giá trị thật | Vì sao dùng |
|---|---|---|
| `context.arch="amd64"` | — | Để `p64()` đóng gói 8 byte little-endian đúng cách CPU đọc địa chỉ; sai kích thước/byte-order là nhảy lệch. |
| `ELF("./split")` | — | Tự tra địa chỉ từ binary thay vì gõ cứng; tránh nhầm, và các địa chỉ cố định được là nhờ **No PIE**. |
| `elf.plt["system"]` | `0x400560` | Ô PLT cố định trong chương trình, dẫn sang libc `system`. Nhắm PLT vì nó **cố định (No PIE)**, khỏi cần libc base → đây là **ret2plt**, không phải vượt ASLR. |
| `elf.symbols["usefulString"]` | `0x601060` | `system` cần **con trỏ tới chuỗi lệnh**; chuỗi `/bin/cat flag.txt` đã nằm sẵn trong `.data` → tái sử dụng dữ liệu có sẵn. |
| gadget `pop rdi ; ret` | `0x4007c3` | ABI System V AMD64 đặt **đối số 1 ở RDI**, không ở stack. Lỗi tràn chỉ ghi được stack → cần gadget "bơm" stack→RDI. |
| gadget `ret` (căn lề) | `0x40053e` | `system` có `movaps` đòi stack căn 16 byte; thêm một `ret` đẩy RSP 8 byte để căn đúng, tránh fault. |

**Payload và vì sao đúng thứ tự:**
```
b"A"*40  +  p64(0x40053e)  +  p64(0x4007c3)  +  p64(0x601060)  +  p64(0x400560)
 (đệm)       ret căn lề        pop rdi;ret       chuỗi lệnh         system@plt
```
Chìa khoá: mỗi gadget kết thúc bằng `ret` = "lấy địa chỉ kế tiếp trên stack rồi nhảy
tới". Stack thành **danh sách việc cần làm**:
1. `"A"*40` lấp tới saved return address (offset 40).
2. `ret` lần đầu → `0x40053e` (căn lề) → `ret` đi tiếp.
3. `0x4007c3` (`pop rdi`) → pop `0x601060` vào RDI → `ret` đi tiếp.
4. RDI đã trỏ chuỗi → `ret` → `0x400560` = `system@plt`.
5. `system` chạy với đối số đúng → in flag.

Không đảo được thứ tự: phải **căn lề → nạp RDI → rồi mới gọi system**; đặt system
trước khi nạp RDI thì nó chạy với đối số rác.

Gửi payload qua **đúng cổng input hợp lệ** (`sendline`) — không sửa binary, không tiêm
mã. Toàn bộ tấn công đi qua kênh nhập liệu bình thường; đó là điểm đáng sợ của lỗ hổng.

Chốt cho khán giả: không dòng nào là phép thuật — mỗi phần tử chỉ là **một địa chỉ có
sẵn trong chương trình**, xếp đúng thứ tự để lợi dụng `ret` và quy ước gọi hàm.

---

## PHẦN 2 — Bước đo: vì sao cần đúng các số đó, vì sao phải ĐO

Exploit là một **chuỗi phụ thuộc**. Mỗi số đo trả lời một câu hỏi mà bước sau bắt
buộc phải biết. Không đo thì chỉ là đoán — đoán sai địa chỉ = crash, không phải khai
thác. Và theo nguyên tắc nhóm: chỉ phát biểu điều có bằng chứng, nên mỗi số đo là
*bằng chứng* cho một mắt xích. Ta đo đúng ba nhóm, không thừa:

### Đo 1 — `checksec` + ASLR → "ĐƯỢC PHÉP dùng kỹ thuật nào?"
- NX bật → không tiêm shellcode được → buộc tái sử dụng mã.
- No canary → ghi tràn thẳng tới saved RIP, khỏi leak canary.
- No PIE → địa chỉ code/.data cố định → dùng số literal.
- ASLR=2 → chỉ xáo libc/stack; ta không đụng libc nên không bị cản.
**Phải đo TRƯỚC khi viết payload** vì hình dạng payload (shellcode hay ROP, có cần
leak không, địa chỉ cứng hay động) phụ thuộc hoàn toàn các bảo vệ này. Đo bảo vệ =
chọn chiến lược.

### Đo 2 — Offset = 40 → "VÔ-LĂNG nằm ở đâu?"
Saved return address là vô-lăng; offset 40 là khoảng cách chính xác từ đầu input tới
nó. Ghi thiếu → không chạm; ghi lệch → gãy chuỗi. Con số này đặc trưng từng binary
(buffer + saved RBP + layout compiler) nên **không đoán, không chép bài khác được**.
Phải đo ở đây vì mọi địa chỉ ở Phần 1 đặt *tương đối sau 40 byte đệm* — offset là bản
lề biến "crash lung tung" thành "crash có kiểm soát".
Điểm dạy: RIP lúc crash = `"kaaalaaa"` (offset 40), RSP = `"maaa"` (offset 48); chênh
8 vì `ret` đã pop 8 byte vào RIP. Số 40-vs-48 chứng minh bằng mắt cách `ret` chạy.

### Đo 3 — Địa chỉ (`system@plt` `0x400560`, chuỗi `0x601060`, gadget `0x4007c3`) → "LÁI tới đâu?"
Nhảy tới địa chỉ là chuyện đúng từng byte; sai một hex là nhảy giữa lệnh khác → crash.
Để pwntools đọc thẳng từ binary nên chắc đúng. Chúng tra được cố định là **nhờ Đo 1
(No PIE)** — thấy rõ mạch phụ thuộc: Đo 1 cho biết địa chỉ cố định → Đo 3 mới có nghĩa.

### Tóm Phần 2 trong một hình
**Đo 1 (được phép lái kiểu nào?) → Đo 2 (vô-lăng ở đâu?) → Đo 3 (lái tới đâu?).**
Ba câu hỏi nối tiếp, mỗi câu là tiền đề của câu sau. Đo đúng ba thứ vì exploit phụ
thuộc đúng ba thứ. Đo thay vì đoán vì đây là sự thật của riêng binary tại runtime —
đoán thì không kiểm chứng được.

---

## Ranh giới trung thực (nhắc khi trình bày)
Đây là **ret2plt**: địa chỉ cố định nhờ No PIE, không chứng minh tìm được libc base
hay vượt ASLR (ASLR vẫn =2). Direct ret2libc là nhánh lý thuyết/mở rộng, chưa làm.
