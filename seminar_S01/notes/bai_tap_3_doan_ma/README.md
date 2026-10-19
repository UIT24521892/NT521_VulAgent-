# Bài tập chung đầu tiên — 3 đoạn mã C (source–sink–guard)

Theo [PLAN.md mục 2](../../PLAN.md#2-học-nền-theo-thứ-tự). Mục tiêu: luyện cách phân tích **source → sink → kích thước buffer → điều kiện lỗi → guard → kết luận** trước khi áp vào binary ret2win thật. Đây là nền cho slide mục 1–5.

## Ba đoạn mã

| File | Vai trò | Ý chính |
|---|---|---|
| [01_co_loi.c](01_co_loi.c) | Có lỗi | `strcpy(buf, argv[1])` không giới hạn độ dài |
| [02_da_sua.c](02_da_sua.c) | Bản sửa của 01 | `snprintf(buf, sizeof(buf), ...)` giới hạn ghi + luôn `\0` |
| [03_co_guard.c](03_co_guard.c) | Trông nguy hiểm, có guard | vẫn dùng `strcpy` nhưng kiểm tra `strlen(input) < sizeof(buf)` trước |

## Cách làm (quy trình nhóm)

1. **Mỗi người tự điền bảng phân tích bên dưới cho cả 3 đoạn**, chưa nhìn phần "đáp án tham khảo".
2. Cả nhóm **phản biện chéo**: so câu trả lời, tranh luận chỗ khác nhau, nhất là đoạn 03 (guard có thật sự chặn mọi đường tới sink không).
3. Sau khi thống nhất, đối chiếu với phần "Phân tích tham khảo".
4. (Khi có VM) biên dịch và chạy thử để **xác nhận bằng quan sát thật**, không chỉ suy luận — xem mục "Kiểm chứng trong VM".

## Bảng phân tích (mỗi người tự điền)

Chép bảng này ra, điền cho từng đoạn 01 / 02 / 03:

| Mục | Trả lời |
|---|---|
| Source (dữ liệu vào từ đâu) | |
| Sink (phép ghi nhạy cảm nào) | |
| Kích thước buffer đích | |
| Điều kiện để lỗi xảy ra | |
| Có guard không? Guard kiểm tra gì? | |
| Guard có chặn **mọi** đường tới sink không? | |
| Kết luận (an toàn / tràn / mức hậu quả) | |

---

## Phân tích tham khảo

> Đọc **sau** khi đã tự điền. Đây là mức suy luận tĩnh (đọc mã); phần "crash/điều khiển luồng" phải kiểm chứng khi chạy thật.

### 01_co_loi.c — CÓ LỖI

| Mục | Trả lời |
|---|---|
| Source | `argv[1]` — chuỗi do người dùng truyền, kiểm soát hoàn toàn độ dài và nội dung |
| Sink | `strcpy(buf, input)` — sao chép tới khi gặp `\0` của `input`, không nhìn `sizeof(buf)` |
| Kích thước buffer | `char buf[64]` trên stack |
| Điều kiện lỗi | `strlen(argv[1]) >= 64` (vì cần thêm 1 byte `\0`): bắt đầu ghi vượt cuối `buf` |
| Guard | Không có |
| Chặn mọi đường? | Không có gì chặn |
| Kết luận | Ghi vượt buffer trên stack → đè các byte ở địa chỉ cao hơn (biến cục bộ khác, `rbp` đã lưu, rồi **địa chỉ trả về**). Đúng bản chất **CWE-121**. Input đủ dài và đúng chỗ có thể đổi luồng thực thi; input dài "lung tung" thường chỉ gây **crash**. Hai mức này khác nhau, phải kiểm chứng khi chạy |

### 02_da_sua.c — BẢN SỬA

| Mục | Trả lời |
|---|---|
| Source | `argv[1]` (như trên) |
| Sink | `snprintf(buf, sizeof(buf), "%s", input)` |
| Kích thước buffer | `char buf[64]` |
| Điều kiện lỗi | Không có đường gây tràn: `snprintf` ghi tối đa `sizeof(buf)-1` ký tự rồi thêm `\0` |
| Guard | Giới hạn nằm ngay trong lời gọi `snprintf` (tham số `sizeof(buf)`) |
| Chặn mọi đường? | Có, với điều kiện truyền đúng `sizeof(buf)` (không hard-code số 64 lệch) |
| Kết luận | **An toàn** khỏi tràn. Đánh đổi: input dài bị **cắt ngắn** (mất dữ liệu) — đó là hành vi đúng, không phải lỗi bộ nhớ. Nhắc: `strncpy` KHÔNG tương đương vì có thể **không** kết thúc `\0`; `snprintf` an toàn hơn |

### 03_co_guard.c — CÓ GUARD

| Mục | Trả lời |
|---|---|
| Source | `argv[1]` |
| Sink | `strcpy(buf, input)` — bản thân vẫn nguy hiểm |
| Kích thước buffer | `char buf[64]` |
| Điều kiện lỗi | Chỉ xảy ra nếu guard sai |
| Guard | `if (strlen(input) < sizeof(buf))` — cho phép tối đa 63 ký tự + `\0` = 64 byte, vừa khít |
| Chặn mọi đường? | Có — mọi đường tới `strcpy` đều qua `if` này; nhánh `else` từ chối input dài |
| Kết luận | **An toàn** nhờ guard đúng. **Bẫy quan trọng:** đổi `<` thành `<=` sẽ cho 64 ký tự + `\0` = 65 byte → **tràn 1 byte (off-by-one)**. Guard lệch một ký tự là lỗi quay lại. Bài học: guard "có tồn tại" chưa đủ, phải **đúng biên** và **chặn mọi đường** |

## Liên hệ sang ret2win và CVE

- Đoạn 01 là phiên bản tối giản của lỗi trong challenge ret2win: input dài hơn buffer → đè địa chỉ trả về. Khác biệt: ret2win đọc bằng `read()`/`gets()` và mục tiêu là nhảy tới một hàm có sẵn; offset phải **đo trên binary thật** bằng GDB, không suy từ `buf[64]` ở đây.
- [CVE-2015-7547](../../cve/CVE-2015-7547.md) cùng họ (ghi vượt buffer trên stack) nhưng nguyên nhân là **sai đồng bộ con trỏ/kích thước** chứ không phải `strcpy` đơn giản — phức tạp hơn ba đoạn này.

## Kiểm chứng trong VM (khi Kali x86_64 sẵn sàng)

```bash
# Đoạn 01: tat bao ve de thay ro loi
gcc -fno-stack-protector -no-pie -g -o 01_co_loi 01_co_loi.c
./01_co_loi AAAA                                   # binh thuong
./01_co_loi $(python3 -c 'print("A"*200)')         # quan sat crash (segfault?)

# Doan 02 va 03: bien dich binh thuong
gcc -g -o 02_da_sua 02_da_sua.c
gcc -g -o 03_co_guard 03_co_guard.c
./02_da_sua $(python3 -c 'print("A"*200)')         # bi cat ngan, khong crash
./03_co_guard $(python3 -c 'print("A"*200)')       # bi tu choi
```

**Ghi lại đúng mức bằng chứng:** "chạy input dài rồi thấy `Segmentation fault`" chỉ chứng minh **crash**, chưa chứng minh điều khiển được luồng. Muốn nói mạnh hơn phải xem trong GDB (địa chỉ trả về bị đè bằng giá trị mình chọn) — để phần demo ret2win.
