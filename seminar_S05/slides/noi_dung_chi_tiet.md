# S05 — Return-to-libc: nội dung chi tiết để soạn slide và giảng lại

> **Mục đích file này.** Đây là **kịch bản nội dung** cho người thuyết trình.
> - **Phần A — Lý thuyết nền:** mạch kiến thức từ số 0 để hiểu ret2libc (bộ nhớ → stack → call/ret → tràn buffer → chèn mã trên stack kiểu cũ → NX → ret2libc → ABI/gadget). Đọc kỹ phần này trước khi dựng slide; nó cũng là nội dung của các slide nền (2–4, có thể tách thêm slide nếu còn giờ).
> - **Phần B — 14 slide:** mỗi slide có **"Lên slide"** (chữ đưa lên slide, viết đủ ý để người đọc nhìn là hiểu) và **"Lời giảng"** (câu nói cho lớp) + ví von + mối liên hệ.
>
> **Nguồn số liệu.** Mọi offset/địa chỉ/flag là **số thật đo trên binary `split`** ngày 2026-11-05 ([../demo/ket_qua_demo.md](../demo/ket_qua_demo.md)). Hai CVE **chỉ nghiên cứu, không tái hiện** ([../cve/CVE-2018-5767.md](../cve/CVE-2018-5767.md), [../cve/CVE-1999-0032.md](../cve/CVE-1999-0032.md)). Kiến thức nền: [../KNOWLEDGE.md](../KNOWLEDGE.md). Yêu cầu đề: [../REQUIREMENTS.md](../REQUIREMENTS.md).
>
> **Ba ranh giới trung thực phải giữ nguyên khi lên slide** (AGENT.md mục 4):
> 1. Demo `split` là **ret2plt** (nhảy vào `system@plt` cố định nhờ No PIE), **chưa** chứng minh tính được libc base hay vượt ASLR của libc. ASLR máy vẫn bật (`randomize_va_space=2`).
> 2. Demo mới chạy **ra flag 1 lần** + quan sát GDB; **lần 2 ngoài GDB chưa chạy** — đề yêu cầu 2 lần liên tiếp, phải chạy nốt trước khi nói "chạy ổn định".
> 3. CVE không tái hiện; nhiều chi tiết CVE-2018-5767 lấy từ advisory/bản tóm tắt (writeup gốc đã bị gỡ) → nói "theo advisory", không khẳng định cấp địa chỉ/payload.

---

## 0. Bản đồ: 10 mục của đề ↔ 14 slide

Đề ([REQUIREMENTS.md](../REQUIREMENTS.md)) yêu cầu 10 mục. Bảng này chứng minh **bố cục đạt đủ requirement** — in ra để tự kiểm, không lên slide.

| Mục đề | Nội dung yêu cầu | Slide phụ trách | Lý thuyết nền |
|---|---|---|---|
| 1 | Giới thiệu lỗ hổng và bối cảnh | Slide 1 | — |
| 2 | Nguyên lý, điều kiện phát sinh, các dạng | Slide 2, 3, 4 | Phần A toàn bộ |
| 3 | CWE tương ứng và liên hệ chủ đề | Slide 2 (CWE), nhắc ở 5, 6 | A3 |
| 4 | Vị trí và nguyên nhân trong binary/mã | Slide 5, 6 (CVE), 8 (demo) | A2, A3 |
| 5 | Nguyên lý và chuỗi khai thác | Slide 4, 9, 10 | A4, A6, A7 |
| 6 | Phân tích ≥1 CVE thực tế (đủ 5 ý) | Slide 5 (lpr), 6 (Tenda) | — |
| 7 | Demo CTF Pwnable, môi trường cấp phép | Slide 7, 8, 9, 10 | A7 |
| 8 | Khắc phục, phòng ngừa, cơ chế bảo vệ | Slide 12 | A5 |
| 9 | Điều kiện, giới hạn khai thác | Slide 11, 13 | A6, A7 |
| 10 | Bài học và kết luận | Slide 13 | — |

Thời lượng mục tiêu **26 phút** (gồm 2–3 phút hỏi đáp). Bản rút 20 phút ở cuối file.

---

## Thông điệp xuyên suốt (nói ở slide 1, nhắc lại ở slide 13)

> **"Một lớp lỗi, một kỹ thuật, kéo dài 22 năm."**
> Cùng một lỗi (ghi tràn buffer trên stack — CWE-121) và cùng một kỹ thuật (đè địa chỉ trả về rồi **dùng lại hàm có sẵn trong thư viện** thay vì nạp mã mới) xuất hiện ở:
> - **1996** — `lpr` trên Unix, cục bộ, lên root (CVE-1999-0032);
> - **2018** — router Tenda AC15, **từ xa không cần đăng nhập**, CVSS 9.8 (CVE-2018-5767);
> - và ta **tự tay làm lại** trên challenge `split` (x86_64) để nhìn tận mắt từng bước.
>
> Điều **không đổi** suốt 22 năm: hàm chép dữ liệu chỉ hỏi *"nguồn hết chưa?"* mà không hỏi *"đích còn chỗ không?"*. Điều **đổi**: kiến trúc (x86 → ARM → x86_64) và lớp bảo vệ (có NX rồi vẫn thủng).

**Vì sao người nghe cần quan tâm:** NX/DEP được bật mặc định trên gần như mọi hệ ngày nay, và nhiều người tưởng "có NX là hết tràn stack". Bài này cho thấy **NX chỉ chặn một đường (chạy mã trên stack), không chặn đường dùng lại mã có sẵn.** Đó là lý do ret2libc vẫn sống.

---

# PHẦN A — LÝ THUYẾT NỀN CẦN BIẾT TRƯỚC

> Đọc hết phần này rồi hãy dựng slide. Mục tiêu: một người **chưa từng học khai thác lỗ hổng** đọc xong vẫn hiểu ret2libc là gì và vì sao nó tồn tại. Mạch logic đi tuần tự: chương trình nằm trong bộ nhớ ra sao (A1) → hàm chạy và trở về thế nào (A2) → tràn buffer đè được gì (A3) → **cách khai thác cũ: chèn shellcode lên stack** (A4) → NX giết cách cũ (A5) → **ret2libc là lối thoát** (A6) → gọi hàm cần đặt đối số đúng chỗ, sinh ra gadget (A7).
>
> Các sơ đồ dưới đây là **minh họa để hiểu cơ chế**, không phải bố cục đo trên binary thật. Con số thật (offset, địa chỉ) nằm ở Phần B, lấy từ demo.

## A1. Chương trình sống trong bộ nhớ như thế nào

Khi một chương trình chạy, hệ điều hành cấp cho nó một **không gian địa chỉ ảo** — hình dung như một dải bộ nhớ dài, chia thành nhiều **vùng**, mỗi vùng có công dụng và **quyền truy cập** riêng (đọc `r`, ghi `w`, thực thi `x`). Quyền này là chìa khóa của cả bài, nên phải nắm từ đầu.

```
   Địa chỉ CAO
   ┌───────────────────────────────┐
   │  Stack                        │  rw-   ← biến cục bộ, địa chỉ trở về của hàm
   │   (lớn dần xuống địa chỉ thấp) │        (với NX: KHÔNG có quyền x)
   ├───────────────────────────────┤
   │  Thư viện dùng chung (libc…)  │  r-x   ← MÃ của system(), printf()… nằm ở đây
   │                               │        (có quyền x — được phép chạy)
   ├───────────────────────────────┤
   │  Heap (lớn dần lên)           │  rw-   ← vùng malloc() cấp phát động
   ├───────────────────────────────┤
   │  .bss / .data                 │  rw-   ← biến toàn cục, chuỗi hằng
   ├───────────────────────────────┤
   │  .text (mã của chương trình)  │  r-x   ← MÃ chương trình, các entry PLT
   └───────────────────────────────┘
   Địa chỉ THẤP
```

| Vùng | Chứa gì | Quyền điển hình | Vai trò trong ret2libc |
|---|---|---|---|
| `.text` | mã máy của chương trình, bảng PLT | `r-x` (chạy được) | chứa `system@plt` — đích demo nhảy tới |
| `.data`/`.bss` | biến toàn cục, chuỗi hằng | `rw-` | có thể chứa chuỗi làm đối số (vd `"/bin/cat flag.txt"`) |
| Heap | vùng `malloc` | `rw-` | phân biệt với buffer stack khi xác định loại lỗi |
| **Stack** | biến cục bộ, **địa chỉ trở về** của hàm | `rw-`, **với NX thì KHÔNG có `x`** | nơi xảy ra tràn; nơi ta "viết kịch bản" khai thác |
| **libc** (ánh xạ) | **mã** của `system`, `printf`, `execve`… | `r-x` (chạy được) | "kho vũ khí có sẵn" mà ret2libc mượn |

**Điểm cốt lõi phải nhớ:** vùng chứa **mã** (`.text`, libc) thì **được phép chạy** (`x`); vùng chứa **dữ liệu** (stack, heap, data) thì **ghi được nhưng — nếu bật NX — không chạy được**. Toàn bộ câu chuyện ret2libc xoay quanh một mâu thuẫn: *kẻ tấn công kiểm soát được dữ liệu trên stack, nhưng stack lại không được phép chạy mã.*

## A2. Hàm được gọi và trở về như thế nào (`call` / `ret`)

Để hiểu "đè địa chỉ trả về", phải hiểu cơ chế gọi hàm. CPU dùng vài **thanh ghi** quan trọng:

- **`RIP`** (Instruction Pointer): địa chỉ lệnh CPU **đang** thực thi. Đổi được `RIP` = đổi được luồng chương trình.
- **`RSP`** (Stack Pointer): trỏ tới **đỉnh** stack hiện tại.
- **`RBP`** (Base Pointer): mốc của khung hàm hiện tại (có thể có hoặc không, tùy cách biên dịch).
- **`RDI`**: giữ **đối số thứ nhất** khi gọi hàm trên x86_64 (dùng ở A7).

Khi hàm `A` gọi hàm `B`, có hai lệnh then chốt:

```
call B :  (1) ĐẨY (push) lên stack địa chỉ của lệnh ngay SAU call  ← "địa chỉ trở về"
          (2) nhảy tới B (đặt RIP = B)

ret    :  (1) LẤY (pop) 8 byte ở đỉnh stack ra
          (2) đặt RIP = giá trị vừa lấy  ← chương trình "trở về" chỗ cũ
```

Nói cách khác: **`call` ghi nhớ "xong việc thì về đâu" bằng cách lưu một địa chỉ lên stack; `ret` tin tưởng tuyệt đối vào địa chỉ đó và nhảy về.** `ret` **không kiểm tra** địa chỉ đó có bị sửa hay không — đây chính là kẽ hở.

Trong lúc `B` chạy, nó tạo một **stack frame** chứa biến cục bộ (ví dụ `char buf[...]`). Bố cục điển hình (minh họa, địa chỉ cao ở trên):

```
   Địa chỉ CAO
   ┌────────────────────────────┐
   │  … frame của hàm gọi (A) …  │
   ├────────────────────────────┤
   │  ĐỊA CHỈ TRỞ VỀ (saved RIP) │ ← ret sẽ nhảy theo ô NÀY
   │  saved RBP (nếu có)         │
   │  … padding / canary …       │ ← bố cục tùy binary, PHẢI đo
   │  buf[N-1]                   │
   │  …                          │
   │  buf[0]                     │ ← biến cục bộ bắt đầu ở đây (địa chỉ thấp)
   └────────────────────────────┘
   Địa chỉ THẤP  (RSP trỏ quanh đây)
```

**Chú ý hướng:** `buf` nằm ở **địa chỉ thấp**, còn **địa chỉ trở về** nằm **phía trên** (địa chỉ cao hơn). Khi ta ghi `buf[0], buf[1], buf[2]…` tức là đi **lên** phía địa chỉ trở về. Ghi đủ xa sẽ chạm tới nó. Đó là cầu nối sang A3.

## A3. Tràn buffer đè được những gì

Ngôn ngữ C **không tự kiểm tra biên mảng**. `char buf[16]` chỉ hợp lệ ở chỉ số 0..15; ghi `buf[16]` trở đi là ghi ra ngoài — và C không ngăn. Nếu hàm chép dữ liệu vào `buf` mà **không giới hạn độ dài theo `sizeof(buf)`**, kẻ tấn công đưa chuỗi dài hơn 16 byte sẽ ghi tràn sang vùng phía trên.

Quá trình, từng bước:

```
Ghi 16 byte đầu   → lấp đầy buf[0..15]            (chưa sao)
Ghi tiếp          → đè saved RBP, padding, canary (bắt đầu phá frame)
Ghi tiếp nữa      → đè ĐỊA CHỈ TRỞ VỀ             ← mục tiêu!
Hàm chạy tới ret  → RIP = giá trị ta vừa ghi đè   → luồng chương trình đi theo ý ta
```

**Khoảng cách từ `buf[0]` tới ô địa chỉ trở về gọi là `offset`.** Kích thước buffer **không** cho ra offset (còn padding, saved RBP, biến khác chen vào) → **bắt buộc đo trên binary**. Ở demo, buffer không lớn mà offset đo ra là **40** (Phần B, slide 8).

**Phân biệt 3 mức — rất hay bị gộp nhầm, nói rõ cho lớp:**

| Mức | Nghĩa là gì | Đã chứng minh được gì |
|---|---|---|
| **Ghi vượt** | dữ liệu tràn ra ngoài `buf` | mới biết có lỗi ghi; chưa chắc chạm địa chỉ trở về |
| **Crash (SIGSEGV)** | chương trình chết | mới biết đã phá cái gì đó; **chưa** chứng minh điều khiển được luồng |
| **Chiếm luồng** | `RIP` nhận đúng giá trị ta đặt | giờ mới thực sự "cầm lái" |

Một lần crash **không** đồng nghĩa đã kiểm soát được chương trình. Đây là nguyên tắc trung thực xuyên suốt S05.

## A4. Cách khai thác CŨ: chèn mã trên stack (shellcode injection)

> **Đây là phần người nghe cần để hiểu ret2libc "giải quyết vấn đề gì".** Phải kể cách cũ trước, rồi mới thấy vì sao cần cách mới.

Trước khi có NX, ý tưởng khai thác kinh điển (bài "Smashing the Stack for Fun and Profit", Aleph One, 1996) là: **tự mang mã của mình vào rồi bắt CPU chạy nó.**

Cụ thể, kẻ tấn công nhồi vào `buf` không phải chuỗi rác, mà là **shellcode** — một đoạn **mã máy** ngắn, thường để mở một shell (gọi `execve("/bin/sh")`). Sau đó dùng phần tràn để **đè địa chỉ trở về bằng địa chỉ của chính `buf`**. Khi hàm `ret`, CPU nhảy *vào trong buffer* và **thực thi shellcode** như thể đó là mã hợp lệ.

```
   KHAI THÁC KIỂU CŨ (stack còn được phép chạy mã)

   ┌────────────────────────────┐
   │  địa chỉ trở về (bị đè)     │ ──┐  đè bằng địa chỉ trỏ NGƯỢC vào buf
   ├────────────────────────────┤   │
   │  …                          │   │
   │  [ SHELLCODE: mã máy của    │ ◄─┘  ret nhảy vào đây → CPU chạy shellcode
   │    kẻ tấn công, vd execve   │
   │    "/bin/sh" ]              │
   │  [ NOP NOP NOP … ] (NOP sled)│      đệm "trượt" để không cần đoán địa chỉ
   │  buf[0]                     │       chính xác tới từng byte
   └────────────────────────────┘
```

Vài điểm để giảng cho kỹ:

- **Shellcode = mã máy, không phải chuỗi văn bản.** Nó là các byte lệnh CPU, viết sao cho không chứa byte cấm (thường tránh `0x00` vì hàm chuỗi dừng ở đó — xem A3 và ca 1997).
- **NOP sled** (`0x90 0x90 …`): một dãy lệnh "không làm gì". Kẻ tấn công không biết chính xác `buf` nằm ở địa chỉ nào, nên đặt địa chỉ trở về trỏ vào *khoảng giữa* vùng NOP; CPU "trượt" qua các NOP rồi rơi vào shellcode. Đây là mẹo để bớt phụ thuộc địa chỉ chính xác.
- **Điều kiện sống còn:** cách này **chỉ chạy được nếu trang stack có quyền thực thi (`x`)**. Thời đó stack mặc định `rwx`.

**Chốt A4:** kiểu cũ = "mang súng của mình vào tòa nhà rồi bắn". Đơn giản, mạnh — nhưng hoàn toàn phụ thuộc việc stack cho phép chạy mã.

## A5. NX/DEP giết cách cũ

Để diệt kiểu tấn công trên, các hệ điều hành đưa vào **NX** (No-eXecute, còn gọi **DEP** — Data Execution Prevention; trên x86 phổ biến từ khoảng 2003–2004 nhờ bit NX phần cứng). NX làm **đúng một việc**:

> Đánh dấu các trang **dữ liệu** (stack, heap) là **không thực thi** (`rw-`, bỏ `x`).

Hệ quả với kiểu cũ:

```
   ret nhảy vào buf (chứa shellcode)
        → CPU định thực thi byte đầu của shellcode
        → trang stack KHÔNG có quyền x
        → CPU phát sinh lỗi (fault) → chương trình chết
        → shellcode trở thành "dữ liệu chết", không bao giờ chạy
```

Hai điều phải nhấn mạnh (vì chúng là bản lề của cả bài):

1. **NX không sửa lỗi tràn.** Buffer vẫn tràn như cũ, địa chỉ trở về vẫn bị đè như cũ. NX chỉ chặn *bước cuối*: chạy mã **trên stack**.
2. **NX không đụng tới mã đã có quyền chạy.** Mã trong `.text` và trong **libc** vẫn `r-x` — vẫn chạy bình thường. NX không có lý do gì cấm chúng.

Chính điểm (2) để lộ lối thoát cho kẻ tấn công.

## A6. Ret2libc: không mang mã mới, dùng lại mã có sẵn

Nếu không được chạy mã của mình trên stack, kẻ tấn công **không nhảy vào stack nữa** — mà nhảy vào **mã đã nằm sẵn trong bộ nhớ, ở vùng được phép chạy**. Nơi dồi dào nhất là **libc**: nó luôn được nạp, có quyền `r-x`, và chứa những hàm cực mạnh như `system()` (chạy một lệnh shell), `execve()`, v.v.

Ý tưởng **return-to-libc**:

```
   KHAI THÁC KIỂU MỚI (ret2libc) — stack KHÔNG cần chạy mã

   ┌────────────────────────────┐
   │  địa chỉ trở về (bị đè)     │ ── đè bằng ĐỊA CHỈ system() trong libc
   ├────────────────────────────┤
   │  [ địa chỉ "trở về" sau khi │
   │    system() xong ]          │
   │  [ đối số cho system():     │
   │    con trỏ tới "/bin/sh" ]  │   ← toàn là ĐỊA CHỈ và DỮ LIỆU, không phải mã
   │  … đệm tới địa chỉ trở về … │
   │  buf[0]                     │
   └────────────────────────────┘

   ret → RIP = system()  → CPU chạy system() (nằm trong libc, có quyền x)
                         → system đọc đối số → chạy "/bin/sh"
```

So sánh hai thời kỳ (slide 3 dùng đúng bảng này):

| | Chèn mã trên stack (cũ) | Return-to-libc (mới) |
|---|---|---|
| Mã chạy nằm ở đâu | trong `buf` (trên **stack**) | trong **libc** (vùng `r-x` có sẵn) |
| Stack chứa gì | **mã máy** (shellcode) | **dữ liệu**: địa chỉ hàm + đối số |
| NX cản được không | **Có** — stack không chạy được | **Không** — libc vốn được phép chạy |
| Ví von | mang súng của mình vào | dùng súng có sẵn trong kho |

**Điểm "aha" cho người nghe:** stack bây giờ không chứa *mã* mà chứa một **"kịch bản"** — gọi hàm nào, đưa đối số gì, xong thì đi đâu. Vì toàn là dữ liệu, **NX không có gì để cấm**. Đó là lý do ret2libc đánh bại NX mà không cần phá NX.

Ret2libc **ra đời chính thức năm 1997** khi Solar Designer dùng lỗi của `lpr` (ca CVE ở slide 5) để trình diễn — đúng ngữ cảnh "stack đã bị khóa thực thi".

## A7. Gọi hàm cần đặt đối số đúng chỗ → sinh ra "gadget" và ROP

Nhảy tới `system` mới trả lời được *"chạy ở đâu"*. Còn *"`system` lấy đối số từ đâu"*? Tùy **ABI** (quy ước gọi hàm) của từng kiến trúc:

| Kiến trúc | Đối số thứ nhất đặt ở đâu | Hệ quả cho payload |
|---|---|---|
| x86 32-bit (cdecl) | **trên stack** | chỉ cần xếp con trỏ đối số lên stack — payload đơn giản (ca 1996) |
| **x86_64 (System V)** | **trong thanh ghi `RDI`** | stack không tự vào `RDI` được → **cần gadget** (demo của ta) |
| ARM 32-bit | trong thanh ghi **`r0`** | cũng cần gadget nạp `r0` (ca Tenda 2018) |

Trên x86_64/ARM, muốn đặt giá trị vào thanh ghi, kẻ tấn công mượn một **gadget**: một đoạn lệnh **ngắn, có sẵn trong binary, kết thúc bằng `ret`**. Gadget kinh điển:

```
   pop rdi ; ret
   │        └─ ret: nhảy tiếp theo giá trị kế trên stack (đi tới bước sau)
   └─ pop rdi: LẤY 8 byte trên đỉnh stack ĐẶT vào RDI
```

Ghép nhiều gadget nối tiếp nhau (mỗi cái kết thúc `ret` để "chuyền" sang cái sau) gọi là **ROP — Return-Oriented Programming**. Ret2libc đời thực thường là một chuỗi ROP ngắn: *gadget đặt đối số → gọi hàm libc*.

**Ba tên gọi — đừng nhầm (slide 4 dùng lại):**

| Thuật ngữ | Đích nhảy / bản chất | Liên quan ASLR |
|---|---|---|
| **ret2plt** | nhảy vào `system@plt` — entry trong **chương trình** | nếu No PIE thì địa chỉ cố định → **né được ASLR của libc** (đây là demo của ta) |
| **direct ret2libc** | nhảy thẳng vào `system` **trong libc** | phải biết libc base → **vướng ASLR**, thường cần leak địa chỉ |
| **ROP** | ghép nhiều gadget `…; ret` để dựng trạng thái | kỹ thuật chung, ret2libc là một ứng dụng của nó |

> **Chốt Phần A (một câu để chuyển sang CVE/demo):** *"Lỗi tràn buffer cho tôi quyền ghi đè địa chỉ trở về (A3). Kiểu cũ nhét shellcode vào stack rồi nhảy vào đó (A4), nhưng NX giết nó (A5). Ret2libc không mang mã mới — nó trỏ địa chỉ trở về vào hàm có sẵn trong libc, dùng stack như một kịch bản dữ liệu (A6), và dùng gadget để đặt đối số cho đúng ABI (A7). Giờ ta xem nó xảy ra thật."*

---

# PHẦN B — 14 SLIDE CHI TIẾT

## SLIDE 1 — Giới thiệu và bối cảnh *(mục 1 · ~1 phút)*

**Lên slide**
- **Tiêu đề:** Return-to-libc (ret2libc) — điều khiển luồng thực thi để **dùng lại hàm có sẵn trong thư viện hệ thống**, khi không thể chạy mã trên stack.
- **Định nghĩa một dòng:** thay vì nạp mã mới của kẻ tấn công (bị NX chặn), ta đè địa chỉ trở về để nhảy vào hàm libc đã có (`system`, `execve`…), chuẩn bị sẵn đối số trên stack.
- **Buổi học trả lời 3 câu hỏi:**
  1. Lỗi nào cho ta quyền đổi luồng thực thi? (tràn buffer trên stack — CWE-121)
  2. Làm sao gọi được hàm libc với đúng đối số khi stack không chạy được mã? (gadget + ABI)
  3. Vì sao NX bật mà vẫn bị khai thác? (NX không chặn việc dùng lại mã có sẵn)
- **Ba ca đi cùng nhau:** `lpr` 1996 (cục bộ) · Tenda AC15 2018 (từ xa, CVSS 9.8) · demo `split` (tự khai thác).
- Nhóm A/B/C — `[CHƯA CHỐT]`; ngày seminar `[CHƯA CHỐT]`.

**Lời giảng**
> "Hình dung bạn tìm được lỗi tràn bộ đệm và chiếm được quyền quyết định chương trình chạy tiếp ở đâu. Phản xạ cũ là nhét đoạn mã của mình vào bộ nhớ rồi nhảy tới. Nhưng hệ điều hành hiện đại bật **NX** — stack không được thực thi — nên mã bạn nhét vào thành dữ liệu chết.
>
> Ret2libc trả lời: *'không cần mang mã mới — mã tôi cần đã có sẵn trong máy.'* libc chứa `system`, `execve`, `open`… Tôi chỉ cần trỏ luồng tới một hàm có sẵn, chuẩn bị đối số, là xong — không vi phạm NX vì libc vốn được phép chạy.
>
> Hôm nay đi ba chặng: lỗi kinh điển 1996, lỗi thật 2018 trên router, và một challenge ta tự khai thác. Cuối buổi bạn phân biệt được *crash*, *chiếm luồng*, và *gọi được hàm* — ba thứ rất khác nhau hay bị gộp."

**Ví von (dùng lại cả bài):** NX = *"cấm mang súng của mình vào tòa nhà"*; ret2libc = *"vậy tôi dùng súng treo sẵn trong kho của tòa nhà"* — đúng luật, vẫn đạt mục đích.

---

## SLIDE 2 — Nền tảng: tràn buffer, địa chỉ trở về, CWE *(mục 2 + 3 · ~2 phút)*

> Nền chi tiết: Phần A2–A3. Nếu còn giờ, tách slide này thành 2 (một stack/call-ret, một CWE).

**Lên slide**
- **Lỗi gốc — đoạn C điển hình:**
  ```c
  void show_name(const char *input) {
      char buf[16];
      strcpy(buf, input);   // chép tới byte '\0' của input, KHÔNG so với sizeof(buf)
      puts(buf);
  }
  ```
- **source → sink → guard:** Source = `input` (do người dùng); Sink = `strcpy(buf,input)`; Guard = **không có** → tràn khi `strlen(input) ≥ 16`.
- **Cơ chế đè (nhắc hướng stack):** `buf` ở địa chỉ thấp, **địa chỉ trở về** ở phía trên; ghi tràn đủ xa → đè địa chỉ trở về → lệnh `ret` nhảy theo giá trị ta đặt. Khoảng cách `buf[0]`→địa chỉ trở về = **offset**, *phải đo* (demo ra 40, không phải 16).
- **Ba mức tách bạch:** ghi vượt ≠ crash ≠ chiếm luồng.
- **Phân loại CWE:**
  - **CWE-787** — Out-of-bounds Write (lớp cha).
  - **CWE-121** — Stack-based Buffer Overflow (tràn buffer *trên stack*) — đây là lỗi nền của cả 2 CVE + demo.
  - ⚠️ **ret2libc KHÔNG phải CWE** — nó là *kỹ thuật khai thác* lỗi CWE-121.

**Lời giảng**
> "Ba đại lượng hay nhầm: **dung lượng vùng đệm** (`buf` = 16 byte), **độ dài chuỗi** (`strlen`), và **số byte thực ghi**. `strcpy` chép tới khi gặp `\0` của *nguồn* — nó hỏi *'nguồn hết chưa?'* chứ không hỏi *'`buf` còn chỗ không?'*. **Lỗi tư duy này** lặp lại ở cả ba ca hôm nay, y hệt.
>
> Vì sao nguy hiểm? Như Phần nền: `buf` nằm dưới, địa chỉ trở về nằm trên; ghi tràn bò lên và đè được nó. Lệnh `ret` lấy đúng ô đó làm đích nhảy mà **không kiểm tra** — ai cầm được ô đó thì cầm lái chương trình.
>
> Phân loại cho chuẩn: lỗi là **CWE-121**, con của **CWE-787**. Còn 'ret2libc' là **cách khai thác** — đừng gọi ret2libc là CWE. Câu này tôi lặp ở mỗi CVE: *'lỗi là CWE-121; ret2libc là kỹ thuật.'*
>
> Và nhớ: sơ đồ stack là minh họa; khoảng cách thật tới địa chỉ trở về **phải đo** — lát nữa đo ra **40**, không phải 16."

---

## SLIDE 3 — Hai thời kỳ: chèn mã trên stack → NX → return-to-libc *(mục 2 · ~2 phút)*

> Nền chi tiết: Phần A4–A6. Đây là slide "trái tim" của phần lý thuyết — đừng rút gọn quá.

**Lên slide**
- **(1) Kiểu cũ — chèn shellcode lên stack:** nhồi **mã máy** (shellcode `execve("/bin/sh")`) vào `buf`, đè địa chỉ trở về trỏ **ngược vào buf**; khi `ret`, CPU chạy mã trong buffer. Mẹo **NOP sled** để khỏi đoán địa chỉ chính xác. *Điều kiện: stack phải có quyền thực thi.*
- **(2) NX/DEP (từ ~2003):** đánh dấu stack **không thực thi** → shellcode trên stack thành **dữ liệu chết**, CPU từ chối chạy → kiểu cũ hỏng.
- **(3) Return-to-libc (lối thoát):** **không** nhét mã mới; đè địa chỉ trở về trỏ vào **`system()` có sẵn trong libc** (vùng được phép chạy); stack giờ chứa **kịch bản dữ liệu**: địa chỉ hàm + đối số.
- **Bảng so sánh:**

  | | Chèn mã (cũ) | Ret2libc (mới) |
  |---|---|---|
  | Mã chạy ở đâu | trong `buf` (stack) | trong libc (`r-x`) |
  | Stack chứa | mã máy (shellcode) | dữ liệu: địa chỉ + đối số |
  | NX cản? | **Có** | **Không** |
- **Câu chốt:** *"NX hạn chế **nơi** được chạy mã; nó không sửa lỗi tràn, cũng không cấm **dùng lại** mã có sẵn."*

**Lời giảng**
> "Phải kể cách cũ mới hiểu vì sao cần cách mới. Thời trước NX, khai thác kinh điển là: nhồi **shellcode** — mã máy mở shell — vào buffer, rồi đè địa chỉ trở về cho nó trỏ *ngược vào chính buffer*. `ret` nhảy vào đó, CPU chạy mã của kẻ tấn công. Vì không biết buffer nằm đúng địa chỉ nào, người ta đệm một dãy **NOP** — lệnh 'không làm gì' — rồi trỏ vào khoảng giữa; CPU trượt qua NOP rồi rơi vào shellcode. Nhưng tất cả **chỉ chạy nếu stack được phép thực thi**.
>
> Khoảng 2003, **NX** ra đời: stack bị đánh dấu *không thực thi*. Giờ `ret` nhảy vào buffer, CPU định chạy byte đầu của shellcode thì gặp trang không có quyền `x` → lỗi → chương trình chết. Shellcode thành rác. **Nhưng** — và đây là mấu chốt — NX **không** sửa lỗi tràn (buffer vẫn tràn, địa chỉ trở về vẫn bị đè), và **không** đụng mã đã được phép chạy như libc.
>
> Ret2libc khai thác đúng kẽ đó: đừng mang mã mới, hãy trỏ địa chỉ trở về vào **`system()` trong libc** — vốn `r-x`. Stack bây giờ không chứa *mã* mà chứa *kịch bản*: gọi hàm nào, đối số gì. Toàn dữ liệu — NX không có gì để cấm. Đây chính là 'dùng súng có sẵn trong kho'."

---

## SLIDE 4 — ABI và gadget: ret2plt · direct ret2libc · ROP *(mục 2 + 5 · ~1,5 phút)*

> Nền chi tiết: Phần A7.

**Lên slide**
- **Vấn đề:** nhảy tới `system` mới là *"chạy ở đâu"*; còn phải đặt **đối số** đúng chỗ ABI quy định, nếu không `system` không biết chạy lệnh gì.
- **Đối số thứ nhất nằm ở đâu:** x86 cdecl → **trên stack**; **x86_64 → thanh ghi `RDI`**; ARM → thanh ghi **`r0`**.
- **Gadget:** đoạn lệnh ngắn có sẵn, kết thúc `ret`, để nạp thanh ghi. Kinh điển: `pop rdi ; ret` (lấy 8 byte trên stack đặt vào `RDI` rồi đi tiếp). Nối nhiều gadget = **ROP**.
- **Ba tên — phân biệt rạch ròi:**

  | Kỹ thuật | Đích nhảy | ASLR |
  |---|---|---|
  | **ret2plt** | `system@plt` trong **chương trình** | No PIE → cố định, **né ASLR libc** (← demo) |
  | **direct ret2libc** | `system` **trong libc** | cần biết libc base → **vướng ASLR** |
  | **ROP** | ghép nhiều gadget `…;ret` | kỹ thuật nền chung |

**Lời giảng**
> "Slide quyết định payload trông thế nào. Nhảy tới `system` trả lời *'chạy ở đâu'*. Còn *'lấy đối số từ đâu'* thì tùy kiến trúc. x86 cũ: đối số trên stack — nên exploit 1996 chỉ cần xếp con trỏ `/bin/sh` lên stack. **x86_64**: quy ước System V bắt đối số thứ nhất nằm trong **`RDI`**, mà stack không tự chui vào thanh ghi được.
>
> Lối ra là **gadget** — mẩu mã ngắn có sẵn, kết thúc `ret`. Kinh điển `pop rdi ; ret`: pop 8 byte kế trên stack vào `RDI`, rồi `ret` đi tiếp. Tôi đặt con trỏ chuỗi lên stack, cho gadget bơm vào `RDI`, rồi mới nhảy `system`. Ghép vài mẩu như vậy gọi là **ROP**.
>
> Ba tên phải nói đúng: **ret2plt** nhảy vào `system@plt` của *chương trình* — không cần biết libc nằm đâu, nên né ASLR của libc; đây là cái demo ta làm. **direct ret2libc** nhảy thẳng vào `system` *trong libc*, mạnh hơn nhưng phải biết địa chỉ libc mà ASLR xáo trộn. Nói đúng tên là điểm cộng khi chấm."

**Ghi nhớ nối demo:** demo `split` dùng đúng chuỗi `pop rdi; ret` → con trỏ chuỗi → `system@plt`. Người nghe sẽ thấy lại y hệt ở slide 9.

---

## SLIDE 5 — CVE bước đệm: CVE-1999-0032 (lpr, 1996) *(mục 6 · ~1,5–2 phút)*

> Giữ **đủ 5 ý**, nói gọn **không cụt**. Chi tiết: [../cve/CVE-1999-0032.md](../cve/CVE-1999-0032.md).

**Lên slide**
- **Đoạn code lỗi** (tô đậm vòng `while`):
  ```c
  card(c, p2) char c, *p2; {
      char buf[BUFSIZ];              // BUFSIZ = 1024, biến cục bộ → nằm trên stack
      char *p1 = buf; int len = 2;
      *p1++ = c;
      while ((c = *p2++) != '\0')    // chỉ hỏi "nguồn hết chưa?"
          *p1++ = c;                 // KHÔNG so len với sizeof(buf) → tràn
      *p1++ = '\n';
      write(tfd, buf, len);
  }
  ```
- **5 ý bắt buộc:**
  1. **Lỗi gì/ở đâu:** `lpr` (lệnh in) chép đối số `-C` (nhãn phân loại) vào `buf[1024]` trong hàm `card()` bằng vòng dừng ở `\0`, không đo độ dài → tràn stack, đè địa chỉ trở về.
  2. **Vì sao thành root:** `lpr` cài **setuid root** → luồng bị chiếm chạy quyền root → **leo quyền cục bộ user→root**.
  3. **Cái nôi của chủ đề:** 1997 Solar Designer dùng chính lỗi này **trình diễn return-into-libc đầu tiên** (stack đã bị khóa thực thi → trỏ địa chỉ trở về vào `system()`, đối số `"/bin/sh"`).
  4. **Ràng buộc byte `0x00`:** địa chỉ libc chứa byte `0` làm chuỗi dừng sớm → **21 năm sau Tenda vẫn gặp**.
  5. **Nhãn:** NVD = `NVD-CWE-Other`; nhóm phân loại **CWE-121**; ret2libc là kỹ thuật, không phải CWE.
- **Mức độ:** CVSS v2 **7.2**, `AV:L` (**cục bộ**).

**Lời giảng**
> "Đây là *cái nôi*, nói nhanh nhưng đủ. `lpr` là lệnh in, cài **setuid root** — ai chạy cũng được nhưng tiến trình mang quyền root. Tùy chọn `-C` chỉ là nhãn phân loại. Chương trình đưa chuỗi `-C` vào hàm `card()`, và `card()` có vòng `while` chép từng byte **tới khi gặp `\0`**, không bao giờ kiểm `buf` còn chỗ. `buf` 1024 byte; chuỗi ~1023 byte trở lên là ghi ra ngoài, đè địa chỉ trở về, chương trình **đang chạy quyền root** nhảy theo ý bạn → **user lên root**.
>
> Vì sao đáng kể: năm **1997**, Solar Designer dùng đúng lỗi `lpr -C` công bố **return-into-libc đầu tiên** của thế giới — lúc đó stack đã bị vá cho không thực thi (như NX), shellcode chết, nên ông đè địa chỉ trở về bằng địa chỉ **`system()` trong libc**, đối số `"/bin/sh"`. Kỹ thuật hôm nay ra đời từ đây.
>
> Chi tiết vọng lại 2018: vì vòng dừng ở `\0`, **địa chỉ đưa vào không được chứa byte `0x00`** — ràng buộc mà 21 năm sau người khai thác Tenda vẫn gặp. Nhãn: NVD không gán CWE cụ thể; nhóm phân loại **CWE-121**. Lặp lại: *lỗi là CWE-121, ret2libc là kỹ thuật.*"

**Câu chuyển:** *"Đó là 1996, máy chủ Unix, cục bộ. Giờ xem đúng lớp lỗi và kỹ thuật này năm 2018 — từ xa, trên một router thật."*

---

## SLIDE 6 — CVE chính: CVE-2018-5767 (Tenda AC15) *(mục 6 · ~3 phút — 2 slide phụ)*

> Chi tiết + ranh giới: [../cve/CVE-2018-5767.md](../cve/CVE-2018-5767.md). **Chỉ nghiên cứu, không tái hiện.**

### 6A — "Lỗi nằm ở đâu"

**Lên slide**
- **Request tấn công:** `Cookie: password=<chuỗi dài do kẻ tấn công đặt>;...` — gửi qua mạng, **không cần đăng nhập**.
- **Cơ chế** (mã **minh họa**, KHÔNG phải mã gốc — writeup đã gỡ):
  ```c
  // minh họa cơ chế
  char buf[/* cố định */];
  char *p = strstr(cookie, "password=");
  if (p) sscanf(p + 9, "%[^;]", buf);   // chép tới khi gặp ';', KHÔNG giới hạn độ dài
  ```
- **4 ý:**
  1. Router Tenda AC15; giao diện web do binary **`httpd`** phục vụ, chạy **quyền cao**.
  2. Gửi Cookie `password=` dài, **không cần xác thực** (lỗi nằm trước khâu đăng nhập).
  3. Hàm **`R7WebsSecurityHandler`** dùng `strstr` lấy phần sau `password=`, rồi `sscanf` định dạng `%[^;]` chép vào **buffer cố định trên stack** — chép tới khi gặp `;`, **không đo độ dài** (đúng kiểu vòng `while` của `lpr`).
  4. Tràn stack → đè địa chỉ trở về của `R7WebsSecurityHandler`. **NVD gán CWE-20; lỗi nền = CWE-121.**

**Lời giảng**
> "Cùng lỗi tư duy, đổi vỏ. Web của router do `httpd` phục vụ, chạy quyền cao. Bạn gửi HTTP request với `Cookie: password=` rồi một chuỗi thật dài — **không cần đăng nhập**, vì lỗi ở khâu xử lý Cookie *trước* khi kiểm tra đăng nhập.
>
> Hàm `R7WebsSecurityHandler` tìm `password=`, rồi `sscanf` với `%[^;]` — nghĩa là *'chép mọi ký tự tới khi gặp dấu chấm phẩy'*. Quen không? Đúng kiểu vòng `while` của `lpr`: chép tới ký tự dừng, **không có tham số giới hạn kích thước đích**. Cookie đủ dài → tràn buffer stack của hàm → đè địa chỉ trở về.
>
> NVD gán **CWE-20** (không kiểm input — mô tả *nguyên nhân*); còn *lỗi nền* theo mô tả mã là **CWE-121**. Nói cả hai để khỏi bị bắt bẻ."

### 6B — "Vì sao vẫn RCE dù có NX"

**Lên slide**
- `httpd` **bật NX** (NX thật của nền tảng 2018) → shellcode trên stack vô dụng → **buộc dùng ret2libc/ROP**.
- **ARM**: đối số thứ nhất nằm trong thanh ghi **`r0`** (giống `RDI` của x86_64) → cần **gadget nạp `r0`** rồi mới gọi hàm libc — **đúng cơ chế demo, chỉ đổi thanh ghi**.
- **Ràng buộc địa chỉ (lặp lại 1997):** gadget trong `httpd` ở **địa chỉ cố định** (không PIE) nhưng **chứa byte null → chỉ dùng được một lần** — đúng ràng buộc byte `0x00` năm 1997. *(Theo bản tóm tắt; chưa đọc writeup gốc.)*
- **Kết quả:** **RCE từ xa, không xác thực, CVSS 9.8** — nghiêm trọng hơn hẳn ca 1999 (cục bộ, 7.2).

**Lời giảng**
> "Đây là lúc cả bài khớp lại. Router này **đã bật NX** — hãng tưởng đã an toàn trước tràn stack. Nhưng NX chỉ chặn chạy mã *trên stack*, không chặn *dùng lại mã có sẵn*. Trên ARM, đối số thứ nhất nằm trong **`r0`** — giống `RDI` ta vừa học. Nên kẻ tấn công dùng **gadget** nạp `r0` rồi gọi hàm thư viện. **Chính là chuỗi ROP lát nữa ta tự làm ở demo, chỉ đổi tên thanh ghi.**
>
> Chi tiết đẹp nhất: theo advisory, gadget trong `httpd` **chứa byte null nên chỉ dùng được một lần** — đúng ràng buộc byte `0x00` Solar Designer vướng năm 1997. **21 năm, cùng một bài toán.**
>
> Kết quả: **RCE từ xa, không cần đăng nhập, CVSS 9.8** — nặng hơn hẳn ca 1999 (cục bộ, 7.2). Thiết bị *có NX* vẫn thủng vì thiếu các lớp còn lại (ASLR đầy đủ/PIE/canary) và vì **lỗi gốc không được sửa**."

**Ranh giới (nói miệng):** writeup gốc Fidus đã bị gỡ, offset bị redact → format `sscanf` chính xác, kích thước buffer, gadget cụ thể **nhóm chưa đọc được**, nói "theo advisory/bản tóm tắt". Nhóm **không chạy firmware**.

---

## SLIDE 7 — Demo: môi trường và bảo vệ đã đo *(mục 7 · ~1 phút)*

> Số thật: [../demo/ket_qua_demo.md](../demo/ket_qua_demo.md). Ảnh: `evidence/01_...` (khi lưu).

**Lên slide**
- **Challenge:** ROP Emporium **`split` (x86_64)** — bài huấn luyện công khai, dựng riêng để học ret2libc. **Không nhắm hệ thống thật.**
- **Môi trường:** Kali amd64 trên **UTM (VM cô lập, được phép)**; `uname -m` = `x86_64`; pwntools 4.15.0; gdb/checksec/ROPgadget sẵn có.
- **Binary:** `sha256 = bf9af5…40f9`, ELF 64-bit, dynamically linked, **không stripped**.
- **`checksec` — đọc từng cờ:**
  - **NX enabled** → stack không chạy mã (giống Tenda → phải ret2libc).
  - **No PIE (0x400000)** → code chương trình ở **địa chỉ cố định** → `system@plt` biết trước.
  - **No canary** → không có lính canh phát hiện ghi đè → tràn chạm thẳng địa chỉ trở về.
  - **Partial RELRO**.
- **`randomize_va_space = 2`** → **ASLR của máy vẫn BẬT** (không tắt) → đây là lý do ta đi đường **ret2plt** (địa chỉ cố định của chương trình), không dò libc.

**Lời giảng**
> "Demo chạy trong **VM Kali cô lập** — môi trường huấn luyện được phép, đúng quy định an toàn của nhóm. `split` của ROP Emporium là bài công khai dựng để học ret2libc, **không nhắm hệ thống thật**.
>
> Đọc `checksec` để biết mình đối mặt gì: **NX bật** (giống Tenda — phải ret2libc, không nhét shellcode). **No canary** — không có lính canh, tràn chạm thẳng địa chỉ trở về. **No PIE** — code chương trình ở địa chỉ **cố định** `0x400000`, nhờ vậy `system@plt` có địa chỉ biết trước. Và quan trọng: **ASLR máy vẫn bật** (`=2`), tôi **không** tắt. Đó là lý do chọn **ret2plt** — mượn địa chỉ cố định của *chương trình* — thay vì dò libc."

**Vì sao nêu từng cờ:** để slide 11 và 13 nói được **lớp nào chặn bước nào** — mấu chốt của mục 9.

---

## SLIDE 8 — Lỗi, buffer, và đo offset *(mục 4 cho demo · ~2 phút)*

**Lên slide**
- **Hàm nhận input:** `pwnme` (xác nhận bằng objdump/GDB).
- **Offset tới địa chỉ trở về = 40** — **đo**, không đoán.
- **Cách đo (cyclic):**
  1. gửi chuỗi `cyclic(200)` (các đoạn 4 ký tự duy nhất `aaaabaaac…`) → chương trình crash;
  2. đọc `RIP` lúc crash = `0x6161616c6161616b` = chuỗi `"kaaalaaa"`;
  3. `cyclic_find("kaaa") = 40` → **offset = 40** (40 byte đệm rồi tới địa chỉ trở về).
- **Bẫy off-by-8 (đáng dạy):** đọc tại `RSP` ra **48**, vì `ret` đã pop 8 byte; lấy giá trị ở `RIP` mới đúng, hoặc nhớ **48 − 8 = 40**.
- **Kết luận:** offset 40 ≠ kích thước buffer → minh chứng "phải đo trên binary".

**Lời giảng**
> "Nhớ slide 2 tôi nói *kích thước buffer không cho ra offset*? Đây là bằng chứng — ta không đoán, ta **đo**.
>
> Kỹ thuật **cyclic**: gửi chuỗi không lặp kiểu `aaaabaaacaaad…`, mỗi 4 ký tự là duy nhất. Chương trình crash vì `ret` nhảy vào rác. Nhìn `RIP` lúc crash — nó chứa đúng 4 ký tự đã rơi vào ô địa chỉ trở về: `"kaaa"`. Tra ngược, `"kaaa"` ở vị trí thứ **40**. Vậy **offset = 40**: 40 byte đệm rồi tới địa chỉ trở về.
>
> Một bẫy đáng dạy: nếu đọc giá trị tại `RSP` sau crash, ra **48** chứ không phải 40 — vì `ret` đã *pop* 8 byte, `RSP` trượt lên 8. Lấy giá trị ở `RIP` mới đúng, hoặc nhớ trừ 8. Tôi vấp đúng chỗ này khi làm demo, nên ghi lại để các bạn khỏi vấp. Và để ý: 40 chẳng liên quan gì tới con số 'đẹp' — buffer + padding + saved RBP đẩy nó lệch trực giác. **Luôn phải đo.**"

---

## SLIDE 9 — Chuỗi khai thác và truyền đối số *(mục 5 · ~2 phút)*

**Lên slide** — bảng payload (địa chỉ **thật**, đo trên `split`):

| Thứ tự trên stack | Thành phần | Địa chỉ | Vai trò |
|---|---|---|---|
| 1 | `b"A" * 40` | — | đệm lấp tới địa chỉ trở về (offset đã đo) |
| 2 | `ret` (căn lề) | `0x40053e` | đẩy `RSP` về bội số 16 cho lệnh `movaps` trong `system` |
| 3 | `pop rdi ; ret` | `0x4007c3` | bơm 8 byte kế trên stack vào `RDI` |
| 4 | con trỏ `"/bin/cat flag.txt"` (`usefulString`) | `0x601060` | giá trị cho `RDI` = đối số của `system` (chuỗi có sẵn trong `.data`) |
| 5 | `system@plt` | `0x400560` | gọi `system(RDI)` |

- **Sơ đồ stack sau tràn:** `[40 byte 'A'][ret][pop rdi;ret][0x601060][system@plt]`
- **Toàn bộ payload là dữ liệu (địa chỉ + đệm) — NX không bị vi phạm.**

**Lời giảng**
> "Giờ ráp mọi thứ — slide 4 (ABI) biến thành hành động. **40 byte 'A'** lấp đệm tới đúng ô địa chỉ trở về. Từ đây mỗi 8 byte là một *bước kịch bản*.
>
> Ô đầu lẽ ra là `pop rdi`, nhưng tôi chèn một **`ret` trơn** (`0x40053e`) trước. Vì sao? `system` của glibc đời mới dùng lệnh `movaps` đòi stack **căn lề 16 byte**; lệch là crash ngay trong libc. Một `ret` thừa đẩy `RSP` về đúng bội số 16. Đây là lỗi 'khó chịu' kinh điển của ret2libc trên glibc mới — đáng nói để lớp gặp thì biết đường xử.
>
> Tiếp theo **`pop rdi ; ret`** (`0x4007c3`): pop 8 byte kế — chính là **`0x601060`**, địa chỉ chuỗi `"/bin/cat flag.txt"` **có sẵn trong `.data`** (symbol `usefulString`). Ta *dùng lại dữ liệu có sẵn*, song hành với *dùng lại mã có sẵn*. Giờ `RDI` trỏ đúng chuỗi lệnh.
>
> Cuối cùng nhảy **`system@plt`** (`0x400560`). `system` đọc `RDI`, chạy `"/bin/cat flag.txt"`, in flag. **Cả payload là dữ liệu — NX hoàn toàn không bị động tới.**"

**Chốt liên hệ:** so với Tenda — thay `RDI` bằng `r0`, thay `pop rdi` bằng gadget nạp `r0`, phần còn lại **giống hệt**. *"Cùng một kịch bản, đổi diễn viên."*

---

## SLIDE 10 — Chạy demo và quan sát bằng debugger *(mục 7 · ~4 phút)*

> Bằng chứng: [../demo/ket_qua_demo.md](../demo/ket_qua_demo.md); ảnh `evidence/05`, `evidence/06`.

**Lên slide**
- **Kết quả chạy:** exploit → in flag **`ROPE{a_placeholder_32byte_flag!}`**.
- **Quan sát trong GDB** (đặt breakpoint tại `system`):
  - dừng tại `system`; `RDI = 0x601060`; `x/s $rdi` → `"/bin/cat flag.txt"` → **đối số 1 trỏ đúng chuỗi** (không phải "crash may mà ra flag").
  - `RSP` tận cùng `…8` → thỏa `RSP % 16 == 8` ở cửa vào hàm → `ret` căn lề đã đúng, `movaps` không fault.
- **Trạng thái trung thực:** ra flag **1 lần** + quan sát GDB; **lần 2 ngoài GDB: `[CHƯA CHẠY]`** (đề yêu cầu 2 lần liên tiếp → sẽ chạy nốt + lưu log trước buổi).
- **Ranh giới:** địa chỉ libc `0x7ffff7e0…` thấy trong GDB **chỉ** vì GDB tắt ASLR trong lab; exploit **không** dùng nó → đây là **ret2plt**, **chưa** vượt ASLR libc.

**Lời giảng**
> "Chạy thật: flag `ROPE{...}` hiện ra. Nhưng *ra flag* chưa đủ để nói *hiểu vì sao* — nên tôi mở GDB, đặt breakpoint ngay tại `system` và soi.
>
> Tại điểm dừng: `RDI = 0x601060`, lệnh `x/s $rdi` in `"/bin/cat flag.txt"`. Đây là bằng chứng **tận mắt**: tôi không chỉ làm nó crash rồi may mắn; tôi **đưa đúng đối số vào đúng thanh ghi tại đúng hàm**. `RSP` tận cùng số 8 — đúng `RSP % 16 == 8` ABI đòi ở cửa vào hàm — xác nhận cái `ret` căn lề ở slide 9 có tác dụng thật.
>
> **Tôi phải trung thực hai điều:** (1) địa chỉ libc `0x7ffff7e0…` tôi thấy trong GDB *chỉ* vì GDB tắt ASLR trong lab — exploit của tôi *không* dùng nó, nó chỉ dùng `system@plt = 0x400560` cố định. Nên đây là **ret2plt**, **chưa** vượt ASLR của libc. (2) Tôi mới ra flag **một lần**; đề yêu cầu **hai lần liên tiếp** — tôi sẽ chạy nốt lần hai ngoài GDB và lưu log trước buổi."

**Nếu VM chậm:** dự phòng bằng ảnh `evidence/` + log; dừng demo trực tiếp, giảng theo bằng chứng đã lưu.

---

## SLIDE 11 — Đối chiếu bằng chứng: PLT vs direct libc *(mục 9 · ~1 phút)*

**Lên slide** — thang 5 mức bằng chứng, đánh dấu demo đạt tới đâu:

| Mức | Demo `split` | Căn cứ |
|---|---|---|
| Ghi vượt / crash | ✅ | cyclic → SIGSEGV |
| Chiếm luồng (RIP = giá trị ta đặt) | ✅ | offset 40, kiểm soát được RIP |
| Gọi đúng hàm, đối số đúng | ✅ | GDB: `RDI → "/bin/cat flag.txt"` tại `system` |
| Đạt mục tiêu CTF | ✅ | in ra flag |
| **Vượt ASLR của libc** | ❌ **chưa** | dùng `system@plt` cố định (No PIE), không tính libc base |

- **ret2plt (đã làm):** mượn `system@plt` của chương trình, địa chỉ cố định nhờ No PIE → không cần biết libc nằm đâu.
- **direct ret2libc (chưa làm, nhánh mở rộng):** phải *leak* một địa chỉ libc rồi tính base, vì ASLR xáo trộn mỗi lần chạy.

**Lời giảng**
> "Slide này để *nói đúng mức mình đã làm* — thứ dễ bị thổi phồng nhất. Ta chứng minh được: ghi vượt, chiếm luồng, **gọi đúng hàm với đối số đúng** (có ảnh GDB), và đạt mục tiêu. Ta **chưa** chứng minh vượt ASLR của libc — vì đi đường ret2plt, mượn địa chỉ cố định của *chương trình* (nhờ No PIE), không hề tính địa chỉ libc.
>
> direct ret2libc — nhảy thẳng vào `system` trong libc — sẽ phải *leak* một địa chỉ libc rồi tính base, vì ASLR xáo trộn nó mỗi lần. Đó là nhánh mở rộng, nhóm chưa làm. Nói rõ ranh giới này là điểm cộng: nó cho thấy nhóm hiểu *chính xác* mình đã đạt gì."

---

## SLIDE 12 — Khắc phục, phòng ngừa, các lớp bảo vệ *(mục 8 · ~2 phút)*

> Nền: Phần A5 (NX làm được/không làm được gì).

**Lên slide**
- **Sửa gốc (quan trọng nhất) — giới hạn độ dài khi chép:**
  ```c
  // lpr 1996 — bản vá THẬT của FreeBSD: thêm đúng một điều kiện
  while ((c = *p2++) != '\0' && len < sizeof(buf)) { ... }
  // show_name — đặt guard TRƯỚC sink:
  if (strlen(input) >= sizeof(buf)) return -1;
  // sscanf — dùng giới hạn trường:
  sscanf(p, "%255[^;]", buf);
  ```
- **Bảng các lớp bảo vệ — mỗi lớp chặn MỘT bước, không lớp nào đủ một mình:**

  | Cơ chế | Chặn bước nào | Giới hạn |
  |---|---|---|
  | **Kiểm tra biên ở mã nguồn** | chặn **ghi tràn tại gốc** | phải sửa đúng *mọi* sink |
  | **Stack canary** | phát hiện ghi đè qua địa chỉ trở về (dừng chương trình) | không ngăn tràn; tùy hàm được bảo vệ |
  | **NX/DEP** | chặn chạy mã **trên stack** | **không** chặn ret2libc/ROP (cả bài đã chứng minh) |
  | **ASLR + PIE** | làm khó đoán địa chỉ (libc **và** chương trình) | No PIE → code cố định; phải bật **cả hai** |
  | **Full RELRO** | khóa GOT chống ghi đè | không cấm gọi qua PLT |
- **Thông điệp:** phòng thủ **theo lớp**; không lớp nào thay được việc **sửa lỗi gốc**.

**Lời giảng**
> "Thứ tự ưu tiên: **sửa lỗi gốc trước**, bảo vệ nền tảng sau. Nhìn bản vá `lpr` của FreeBSD — thêm **đúng một điều kiện** `&& len < sizeof(buf)`; vòng lặp giờ hỏi cả *'đích còn chỗ không?'*. Với `sscanf` của Tenda, tương đương là giới hạn trường `%255[^;]`. Với `show_name`, đặt guard `strlen >= sizeof(buf)` *trước* `strcpy`. Rẻ, dứt điểm.
>
> Các lớp nền tảng mỗi lớp chỉ bịt **một bước**: **canary** phát hiện ghi đè nhưng không ngăn tràn; **NX** chặn shellcode stack nhưng — như cả bài đã thấy — **không** chặn ret2libc; **ASLR+PIE** làm khó đoán địa chỉ, nhưng quên bật PIE thì code chương trình cố định (đúng kẽ hở `split` và Tenda khai thác); **RELRO** khóa GOT nhưng không cấm gọi qua PLT.
>
> Bài học mục 8: **phòng thủ theo lớp.** Tenda *có* NX mà vẫn RCE vì thiếu các lớp kia **và** vì lỗi gốc chưa sửa. Không lớp nào thay được việc viết code chặn tràn từ đầu."

---

## SLIDE 13 — Điều kiện, giới hạn, và kết luận *(mục 9 + 10 · ~2 phút)*

**Lên slide**
- **Điều kiện để ret2libc thành công (phải đủ TẤT CẢ):**
  1. có lỗi ghi tràn tới dữ liệu điều khiển (địa chỉ trở về);
  2. biết/đoán được địa chỉ hàm đích (hoặc entry PLT cố định);
  3. đặt được đối số đúng chỗ ABI (RDI/r0/stack) — thường cần gadget;
  4. căn lề stack đúng (vd `movaps`);
  5. đường "trở về" sau khi hàm xong hợp lệ;
  6. vượt được canary/ASLR nếu chúng bật.
  → Đứt **một** mắt là hỏng. Demo đúng trong *cấu hình đã đo*, không tự suy ra cho cấu hình khác.
- **Ba kết luận:**
  1. **Lỗi và kỹ thuật là hai lớp tách biệt:** CWE-121 là *lỗi*; ret2libc là *cách khai thác*. Phân biệt rạch ròi mới nói đúng.
  2. **NX hữu ích nhưng không đủ:** nó dời khai thác từ "chạy mã mới" sang "dùng lại mã cũ". Cần phối hợp canary + ASLR/PIE + RELRO, và **sửa lỗi gốc**.
  3. **Lỗi kinh điển không chết:** cùng CWE-121 + ret2libc kéo từ 1996 (cục bộ) → 2018 (từ xa, 9.8). Mọi `strcpy`/`sscanf('%[^;]')`/vòng chép không đo độ dài hôm nay vẫn là CVE ngày mai.

**Lời giảng**
> "Nhấn mạnh mục 9: demo chạy được **không** nghĩa 'khai thác được mọi nơi'. Nó đúng trong *cấu hình đã đo*: No PIE, No canary, offset 40 này, binary này. Đổi sang có canary, bật PIE, hay kiến trúc khác — payload phải làm lại từ đầu. Khai thác là chuỗi điều kiện, đứt một mắt là hỏng.
>
> Ba điều mang về: **Một**, tách lỗi khỏi kỹ thuật — đừng gọi ret2libc là CWE. **Hai**, NX không phải viên đạn bạc; nó chỉ đổi luật chơi, ret2libc là nước đi trong luật mới. **Ba**, lỗi 'chép không đo độ dài' sống dai 22 năm vì dễ viết và khó thấy — bạn viết `strcpy`, `sscanf('%[^;]')`, hay vòng `while` chép tới `\0` mà quên kiểm biên, là vừa viết lại CVE-1999-0032.
>
> Và câu mở đầu, giờ đã có bằng chứng: *một lớp lỗi, một kỹ thuật, 22 năm* — ta vừa thấy ở `lpr`, ở Tenda, và tự tay dựng lại trên `split`."

---

## SLIDE 14 — Nguồn tham khảo và hỏi đáp *(~2 phút)*

**Lên slide**
- **CWE:** [CWE-121](https://cwe.mitre.org/data/definitions/121.html) (stack buffer overflow), [CWE-787](https://cwe.mitre.org/data/definitions/787.html) (out-of-bounds write).
- **CVE:** [NVD CVE-1999-0032](https://nvd.nist.gov/vuln/detail/CVE-1999-0032); [NVD CVE-2018-5767](https://nvd.nist.gov/vuln/detail/CVE-2018-5767); Solar Designer, Bugtraq 1997 ("return-into-libc").
- **Lý thuyết nền:** Aleph One, "Smashing the Stack for Fun and Profit" (1996); [ROP Emporium](https://ropemporium.com/guide.html).
- **Challenge demo:** [ROP Emporium `split`](https://ropemporium.com/challenge/split.html).
- **ABI:** [System V AMD64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI).
- *Tra cứu 2026-11-02; CVE chỉ nghiên cứu, không tái hiện.*

**Câu hỏi phản biện — thủ sẵn** (chi tiết trong hai ghi chú CVE, mục "Câu hỏi phản biện"):

| Câu hỏi | Trả lời ngắn |
|---|---|
| Có NX sao vẫn thủng? | NX chỉ chặn chạy mã **trên stack**; `system`/gadget nằm ở vùng được phép chạy (libc/`.text`) |
| Demo đã vượt ASLR chưa? | Chưa. Đây là **ret2plt** dùng địa chỉ cố định (No PIE), không tính libc base |
| Demo x86_64 mà CVE ARM, có khập khiễng? | Không — cùng cơ chế "gadget đặt đối số vào thanh ghi rồi gọi hàm libc"; chỉ khác thanh ghi `RDI`/`r0` |
| Vì sao offset 40 chứ không 16? | Buffer + padding + saved RBP; **phải đo**, kích thước buffer không cho offset |
| Shellcode với ret2libc khác gì? | Shellcode = mang mã mới lên stack (NX giết); ret2libc = dùng lại mã có sẵn trong libc (NX không cản) |
| Nhóm có chạy CVE không? | Không. Chỉ nghiên cứu; demo là challenge `split` riêng, trong VM cô lập |
| ret2libc là CWE gì? | Không phải CWE. Lỗi nền là CWE-121; ret2libc là kỹ thuật khai thác |

---

## Bản rút gọn 20 phút (nếu bị cắt giờ)

Giữ đủ 10 mục, bỏ phần mở rộng:
- **Nền (4'):** gộp slide 2+3+4 — tràn buffer + CWE, rồi "chèn mã trên stack → NX → ret2libc", rồi ABI/gadget, một mạch. (Lấy ý chính từ Phần A3→A7.)
- **CVE (3'):** slide 5 (1 phút) + slide 6 (2 phút).
- **Phân tích + demo (8'):** slide 7→8→9→10, ưu tiên slide 9 (payload) và 10 (ra flag + GDB).
- **Sửa lỗi + kết luận (3'):** gộp slide 12+13.
- **Hỏi đáp (2').**
- Bỏ: slide 11 — nói ghép vào slide 10 (một câu ranh giới ret2plt).

Nếu có đủ 26 phút, có thể **tách Phần A thành thêm 1 slide** riêng cho "chèn mã trên stack → NX" (slide 3 hiện đã gánh việc này) để người nghe mới hoàn toàn theo kịp.

## Việc cần làm trước buổi (để mọi phát biểu có bằng chứng)

- [ ] **Chạy demo lần 2 ngoài GDB**, lưu `run_log.txt` + `evidence/06` → mới được nói "hai lần liên tiếp".
- [ ] Lưu ảnh `evidence/01` (checksec/môi trường) và `evidence/05` (GDB: `RDI → chuỗi`) kèm chú thích trong `evidence/README.md`.
- [ ] Chốt ngày seminar + tên A/B/C; điền vào slide 1.
- [ ] Review chéo: một thành viên khác nghe thử phần nền + CVE + demo, bắt lỗi phát biểu quá mức.
- [ ] (Tùy chọn) tìm lại writeup gốc Fidus để bổ sung dẫn mã CVE-2018-5767; nếu không có, giữ nguyên "theo advisory".
