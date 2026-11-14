# Kiến thức cần học cho S05

Học theo thứ tự dưới đây. Mục tiêu là giải thích được luồng điều khiển và điều kiện tái sử dụng hàm thư viện, rồi đối chiếu với bằng chứng của binary S05. Kế hoạch thực hành ở [PLAN.md](PLAN.md).

**Trọng tâm S05 là kỹ thuật return-to-libc.** Phần tràn buffer và CWE bên dưới giúp phân tích lỗi tạo điều kiện đổi luồng trong một ca cụ thể. CWE được xác định theo lỗi đó; không dùng CWE-121 làm nhãn cho bản thân ret2libc.

**Cách học:** mỗi phần có nội dung cần hiểu, ví dụ hoặc sơ đồ, câu hỏi tự kiểm tra. Đọc mục 1 trước, sau đó học ABI ở mục 2, liên kết động ở mục 3 và bảo vệ ở mục 4. Bài tập và khung nói 5–6 phút ở mục 6.

**Cách đọc bằng chứng:** các đoạn C và sơ đồ dưới đây là **minh họa để học**, không phải mã nguồn hay kết quả chạy `split`. Nguồn kỹ thuật được đặt cạnh nội dung tương ứng; các nguồn bổ sung về C, ABI, CWE và GDB được đối chiếu ngày **2026-10-21**. Kiến trúc, offset, gadget, địa chỉ và bảo vệ của binary S05 vẫn **chưa đo**.

## 1. Nền tảng bắt buộc

| Chủ đề | Cần tự làm được | Dùng trong seminar |
|---|---|---|
| C, mảng, con trỏ và độ dài | Phân biệt dung lượng đích với số byte có thể ghi; theo dấu input đến sink và guard | Chỉ ra nguyên nhân ghi vượt trước khi bàn kỹ thuật khai thác |
| Stack, `call`, `ret` | Giải thích địa chỉ trở về trên stack, tác động của `ret` lên luồng thực thi và stack pointer | Sơ đồ luồng bình thường so với luồng bị thay đổi |
| Crash và quyền điều khiển | Phân biệt ghi vượt, crash, thay đổi địa chỉ trả về, gọi đúng hàm, đạt mục tiêu challenge | Kết luận đúng mức bằng chứng |
| CWE và kỹ thuật khai thác | Xác định CWE theo lỗi nền của ca phân tích; phân biệt với ret2libc/ROP là cách khai thác | Giải thích quan hệ giữa lỗi tạo điều kiện đổi luồng và kỹ thuật tái sử dụng mã |
| Debugger và disassembly | Xác nhận kiến trúc, hàm nhận input, vị trí ghi, offset, đích chuyển luồng và tham số | Thu bằng chứng mới cho `split`; mọi offset/gadget đều đo trên binary này |

Stack frame chỉ là sơ đồ minh họa cho đến khi được đối chiếu với compiler, binary và trạng thái runtime đang dùng. Không suy ra khả năng điều khiển từ một lần SIGSEGV.

### 1.1. C: mảng, con trỏ, dung lượng và chuỗi

**Hiểu gì**

`char buf[8]` tạo mảng gồm 8 phần tử `char`, chỉ số hợp lệ từ `buf[0]` đến `buf[7]`. Ghi `buf[8]` đã vượt biên dù chỉ dư một byte. C không tự kiểm tra biên cho mỗi lần truy cập mảng; ghi ngoài vùng hợp lệ là **undefined behavior**, nên không thể dự đoán chắc chương trình sẽ crash hay ghi đè đối tượng nào chỉ từ mã C.

Phải tách ba đại lượng:

| Đại lượng | Ý nghĩa | Ví dụ |
|---|---|---|
| Dung lượng vùng đệm | Số byte thực sự được cấp cho vùng đích | `sizeof(buf)` bằng 8 khi `buf` là mảng `char[8]` tại đó |
| Độ dài C string | Số byte trước byte kết thúc `\0`, không tính chính byte `\0` | `strlen("ABC")` bằng 3, nhưng cần 4 byte để lưu cả chuỗi |
| Số byte đọc/ghi thực tế | Lượng dữ liệu được xử lý trong một lần gọi | `read()` trả về số byte đã đọc, có thể ít hơn số yêu cầu |

Ví dụ với ký tự ASCII:

```c
char a[8] = "1234567";   // 7 ký tự + '\0': vừa đủ, là C string
char b[8] = {'1', '2', '3', '4', '5', '6', '7', '8'}; // 8 byte, không có '\0'
```

`b` chứa đủ 8 byte dữ liệu; không được coi nó là C string hợp lệ để gọi `strlen(b)` hoặc `puts(b)`. Những hàm đó có thể tiếp tục đọc ra ngoài mảng để tìm `\0`. Nếu dùng `strcpy` để chép chuỗi `"12345678"` vào một buffer 8 byte, hàm còn chép cả `\0`, tức cần 9 byte và gây ghi vượt. Xem [Linux man-pages — strlen(3)](https://man7.org/linux/man-pages/man3/strlen.3.html) và [strcpy(3)](https://man7.org/linux/man-pages/man3/strcpy.3.html).

**Con trỏ không mang sẵn dung lượng của vùng nhớ.** Với `char *p = a`, `sizeof(p)` đo kích thước con trỏ, không đo dung lượng của `a`. Tương tự, tham số `void f(char buf[8])` thực chất được điều chỉnh thành tham số con trỏ; `sizeof(buf)` bên trong `f` không còn cho kích thước mảng của caller. Hàm xử lý buffer cần nhận thêm dung lượng hoặc có một hợp đồng rõ ràng về vùng đích. Nguồn: [GNU C Language Manual — Type Size](https://www.gnu.org/software/c-intro-and-ref/manual/html_node/Type-Size.html).

**Liên hệ S05:** trước khi hỏi “ghi tới địa chỉ trả về chưa?”, phải biết sink được phép ghi bao nhiêu byte và vùng đích thực sự còn bao nhiêu byte. Chuỗi, địa chỉ của chuỗi và địa chỉ mã hàm là ba thứ khác nhau.

**Tự kiểm tra:** Vì sao mảng 8 byte có thể chứa 8 byte dữ liệu nhưng chỉ chứa C string tối đa 7 byte nội dung? Với `char *p = a`, vì sao không dùng `sizeof(p)` làm dung lượng của `a`?

### 1.2. Source → sink → guard: tìm lỗi trước khi bàn khai thác

**Hiểu gì**

- **Source:** nơi dữ liệu không tin cậy đi vào, như `argv`, stdin, file hoặc socket.
- **Sink:** thao tác sử dụng dữ liệu có thể gây lỗi; ở đây là phép ghi/sao chép vào buffer.
- **Guard:** điều kiện hoặc giới hạn ngăn thao tác nguy hiểm trước khi nó xảy ra. Guard phải ràng buộc đúng độ dài, đúng vùng đích và có hiệu lực trên **mọi đường thực thi tới sink**.

Ví dụ lỗi minh họa, với `input` là C string hợp lệ do người dùng cung cấp:

```c
#include <stdio.h>
#include <string.h>

void show_name(const char *input)
{
    char buf[16];
    strcpy(buf, input);       // không ràng buộc độ dài theo dung lượng buf
    puts(buf);
}
```

| Thành phần | Phân tích |
|---|---|
| Source | Dữ liệu từ người dùng được caller truyền qua `input` |
| Sink | `strcpy(buf, input)` chép cả byte kết thúc `\0` |
| Dung lượng đích | 16 byte tại `buf` |
| Guard | Chưa có |
| Điều kiện ghi vượt | `strlen(input) >= 16`; ví dụ 16 byte nội dung cần 17 byte khi chép cả `\0` |

Bản sửa minh họa, dùng cùng hai header trên:

```c
int show_name_checked(const char *input)
{
    char buf[16];
    size_t len = strlen(input);
    if (len >= sizeof(buf))
        return -1;           // nhánh input quá dài không đi tới sink
    strcpy(buf, input);
    puts(buf);
    return 0;
}
```

Guard đúng ở đây là `len < sizeof(buf)` trên đường đi tới `strcpy`: tối đa 15 byte nội dung và 1 byte `\0`. Điều này dựa trên tiền điều kiện `input` là chuỗi hợp lệ, không chồng lấn với đích và không thay đổi giữa lần kiểm tra với lần sao chép. `strlen()` không tự xác minh một con trỏ tùy ý có trỏ tới chuỗi hợp lệ hay không. Hợp đồng của hàm sao chép được mô tả ở [strcpy(3)](https://man7.org/linux/man-pages/man3/strcpy.3.html).

**Trường hợp đọc byte thô:** `read(fd, buf, n)` đọc tối đa `n` byte và không tự thêm `\0`. `n` lớn hơn dung lượng cho thấy lời gọi cho phép ghi quá nhiều; để nói một lần chạy đã ghi vượt, còn cần quan sát lượng dữ liệu thực sự ghi. Nếu cần dùng kết quả như chuỗi, phải dành chỗ cho byte kết thúc và kiểm tra lỗi trước khi dùng giá trị trả về làm chỉ số:

```c
#include <unistd.h>

int read_name(void)
{
    char buf[16];
    ssize_t n = read(STDIN_FILENO, buf, sizeof(buf) - 1);
    if (n < 0)
        return -1;
    buf[n] = '\0';          // n trong khoảng 0..15 sau kiểm tra lỗi
    // Xử lý tối đa n byte vừa nhận; một lần read chưa chắc đọc hết thông điệp.
    return 0;
}
```

Đây chỉ minh họa giới hạn bộ nhớ cho một lần đọc; input dài có thể còn nằm trong luồng, và dữ liệu chứa byte NUL sẽ làm các hàm chuỗi chỉ thấy phần trước NUL. Nguồn: [Linux man-pages — read(2)](https://man7.org/linux/man-pages/man2/read.2.html).

**Tự kiểm tra:** Đổi guard thành `if (len > sizeof(buf)) return -1;` thì input 16 byte có bị chặn không? Một kiểm tra đặt sau `strcpy` còn ngăn được ghi vượt không? Vì sao nhánh đã `return` trước sink không phải đường gây ghi vượt tại sink đó?

### 1.3. Bộ nhớ tiến trình, stack frame, `call` và `ret`

**Hiểu gì**

Tiến trình có không gian địa chỉ ảo chứa các vùng mã và dữ liệu. Để hiểu S05, cần phân biệt:

| Vùng | Nội dung thường gặp | Vai trò trong S05 |
|---|---|---|
| Mã executable | Lệnh máy của chương trình, các entry PLT | Một số đích chuyển luồng và đoạn mã có sẵn |
| Dữ liệu tĩnh | Biến global, chuỗi hằng; quyền ghi tùy vùng | Có thể chứa chuỗi dùng làm đối số |
| Heap | Vùng cấp phát động, ví dụ qua `malloc` | Phân biệt với buffer trên stack khi xác định loại lỗi |
| Stack | Dữ liệu phục vụ lời gọi hàm, biến cục bộ tùy cách biên dịch | Có thể chứa buffer và saved return address |
| Thư viện được ánh xạ | Mã và dữ liệu của libc, loader và thư viện khác | Nơi implementation của hàm thư viện nằm ở runtime |

**Stack frame** là vùng trạng thái gắn với một lần gọi hàm. Một frame có thể có biến cục bộ, thanh ghi được lưu, padding và dữ liệu bảo vệ. Tham số có thể đi qua thanh ghi, không phải tất cả đều nằm trên stack. Không phải biến cục bộ nào trong mã C cũng được compiler đặt lên stack.

Các thanh ghi cần nhận ra trên x86_64:

- `RIP`: vị trí lệnh đang thực thi; **saved return address** là một giá trị lưu trong bộ nhớ để dùng khi trở về, không phải chính thanh ghi `RIP`.
- `RSP`: con trỏ đỉnh stack hiện tại.
- `RBP`: có thể làm mốc frame; compiler có thể bỏ frame pointer, nên không mặc định luôn có saved `RBP`.
- `RDI`: thanh ghi chứa đối số integer/pointer đầu tiên theo Linux System V AMD64, sẽ dùng ở mục 2.

Trong mô hình near `call`/`ret` thông thường của x86_64, bỏ qua các kiểm tra bổ sung như shadow stack:

```text
call f: lưu địa chỉ lệnh ngay sau call lên stack, rồi chuyển tới f
        RSP giảm 8 byte do lưu địa chỉ trở về

ret:    lấy địa chỉ 8 byte tại [RSP] làm đích tiếp tục
        RSP tăng 8 byte với lệnh ret không có toán hạng
```

`call` không tự cấp phát toàn bộ biến cục bộ. Compiler có thể sinh prologue như `push rbp; mov rbp, rsp; sub rsp, ...`, rồi epilogue khôi phục stack trước `ret`; mã thực tế có thể khác. Nền về lệnh ở [Intel SDM, Volume 2 — CALL/RET](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html); bố cục lời gọi ở [System V AMD64 psABI — Function Calling Sequence](https://gitlab.com/x86-psABIs/x86-64-ABI/-/blob/master/x86-64-ABI/low-level-sys-info.tex).

Sơ đồ một frame **minh họa**, địa chỉ cao ở trên:

```text
địa chỉ cao  ┌──────────────────────────────┐
             │ frame của caller             │
             ├──────────────────────────────┤
             │ saved return address         │ ← đích dùng khi hàm ret
             │ saved RBP, nếu có            │
             │ padding / canary / biến khác │ ← bố cục tùy binary
             │ ... buf[15]                  │
             │ ...                          │
địa chỉ thấp │ buf[0]                       │ ← bắt đầu ghi buffer
             └──────────────────────────────┘
```

Stack tăng trưởng về địa chỉ thấp khi thêm dữ liệu bằng `push`/`call`; còn ghi `buf[i]` với `i` tăng đi về địa chỉ cao. Vì vậy một phép ghi tràn liên tục có thể chạm dữ liệu nằm phía địa chỉ cao hơn buffer, trong đó **có thể** có saved return address. Không phải mọi ghi tràn đều chạm tới đó: còn tùy khoảng cách, lượng ghi, bố cục và bảo vệ.

**Offset tới saved return address** là khoảng cách byte từ byte đầu của vùng đích tại sink (ví dụ `&buf[0]`) tới slot saved return address. Kích thước buffer không tự cho offset vì còn padding, biến khác và dữ liệu đã lưu. Mọi con số phải đo trên binary S05.

**Tự kiểm tra:** `call` lưu địa chỉ của hàm được gọi hay địa chỉ lệnh sau `call`? Đổi dữ liệu trong saved return address có lập tức đổi `RIP` không? Vì sao buffer 16 byte không đủ để kết luận offset bằng 16?

### 1.4. Từ ghi vượt đến sử dụng lại mã: mỗi bước cần bằng chứng riêng

**Hiểu gì**

```text
input → sink ghi vượt → dữ liệu điều khiển bị ảnh hưởng
      → chuyển tới đích đã chọn → tham số và stack đúng ABI
      → hàm thư viện thực thi đúng yêu cầu → đạt mục tiêu challenge
```

| Mức nhận định | Cần quan sát gì? | Chưa tự chứng minh điều gì? |
|---|---|---|
| Có ghi vượt | Phép ghi ra ngoài vùng đích; đối chiếu mã, bộ nhớ hoặc báo cáo công cụ | Chưa chắc chạm dữ liệu điều khiển |
| Có crash | Tín hiệu/lỗi và vị trí dừng | Chưa chứng minh chọn được đích thực thi |
| Saved return address bị thay đổi | Giá trị ở đúng slot trước khi hàm trở về | Chưa chắc `ret` tới được đích mong muốn |
| Điều khiển được đích chuyển luồng | Debugger cho thấy tới đích do input quyết định | Chưa chắc tham số, alignment và đường tiếp tục hợp lệ |
| Gọi đúng hàm thư viện | Đã tới implementation với đối số đúng | Chưa chắc lệnh thành công hoặc đạt mục tiêu CTF |
| Đạt mục tiêu challenge | Kết quả thực tế theo yêu cầu challenge | Chưa chứng minh chạy ổn định ở cấu hình khác |

Ý tưởng **return-to-libc** là hướng luồng thực thi tới mã hàm đã có trong libc, với trạng thái gọi phù hợp. Stack vẫn có thể giữ dữ liệu, địa chỉ và đối số dù bị NX cấm thực thi lệnh tại đó. CPU thực thi mã ở vùng chương trình/thư viện có quyền execute; không cần biến các byte input trên stack thành lệnh máy.

Phân biệt các khái niệm để dùng đúng trong S05:

| Khái niệm | Vai trò |
|---|---|
| Chèn mã trên stack | Đặt lệnh máy mới trong input rồi cố thực thi ở stack; bị cản khi trang đó không có quyền execute |
| Direct ret2libc | Chuyển trực tiếp tới địa chỉ hàm trong libc đang nạp |
| Gọi qua PLT, thường gọi ret2plt trong ngữ cảnh này | Đến entry của executable để nó chuyển tiếp tới hàm thư viện |
| ROP | Ghép các đoạn mã có sẵn, thường kết thúc bằng `ret`, để thay đổi trạng thái và nối luồng |

ROP và gọi libc có thể cùng xuất hiện: một đoạn mã ngắn chuẩn bị đối số rồi chuyển tới hàm thư viện. Với S05, demo `split` dự kiến được mô tả là **tái sử dụng hàm libc qua `system@plt` bằng ROP ngắn**. Nguồn về ý tưởng và môi trường học: [ROP Emporium — Beginners' guide](https://ropemporium.com/guide.html).

**Tự kiểm tra:** Vì sao NX vẫn cho phép stack chứa địa chỉ hàm? Nếu input làm chương trình crash tại `ret`, còn thiếu gì để nói đã gọi được `system()`? Nếu đã in flag rồi crash sau đó, phải báo riêng kết quả mục tiêu và trạng thái kết thúc như thế nào?

### 1.5. CWE, CVE và tên kỹ thuật khai thác

**Hiểu gì**

**Vì sao S05 vẫn nhắc CWE-121?** CWE phân loại yếu điểm trong chương trình; ret2libc mô tả cách sử dụng lại mã khi đã có điều kiện điều khiển luồng. Nếu ca demo có lỗi tràn buffer trên stack, CWE-121 mô tả **lỗi nền của ca demo**. Điều đó không biến chủ đề S05 thành bài về stack-based buffer overflow, cũng không có nghĩa mọi trường hợp ret2libc đều bắt nguồn từ CWE-121.

Ngay trong mục *Background Details*, [MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html) mô tả khả năng thay địa chỉ trở về để chuyển tới hàm thư viện như `system()`, gọi là return-into-libc. Đây là mối liên hệ giữa một loại lỗi và một cách khai thác, không phải hai tên đồng nghĩa.

- **CWE-787 — Out-of-bounds Write:** mô tả việc ghi ra ngoài biên vùng đệm dự định; không giới hạn riêng stack.
- **CWE-121 — Stack-based Buffer Overflow:** cụ thể cho tràn buffer được cấp trên stack. Trang CWE-121 liệt kê quan hệ `ChildOf` với CWE-787 trong view Research Concepts. Đây không phải tình trạng cạn stack do đệ quy quá sâu.
- **Ret2libc/ROP:** mô tả cách tận dụng điều kiện điều khiển luồng; không phải nhãn thay thế cho lỗi ghi vượt.
- **CVE:** mã định danh một lỗ hổng cụ thể trong sản phẩm. Một CVE có thể được hồ sơ nguồn gán một hoặc nhiều CWE; cần trích đúng nhãn của hồ sơ rồi tách riêng phân tích kỹ thuật của nhóm.

Quan hệ rút gọn phục vụ bài học, không phải toàn bộ cây CWE:

```text
CWE-787: ghi ngoài biên
    └─ CWE-121: tràn buffer trên stack

Lỗi tràn buffer trên stack
    → có thể tạo điều kiện đổi địa chỉ trả về
    → có thể khai thác bằng ret2libc nếu đủ điều kiện khác
```

Hai mũi tên ở phần dưới là **chuỗi điều kiện khai thác**, không phải quan hệ phân loại CWE. Nguồn: [MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html), [MITRE CWE-787](https://cwe.mitre.org/data/definitions/787.html).

**Liên hệ S05:** phải chứng minh lỗi nền của binary là gì, sau đó mới giải thích kỹ thuật dùng để khai thác. Với buffer trên heap, không gán CWE-121 chỉ vì hậu quả có thể làm đổi luồng.

**Cách trình bày mục CWE trong seminar:** “Ret2libc là kỹ thuật tái sử dụng mã. Trong ca minh họa này, lỗi nền là …, được phân loại …; lỗi đó tạo điều kiện cho chuỗi gọi hàm thư viện.” Chỉ điền CWE-121 khi đã xác nhận lỗi tràn buffer trên stack. Với `split`, đây vẫn là phân loại dự kiến theo mô tả của tác giả, cần đối chiếu binary S05; với CVE, giữ riêng nhãn của hồ sơ nguồn và phân tích của nhóm.

**Tự kiểm tra:** Ghi ngoài biên trên heap có thuộc CWE-787 không? Vì sao không gọi “ret2libc” là CWE của ca demo? Có phải mọi CWE-121 đều khai thác ret2libc được không?

### 1.6. Debugger và disassembly: đọc gì để kiểm chứng?

**Hiểu gì**

Disassembly cho thấy các lệnh và lời gọi trong binary; debugger cho thấy trạng thái của **một lần chạy cụ thể**. Cần kết hợp cả hai: đọc sink và vùng đích, dừng trước/sau phép ghi, xác định slot địa chỉ trả về, rồi quan sát đích chuyển luồng và tham số.

Các lệnh dưới đây là gợi ý dùng trong GDB trên **VM Linux x86_64 của S05**, chưa phải log đã chạy:

| Lệnh | Mục đích |
|---|---|
| `disassemble main` | Bắt đầu đọc các lời gọi từ `main`; tìm hàm nhận input theo binary thực |
| `info registers rip rsp rbp rdi` | Quan sát vị trí thực thi, stack và đối số đầu |
| `x/8gx $rsp` | Xem 8 đơn vị, mỗi đơn vị 8 byte, dạng hex tại stack hiện tại |
| `x/i $rip` | Đọc lệnh ở vị trí đang dừng |
| `x/s $rdi` | Khi đã dừng tại entry hàm nhận con trỏ chuỗi qua `RDI`, xem chuỗi đối số |
| `p/x ((unsigned long)$rsp & 0xf)` | Xem phần dư chia 16 của `RSP`; diễn giải theo đúng điểm dừng ở mục 2 |
| `info proc mappings` | Đối chiếu địa chỉ với vùng executable/libc/stack ở runtime |
| `show disable-randomization` | Ghi thiết lập randomization của GDB khi khởi chạy tiến trình |

Không mặc định ô tại `$rsp` ở mọi điểm dừng đều là saved return address: điều đó đúng tại entry hàm theo mô hình lời gọi thông thường; prologue và các thao tác stack có thể đã thay đổi `RSP`. Nguồn cú pháp xem bộ nhớ: [GDB — Examining Memory](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Memory.html).

GDB có thiết lập tắt ASLR khi khởi chạy trên các target hỗ trợ như GNU/Linux. Vì vậy địa chỉ thấy trong GDB và khi chạy độc lập cần được ghi nhận riêng. Biết địa chỉ nhờ debugger trong lab chưa chứng minh input tự làm rò rỉ địa chỉ. Nguồn: [GDB — Starting, disable-randomization](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Starting.html).

**Tự kiểm tra:** Tại sao một ảnh crash không thay thế được ảnh tham số tại entry hàm thư viện? Nếu địa chỉ libc giữ nguyên qua hai lần chạy trong GDB, đã kết luận được ASLR của máy tắt chưa?

## 2. ABI: chuẩn bị lời gọi hàm

**Hiểu gì:** ABI (*Application Binary Interface*) quy định cách các thành phần mã máy tương tác, gồm vị trí đối số, giá trị trả về và trạng thái stack. Chuyển luồng tới đúng địa chỉ hàm mới chỉ giải quyết phần “chạy ở đâu”; còn phải chuẩn bị “hàm lấy đối số từ đâu” và “sau khi hàm kết thúc sẽ đi đâu”.

| Nội dung | x86 32-bit, `cdecl` | Linux System V AMD64 |
|---|---|---|
| Tham số integer/pointer | Truyền trên stack; caller thường dọn tham số | Sáu tham số đầu qua `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9`; tham số tiếp theo dùng stack |
| Giá trị trả về cơ bản | `EAX` | `RAX` |
| Điều cần kiểm tra | Thứ tự tham số, địa chỉ trở về và trạng thái stack sau lời gọi | Tham số đầu trong `RDI`, stack alignment và trạng thái sau lời gọi |

Sơ đồ **minh họa tại entry** một hàm nhận đối số con trỏ, sau khi đã chuyển tới hàm:

```text
x86 cdecl:                         Linux System V AMD64:
[ESP]     = địa chỉ tiếp tục        [RSP] = địa chỉ tiếp tục
[ESP + 4] = con trỏ đối số đầu      RDI   = con trỏ đối số đầu
```

`RDI` phải chứa **địa chỉ của chuỗi**, không phải các ký tự được ghép thành một số. Chỉ đặt địa chỉ chuỗi lên stack theo cách của x86 không khiến `system()` trên AMD64 tự lấy nó làm đối số. **Gadget** là đoạn lệnh có sẵn được dùng làm một bước của chuỗi; ví dụ `pop rdi; ret` lấy một giá trị từ stack vào `RDI` rồi tiếp tục chuyển luồng. Phải tìm đoạn mã và kiểm tra tác động trên binary thực, không giả định sẵn địa chỉ.

Với lời gọi AMD64 thông thường như `system(const char *)`, `RSP % 16 == 0` ngay trước `call`. `call` đẩy địa chỉ trả về 8 byte, nên tại entry hàm, `(RSP + 8) % 16 == 0`, tức `RSP % 16 == 8`. Khi chuyển bằng `ret`, không có một `call` mới tự tạo trạng thái đó: cần kiểm tra `RSP` và địa chỉ tiếp tục tại entry. Yêu cầu alignment có thể cao hơn với một số đối số vector trên stack, nằm ngoài ví dụ này. Nguồn: [System V AMD64 psABI — Function Calling Sequence](https://gitlab.com/x86-psABIs/x86-64-ABI/-/blob/master/x86-64-ABI/low-level-sys-info.tex), [LSB IA-32 ELF/ABI](https://refspecs.linuxfoundation.org/LSB_5.0.0/LSB-Core-IA32/LSB-Core-IA32/elf-ia32.html).

Sai alignment có thể làm một số lệnh truy cập bộ nhớ trong libc lỗi. Đây là **một nguyên nhân cần kiểm tra**, không phải lời giải mặc định cho mọi crash trong libc; còn phải xem địa chỉ hàm, đối số, vùng nhớ và đường tiếp tục.

**`system()` khác `syscall`:** `system()` là hàm thư viện nhận con trỏ tới C string, thực hiện lệnh thông qua shell và chờ lệnh hoàn tất. `syscall` là lệnh CPU dùng để vào kernel trên Linux x86_64, với quy ước lời gọi hệ thống riêng. Gọi được `system()` không đồng nghĩa đã mở shell tương tác; đối số quyết định lệnh được yêu cầu. Demo dự kiến dùng chuỗi có sẵn để đọc flag. Nguồn: [Linux man-pages — system(3)](https://man7.org/linux/man-pages/man3/system.3.html).

**Tự kiểm tra:** Đã tới `system()` nhưng `RDI` trỏ vào vùng không đọc được thì còn đúng lời gọi không? Vì sao tại entry hàm lại mong `RSP % 16 == 8` thay vì 0? Khi `system()` kết thúc, địa chỉ tiếp tục được lấy từ đâu?

## 3. Từ hàm chương trình đến thư viện động

**Hiểu gì:** libc là thư viện cung cấp nhiều hàm C như `puts`, `strcpy`, `system`. Với chương trình liên kết động, executable có thể chứa đường gọi tới thư viện mà không chứa implementation của hàm đó. Dynamic linker/loader nạp thư viện và thực hiện các công việc liên kết cần thiết ở runtime.

| Khái niệm | Cần phân biệt |
|---|---|
| `system@plt` | Entry mã trong executable để chuyển tiếp tới hàm thư viện; không phải chính implementation của `system` |
| GOT entry | Một ô dữ liệu phục vụ liên kết động, có thể giữ địa chỉ hàm sau khi được resolve; địa chỉ ô khác với giá trị chứa trong ô |
| Libc offset | Độ lệch của hàm so với base của **đúng libc build** đang xét |
| Libc runtime address | Địa chỉ thực tế của hàm trong tiến trình đang chạy, phụ thuộc base được nạp |

Hai đường gọi **minh họa**:

```text
Qua PLT:     luồng đã đổi → system@plt trong executable
                         → GOT / dynamic resolver khi cần → system trong libc

Trực tiếp:   luồng đã đổi → địa chỉ runtime của system trong libc
```

Với lazy binding, resolver có thể xác định địa chỉ ở lần gọi đầu và cập nhật GOT; với liên kết sớm, việc resolve diễn ra trước đó. Gọi qua PLT không yêu cầu phải sửa GOT. Nền về đường PLT/GOT được mô tả ở [ROP Emporium guide — Appendix A](https://ropemporium.com/guide.html#appendix-a).

Với hàm `system` thông thường của đúng bản libc đang dùng, mô hình tính địa chỉ là `địa chỉ runtime = libc base (load bias) + offset của system`. Biết offset từ một file libc không tự cho biết base của lần chạy hiện tại; dùng libc build khác có thể cho offset khác. Base của executable và base của libc là hai đại lượng riêng.

Với `split`, nhiệm vụ dự kiến là xác nhận import `system()`, chuỗi dữ liệu, đích PLT và ABI trên binary thực. Gọi được `system@plt` không tự chứng minh đã biết libc base hay đã vượt ASLR. Mô tả challenge: [ROP Emporium split](https://ropemporium.com/challenge/split.html).

**Tự kiểm tra:** Một GOT entry ở địa chỉ `A` chứa giá trị `B`: đâu là địa chỉ ô, đâu là đích hàm đã resolve? Nếu executable không PIE nhưng libc chịu ASLR, địa chỉ PLT và địa chỉ implementation có nhất thiết cùng cố định không?

Thực hành mở rộng: [SEED Return-to-libc Attack Lab](https://seedsecuritylabs.org/Labs_20.04/Software/Return_to_Libc/) để học direct ret2libc; đây là lab theo môi trường SEED Ubuntu 20.04, không thay cho demo CTF và chưa xác minh tương thích Kali của nhóm. Có thể đối chiếu bài “Return to libc” trong [pwn.college — Return Oriented Programming](https://pwn.college/pwndamentals~cfe9c1cb/return-oriented-programming/), cần xác nhận tài khoản/quyền truy cập và môi trường nền tảng trước khi chọn.

## 4. Guard và các lớp bảo vệ

**Hiểu gì:** mỗi lớp tác động vào một bước khác nhau. Kiểm tra biên ngăn ghi sai; canary có thể phát hiện ghi đè trước khi trở về; NX hạn chế nơi được thực thi; ASLR/PIE ảnh hưởng độ dự đoán địa chỉ; RELRO hạn chế sửa dữ liệu liên kết động. Bật một lớp không tự làm các bước còn lại an toàn.

| Cơ chế | Tác dụng cần giải thích | Giới hạn cần nêu |
|---|---|---|
| Kiểm tra biên/độ dài | Ngăn phép ghi vượt dung lượng đích trên mọi đường tới sink | Phải xét cả kích thước thực, con trỏ và giá trị trả về của hàm đọc |
| NX/DEP | Ngăn thực thi ở trang dữ liệu không có quyền execute | Mã thư viện và mã chương trình vẫn có thể thực thi; NX không sửa lỗi ghi vượt |
| Stack canary | Lưu giá trị kiểm tra trong frame và kiểm tra lại trước khi hàm trở về; phát hiện một số dạng ghi tràn đi qua vị trí đó | Phụ thuộc hàm có được bảo vệ, vị trí dữ liệu và phép ghi; không sửa lỗi ghi vượt |
| ASLR | Ngẫu nhiên hóa vị trí các vùng được hỗ trợ, gồm thư viện | Trạng thái runtime và cách khởi chạy phải được ghi nhận; không suy ra từ riêng kết quả `checksec` |
| PIE | Cho phép executable được bố trí ở base thay đổi khi ASLR áp dụng | Cần phân biệt base executable với base libc |
| RELRO | Đặt vùng relocation được chọn thành chỉ đọc sau khi xử lý; full RELRO thường kết hợp resolve sớm để bảo vệ cả GOT phục vụ lời gọi hàm | Hạn chế ghi sửa GOT; không cấm đọc GOT hoặc gọi qua PLT, không chặn mọi ROP |
| Sửa mã và kiểm thử | Giới hạn ghi đúng dung lượng, xử lý lỗi, dùng ASan khi kiểm thử | Đây là biện pháp xử lý lỗi nền; không thay bằng chỉ bật bảo vệ |

CET/shadow stack và CFI là phần mở rộng khi còn thời gian: tập trung mục tiêu bảo vệ luồng điều khiển, không khẳng định binary/VM đang hỗ trợ khi chưa kiểm tra.

Khi phân tích một lần chạy thất bại, cần nói được **lớp nào chặn bước nào**: bị dừng trước `ret` khác với đã chuyển tới địa chỉ sai, và khác với đã tới libc nhưng tham số sai. `checksec` hỗ trợ đọc thuộc tính binary; ASLR là điều kiện runtime cần ghi riêng. Không PIE cũng không có nghĩa toàn bộ tiến trình, gồm libc và stack, đều có địa chỉ cố định.

Nguồn nền về giảm thiểu lỗi bộ nhớ: [MITRE CWE-787 — Potential Mitigations](https://cwe.mitre.org/data/definitions/787.html); tùy chọn `relro` và `now`: [GNU ld — Options](https://sourceware.org/binutils/docs/ld/Options.html).

**Tự kiểm tra:** NX bật có ngăn ghi tràn xảy ra không? Full RELRO có cấm gọi `system@plt` không? Muốn sửa lỗi gốc trong ví dụ `show_name`, cần thay đổi gì ngoài bật các cờ bảo vệ?

## 5. CVE và tự kiểm tra

Đọc [ghi chú CVE-1999-0032](cve/CVE-1999-0032.md), phân biệt lỗi được hồ sơ CVE mô tả với kỹ thuật trong công bố nghiên cứu. Khi dùng ca lịch sử phải nêu đúng điều kiện nền tảng và phạm vi bảo vệ; không tái hiện CVE.

- [ ] Phân biệt được dung lượng buffer, độ dài C string, byte `\0` và số byte `read()` thực sự trả về.
- [ ] Chỉ ra source, sink, guard và đường input quá dài bị chặn trong ví dụ C.
- [ ] Vẽ được stack frame minh họa; giải thích `call`/`ret`, `RIP`/`RSP` và vì sao phải đo offset.
- [ ] Phân biệt được ghi vượt, crash, thay đổi saved return address, điều khiển đích và đạt mục tiêu.
- [ ] Giải thích được CWE-121/CWE-787, CVE và ret2libc thuộc các khái niệm nào.
- [ ] Giải thích được vì sao NX không ngăn mọi cách sử dụng lại mã.
- [ ] Vẽ được hai đường gọi `system@plt` và direct ret2libc, nêu điều kiện địa chỉ và ABI của từng đường.
- [ ] Phân biệt được PLT entry, GOT entry, libc offset và địa chỉ libc runtime.
- [ ] Chỉ được tham số và alignment tại entry hàm thư viện bằng debugger.
- [ ] Nêu được bảo vệ thực tế của binary S05 và bằng chứng tương ứng.
- [ ] Phân biệt được lỗi tràn stack trong CVE với kỹ thuật khai thác đang nghiên cứu.

## 6. Bài tập đầu tiên và khung nói 5–6 phút

**Bài tập chung trước khi mở debugger:** dùng hai hàm `show_name` và `show_name_checked` ở mục 1.2, xét input ASCII có độ dài 0, 15, 16 và 20 byte. Với từng trường hợp, ghi số byte `strcpy` cần chép nếu tới sink, kết quả của guard và có đi tới sink không. Sau đó vẽ frame **minh họa**, chỉ ra dữ liệu điều khiển có thể bị ảnh hưởng và những điều chưa thể suy ra từ mã nguồn.

Tiếp theo, vẽ hai sơ đồ truyền đối số ở mục 2; đánh dấu riêng địa chỉ mã hàm, địa chỉ dữ liệu chuỗi và nơi chứa địa chỉ tiếp tục. Chưa điền địa chỉ hay offset của `split` khi chưa đo. Khi thực hiện, lưu bài làm vào `notes/` theo [PLAN.md mục 2](PLAN.md#2-học-nền-và-bài-tập-chung).

Khung trình bày ngắn, sau khi đã học kỹ các phần trên:

| Thời gian | Nội dung cần nói được |
|---|---|
| 0:00–1:30 | Buffer, `\0`, source–sink–guard; chỉ lỗi ghi vượt trong ví dụ C |
| 1:30–2:30 | Stack frame, saved return address, `call`/`ret`; crash khác điều khiển luồng |
| 2:30–3:30 | CWE-121/CWE-787 và ý tưởng tái sử dụng mã khi stack có NX |
| 3:30–5:00 | ABI AMD64: con trỏ trong `RDI`, alignment và địa chỉ tiếp tục; phân biệt PLT với direct ret2libc |
| 5:00–6:00 | Điều kiện còn phải kiểm chứng, vai trò các lớp bảo vệ; chuyển sang ca CVE và demo S05 |
