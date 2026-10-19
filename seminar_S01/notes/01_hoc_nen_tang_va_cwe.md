# Học: kiến thức nền tảng và CWE (mục 1–3 của đề, ~5–6 phút)

Cách đọc: mỗi phần có **Hiểu gì**, **Tự kiểm tra** và mức tin cậy của thông tin.
- `[N]` = đã đọc từ nguồn chính thức (ghi nguồn), ngày 2026-10-05.
- `[KT]` = kiến thức nền chung của sách giáo khoa, **chưa tra lại**; kiểm tra trước khi đưa lên slide.

Thứ tự học đề nghị: 1 → 2 → 3 → 4 → 5 → làm phần tự kiểm tra cuối file.

---

## 1. Stack và stack frame (mục 1 của đề)

**Hiểu gì** `[KT]`
- Mỗi lần gọi hàm, chương trình tạo một **stack frame** trên stack chứa: tham số (tùy quy ước gọi), **địa chỉ trả về** (nơi chạy tiếp khi hàm kết thúc), (thường) giá trị `rbp` cũ đã lưu, và **biến cục bộ**, trong đó có các mảng như `char buf[64]`.
- Stack trên x86 **mọc về địa chỉ thấp**, còn khi ghi vào mảng thì dữ liệu đi về **địa chỉ cao**. Nên ghi quá cuối `buf` sẽ đè lên những thứ nằm ở địa chỉ cao hơn: các biến cục bộ khác, `rbp` đã lưu, rồi **địa chỉ trả về**.
- Sơ đồ **minh họa** x86_64 (địa chỉ cao ở trên):

```
địa chỉ cao   ┌────────────────────┐
              │ ...frame của caller │
              ├────────────────────┤
              │ địa chỉ trả về     │  ← mục tiêu kẻ tấn công muốn đè
              ├────────────────────┤
              │ rbp đã lưu         │
              ├────────────────────┤
              │ buf[63] ... buf[0] │  ← ghi bắt đầu từ buf[0], đi lên
địa chỉ thấp  └────────────────────┘
```

> Đây chỉ là sơ đồ minh họa. Khoảng cách thực tế từ `buf` đến địa chỉ trả về (offset) phụ thuộc compiler, cờ biên dịch, kiến trúc và phải **đo trên binary thật**. Trang ROP Emporium nêu ret2win x86_64 khoảng 40 byte `[N: ropemporium.com/challenge/ret2win.html]` nhưng con số của nhóm phải tự đo bằng gdb.

**Tự kiểm tra:** Vì sao ghi quá cuối `buf` lại chạm địa chỉ trả về chứ không chạm biến của hàm khác ở dưới? Vì sao `char buf[8]` chứa được chuỗi "12345678" nhưng vẫn lỗi (gợi ý `\0`)?

## 2. Nguyên lý, điều kiện và dạng phổ biến (mục 2 của đề)

**Hiểu gì**
- **Nguyên lý** `[N: CWE-121]`: buffer bị ghi tràn nằm trên stack, tức là biến cục bộ (hiếm khi là tham số hàm). Mục tiêu hay gặp nhất là địa chỉ trả về đã lưu. Ngoài ra còn con trỏ stack/frame, có thể tạo điều kiện ghi tùy ý.
- **Điều kiện cần có** `[KT]`: (a) có đường dữ liệu từ input không tin cậy tới thao tác ghi; (b) thao tác ghi không bị giới hạn bởi kích thước đích; (c) buffer nằm trên stack. Thiếu một điều kiện thì lỗi không xảy ra.
- **Các dạng phổ biến** `[KT]`:
  - Sao chép không kiểm tra độ dài: `strcpy`, `strcat`, `sprintf`, `gets`, `scanf("%s")`.
  - Độ dài đọc/ghi lớn hơn buffer: `read(fd, buf, n)` với `n > sizeof(buf)`. Đây là dạng của challenge kiểu ret2win (trang challenge nêu input bị cắt ngắn và có `read()` `[N]`).
  - **Off-by-one**: ghi dư đúng 1 byte, thường do quên `\0` kết thúc hay dùng `<=` thay cho `<`.
  - Tính sai độ dài: trộn số có dấu/không dấu, tràn số nguyên khi tính kích thước.
- **Ví dụ trong chính mô tả CWE** `[N: CWE-121]`:
  ```c
  char buf[256];
  strcpy(buf, argv[1]);   // không kiểm tra độ dài
  ```
  ```c
  char hostname[64];
  strcpy(hostname, hp->h_name);  // chuỗi dài quá 64 byte sẽ ghi đè stack
  ```
- **Phân biệt mức hậu quả** `[N: CWE-121 mục Consequences]`: crash/từ chối dịch vụ; hoặc thực thi mã tùy ý/ghi bộ nhớ. "Crash" **không** chứng minh điều khiển được luồng thực thi: đây là điều phải nói rõ ở S01.

**Tự kiểm tra:** Chỉ ra source, sink, guard trong `strcpy(buf, argv[1])`. Nếu thêm `if (strlen(argv[1]) < 256)` thì lỗi còn không? (Gợi ý: `<256` với `buf[256]` còn thiếu chỗ cho `\0` không?)

## 3. CWE-121 và liên hệ với chủ đề (mục 3 của đề)

**Thông tin chính thức** `[N: cwe.mitre.org/data/definitions/121.html, 787.html]`
- **CWE-121: Stack-based Buffer Overflow**. Mô tả: "A stack-based buffer overflow condition is a condition where the buffer being overwritten is allocated on the stack (i.e., is a local variable or, rarely, a parameter to a function)."
- **CWE-787: Out-of-bounds Write**: "The product writes data past the end, or before the beginning, of the intended buffer."
- **Quan hệ:** CWE-121 là con của CWE-787 (và CWE-788). CWE-787 là con của CWE-119. CWE-125 (đọc ngoài biên) là mục ngang hàng với 787. Theo trang CWE-787 thì CWE-120 "Classic Buffer Overflow" cũng là con của 787.

```
CWE-119  (phạm vi rộng: thao tác vượt biên buffer)
  └─ CWE-787 Out-of-bounds Write
        ├─ CWE-120 Classic Buffer Overflow
        └─ CWE-121 Stack-based Buffer Overflow   ← chủ đề S01
```

> Lưu ý: bản tóm tắt tự động của trang CWE-121 có nhắc một mối quan hệ với CWE-120 mà mình cho là không đáng tin. Hãy mở trang MITRE và đọc mục *Relationships* trực tiếp trước khi vẽ sơ đồ này lên slide.

- **Liên hệ với chủ đề được phân công:** S01 = *stack-based buffer overflow* chính là CWE-121. Dùng CWE-787 như danh mục cha để giải thích "ghi ngoài biên" tổng quát, rồi thu hẹp xuống 121 vì buffer nằm trên stack.
- **CWE ≠ CVE** `[KT]`: CWE là *loại* yếu điểm (ví dụ CWE-121). CVE là *một lỗ hổng cụ thể* trong một sản phẩm cụ thể (ví dụ CVE-2015-7547 trong glibc). Một CVE được gán một hay nhiều CWE.
- **Ví dụ thật về việc gán CWE không luôn ở mức cụ thể nhất** `[N: NVD API CVE-2015-7547, 2026-10-11]`: CVE-2015-7547 có bản chất kỹ thuật là tràn bộ đệm **trên stack** (đúng CWE-121), nhưng NVD dán nhãn ở mức cha **CWE-119**. Bài học cho slide: khi trích CWE của một CVE, nói đúng NVD gán gì (ở đây là 119), rồi mới phân tích thêm bản chất là 121 — đừng tự sửa nhãn NVD thành 121. Xem [../cve/CVE-2015-7547.md](../cve/CVE-2015-7547.md).

**Tự kiểm tra:** Một chương trình ghi tràn buffer trên **heap**: thuộc CWE-121 không? Thuộc CWE-787 không? Vì sao?

## 4. Cơ chế bảo vệ (nền cho mục 8 và 9)

`[N: CWE-121 mục Mitigations]` nêu: stack canary, kiểm tra biên, thay hàm nguy hiểm như `gets()`, ASLR, PIE, và phát hiện bằng fuzzing/SAST/AddressSanitizer. Cách mỗi cơ chế hoạt động và giới hạn của nó (dưới đây là `[KT]`, kiểm tra trên binary khi demo):

| Cơ chế | Tác dụng | Giới hạn |
|---|---|---|
| Stack canary | Giá trị đặt trước địa chỉ trả về, kiểm tra khi hàm kết thúc; phát hiện ghi tràn liên tục | Không chặn ghi tới biến cục bộ nằm trước canary; có thể bị lộ giá trị |
| NX (DEP) | Vùng stack không thực thi được | Không chặn đổi luồng sang mã có sẵn (return-to-function, ROP) |
| ASLR | Ngẫu nhiên hóa địa chỉ stack/heap/thư viện | Có thể bị lộ địa chỉ qua lỗi khác |
| PIE | Ngẫu nhiên hóa cả địa chỉ chương trình chính | Cần ASLR bật |

Điểm cần nhớ: **các cơ chế này giảm khả năng khai thác, không loại bỏ lỗi**. Sửa tận gốc = giới hạn ghi theo kích thước đích.

## 5. Tóm tắt thành lời nói 5–6 phút (khung)

| Phút | Nội dung | Slide |
|---|---|---|
| 0:00–1:30 | Stack frame, buffer, địa chỉ trả về; ví dụ input quá dài; bối cảnh nơi lỗi hay gặp (C/C++, dịch vụ mạng, thư viện) | 1 |
| 1:30–3:00 | Điều kiện + các dạng phổ biến; crash vs điều khiển luồng | 2 |
| 3:00–5:00 | CWE-121 → CWE-787 → CWE-119; CWE vs CVE; liên hệ chủ đề | 3 |
| 5:00–6:00 | Chuyển sang CVE, tóm tắt cơ chế bảo vệ để dùng ở mục 8 | — |

---

## Tự kiểm tra cuối (trả lời không nhìn tài liệu)

1. Vẽ stack frame của một hàm có `char buf[16]` và chỉ ra chỗ địa chỉ trả về.
2. Nêu 3 dạng gây lỗi ghi tràn buffer stack, mỗi dạng một ví dụ code.
3. Phát biểu CWE-121 bằng lời của bạn trong một câu; nói nó là con của CWE nào.
4. Crash khác gì "đã điều khiển được địa chỉ trả về"?
5. Canary, NX, ASLR, PIE: mỗi cái chặn bước nào và giới hạn là gì?
6. Vì sao không dùng sơ đồ minh họa để nói offset của binary?
