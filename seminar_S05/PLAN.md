# Kế hoạch mini seminar S05 — Return-to-libc (ret2libc)

Cập nhật: **2026-10-19**. Yêu cầu chuẩn: [REQUIREMENTS.md](REQUIREMENTS.md). Quy tắc: [../AGENT.md](../AGENT.md). Trạng thái thực hiện: [CHECKLIST.md](CHECKLIST.md).

**Mục tiêu:** giải thích cách điều khiển luồng thực thi để tái sử dụng hàm thư viện khi stack không thực thi được; nối rõ buffer overflow → khả năng chiếm luồng → gọi hàm có sẵn → tác dụng và giới hạn của bảo vệ.

## 0. Việc cần làm ngay

1. [x] Xác định phạm vi độc lập của S05: return-to-libc, lỗi nền và cơ chế bảo vệ.
2. [ ] Chốt ngày seminar, tên A/B/C và thời gian còn lại.
3. [ ] Chuẩn bị challenge **ROP Emporium `split` x86_64** trên Kali amd64/UTM đã có; xác nhận kiến trúc, checksum, loader và libc thực tế.
4. [ ] Đo offset và kiểm tra NX/canary/PIE/RELRO của chính `split`; ghi trạng thái ASLR khi chạy ngoài GDB và thiết lập randomization trong GDB.
5. [ ] Phân tích đường gọi `system()` qua PLT và quy ước truyền tham số; lưu bằng chứng mới cho S05.
6. [ ] Chuẩn bị phần trình bày CVE-1999-0032 theo [ghi chú riêng S05](cve/CVE-1999-0032.md); sau đó soạn slide và diễn tập.

Các mục 3–6 là **công việc sắp làm**. Phiên đổi kế hoạch chưa tải/chạy challenge, chưa đo offset, chưa tạo slide hoặc ảnh S05.

## 1. Phạm vi S05

| Nội dung | Cách dùng trong S05 |
|---|---|
| Buffer overflow, stack frame, saved return address | Kiến thức nền để giải thích điều kiện chiếm quyền điều khiển luồng |
| Return-to-libc | Trọng tâm: gọi hàm có sẵn trong libc, chuẩn bị đối số và đường tiếp tục hợp lệ |
| `split` dự kiến | Demo tái sử dụng hàm libc qua `system@plt`, kết hợp ROP ngắn để chuẩn bị đối số trên x86_64 |
| Nhảy trực tiếp vào libc | Giải thích riêng cách xác định đúng bản libc và địa chỉ runtime; thực hành mở rộng nếu đủ thời gian |
| ROP tổng quát, pivot, one-gadget | Ngoài trọng tâm; chỉ giải thích đủ để hiểu khác biệt, không mở rộng demo |

**Phát biểu phải giữ chính xác:** ret2libc là kỹ thuật khai thác/tái sử dụng mã; CWE mô tả lỗi nền. Demo gọi `system@plt` không tự chứng minh đã tìm libc base hoặc vượt ASLR của libc. Nếu yêu cầu chấm cụ thể đòi nhảy trực tiếp vào libc, phải bổ sung challenge theo nhánh mở rộng ở mục 4 trước khi chốt demo.

Tài liệu, sơ đồ và bằng chứng của S05 được chuẩn bị trong thư mục này. Offset, địa chỉ hàm/gadget và trạng thái hoàn thành chỉ ghi khi đã xác nhận trên binary đang dùng.

## 2. Học nền và bài tập chung

Chi tiết thứ tự học: [KNOWLEDGE.md](KNOWLEDGE.md).

1. Ôn C, giới hạn buffer, `call`/`ret`, stack frame và phân biệt dữ liệu với địa chỉ mã.
2. Phân biệt chèn mã trên stack, gọi thư viện qua PLT, direct ret2libc và ROP; giải thích vì sao stack không thực thi vẫn có thể chứa đối số/địa chỉ cho mã nằm ở vùng thực thi khác.
3. Đối chiếu x86 cdecl (đối số trên stack) và System V AMD64 (đối số con trỏ đầu tiên qua `RDI`, yêu cầu căn lề stack). Demo thống nhất **x86_64**; không dùng nguyên bố cục payload x86 cho x86_64.
4. Học libc, dynamic linker, PLT/GOT và địa chỉ runtime ở mức đủ đọc đường gọi thư viện.
5. Phân tích NX, canary, ASLR/PIE và RELRO theo từng bước của chuỗi; kiểm tra biên và sửa mã là cách xử lý lỗi gốc.

**Bài tập chung:** chọn một đoạn C nhỏ có lỗi ghi vượt và bản sửa để phân tích cho S05. Mỗi thành viên lập bảng: nguồn input, sink, guard, điều kiện để tới saved return address, NX ảnh hưởng ở đâu và còn thiếu bằng chứng gì để kết luận gọi được hàm thư viện. Vẽ hai sơ đồ ABI có nhãn **minh họa**. Lưu phân tích vào `notes/` khi thực hiện.

## 3. Kế hoạch theo 10 mục của đề

| Mục | Nội dung S05 cần chuẩn bị | Bằng chứng/đầu ra |
|---|---|---|
| 1. Giới thiệu và bối cảnh | Tái sử dụng mã thư viện trong chương trình C/C++; bối cảnh stack NX và lỗi bộ nhớ có thể làm đổi luồng | Sơ đồ vùng dữ liệu stack và vùng mã thư viện; mục tiêu demo |
| 2. Nguyên lý và điều kiện | Ghi tới dữ liệu điều khiển; địa chỉ hàm hợp lệ; đối số đúng ABI; stack alignment; đường tiếp tục | So sánh chèn mã, gọi libc qua PLT và nhảy trực tiếp vào libc |
| 3. CWE và quan hệ với chủ đề | CWE-121 cho lỗi stack buffer của ca demo nếu được phân tích xác nhận; liên hệ CWE-787. Ret2libc không phải tên của lỗi gốc | Đánh dấu vùng ghi ngoài biên và giải thích lỗi nền → kỹ thuật khai thác |
| 4. Vị trí và nguyên nhân | Theo dấu input tới sink; dung lượng vùng đệm, giới hạn đọc/ghi, guard; đường liên kết tới hàm thư viện | Source/disassembly của binary S05, offset đo lại và bản đồ vùng nhớ |
| 5. Chuỗi khai thác | Input → ghi vượt → thay đổi địa chỉ trả về → chuẩn bị đối số → gọi hàm thư viện → quan sát kết quả | Sơ đồ bám đúng demo; debugger cho thấy tới hàm thư viện với đối số đúng |
| 6. CVE thực tế | CVE-1999-0032: lỗi `lpr`, điều kiện cục bộ, tác động và khắc phục; đối chiếu công bố return-into-libc | Hai slide; phân biệt bằng chứng từ hồ sơ CVE, advisory và công bố kỹ thuật |
| 7. Demo Pwnable | `split` x86_64 trong VM cô lập; input thường, phân tích lỗi, gọi `system()` theo mục tiêu CTF | Log/ảnh riêng S05, trạng thái NX thực tế, kết quả challenge và ít nhất hai lần chạy liên tiếp |
| 8. Khắc phục và bảo vệ | Sửa giới hạn ghi, kiểm tra độ dài/kết quả; so sánh NX/canary/ASLR/PIE/RELRO; ASan khi kiểm thử mã có source | Mã lỗi/sửa; bảng mỗi cơ chế tác động ở bước nào và giới hạn |
| 9. Điều kiện và giới hạn | Kiến trúc, ABI, libc/loader, trạng thái randomization, độ kiểm soát input, các bảo vệ đã đo | Bảng đã xác nhận/chưa xác nhận; phân biệt kết quả trong GDB và ngoài GDB |
| 10. Kết luận | Lỗi bộ nhớ và kỹ thuật tái sử dụng mã là hai lớp phân tích; NX hữu ích nhưng cần phối hợp bảo vệ; ưu tiên sửa lỗi gốc | Ba ý kết luận dựa trên bằng chứng đã thu |

## 4. Demo và CVE dự kiến

### Demo chính: ROP Emporium `split` x86_64

[Trang chính của challenge](https://ropemporium.com/challenge/split.html) mô tả NX bật, có lời gọi `system()` và chuỗi lệnh đọc `flag.txt`. Chọn bài này để quan sát việc ghép đường gọi hàm thư viện và đối số khi stack không thực thi. **Mới xác minh mô tả trên trang ngày 2026-10-19; chưa xác minh binary tại VM.**

Đặt đúng tên kết quả trên slide: **tái sử dụng hàm libc qua PLT bằng ROP ngắn**. Phân tích điểm vào `system@plt` và bước thực thi trong thư viện; không gọi đây là bằng chứng đã tính được địa chỉ libc trực tiếp. Trạng thái canary/PIE/RELRO, offset, địa chỉ và căn lề phải lấy từ binary đang dùng.

**Nhánh thực hành direct ret2libc:** xem module [pwn.college — Pwndamentals](https://pwn.college/pwndamentals~cfe9c1cb/return-oriented-programming/) có bài “Return to libc” theo nguồn đã kiểm tra ngày 2026-10-19. Trước khi chọn phải xác nhận quyền truy cập, kiến trúc và điều kiện chạy; không mặc định tải được về Kali. Đầu ra cần bổ sung: bản libc đúng, cách biết địa chỉ runtime, điểm vào trực tiếp trong vùng mã libc và giới hạn khi ASLR bật. Thông tin debugger cung cấp để học phải được ghi là giả định của lab, không phải khả năng tự rò rỉ địa chỉ của exploit. Có thể học thêm bằng [SEED Return-to-libc Attack Lab](https://seedsecuritylabs.org/Labs_20.04/Software/Return_to_Libc/); đây là lab học tập, không thay thế yêu cầu CTF, và môi trường được tác giả kiểm thử là SEED Ubuntu 20.04.

### CVE được chọn: CVE-1999-0032 trong lpr

Chuẩn bị theo [cve/CVE-1999-0032.md](cve/CVE-1999-0032.md). Nguồn gồm hồ sơ NVD, advisory FreeBSD và công bố gốc return-into-libc. Ghi chú đã tách rõ phát biểu của từng nguồn và cách đối chiếu lỗi với kỹ thuật khai thác.

Phần trình bày phải có sản phẩm, nguyên nhân, input, điều kiện, tác động, phạm vi bản vá và mối liên hệ với ret2libc. Chỉ nghiên cứu CVE; demo thực hành là challenge CTF riêng. Không suy ra khả năng vượt mọi bảo vệ hiện đại từ một ca lịch sử.

## 5. Kịch bản demo và bằng chứng cần thu

Tạo `demo/`, `evidence/`, `notes/`, `slides/` khi bắt đầu làm các sản phẩm tương ứng. Các tên dưới đây là đầu ra dự kiến, chưa phải file/ảnh đã có.

| Bước | Thực hiện trong VM | Bằng chứng dự kiến |
|---|---|---|
| 1 | Ghi ngày, nguồn binary, checksum, `uname -m`, `file`, phiên bản công cụ, loader/libc và thuộc tính bảo vệ; ghi riêng ASLR của tiến trình | `evidence/01_moi_truong_va_bao_ve.png` + log |
| 2 | Chạy input ngắn làm mốc so sánh | `evidence/02_chay_binh_thuong.png` |
| 3 | Xác định sink, dung lượng buffer, guard và đường ghi tới dữ liệu điều khiển | `evidence/03_sink_va_stack.png` |
| 4 | Đo offset; quan sát thay đổi địa chỉ trả về; xác định đối số và yêu cầu ABI | `evidence/04_dieu_khien_luong_va_abi.png` |
| 5 | Theo debugger qua PLT tới hàm thư viện; kiểm tra vùng mã đang thực thi và đối số; đối chiếu stack NX | `evidence/05_goi_ham_libc.png` |
| 6 | Chạy ngoài debugger, đạt mục tiêu challenge ít nhất hai lần liên tiếp; lưu lỗi/exit status nếu có | `evidence/06_ket_qua_challenge.png` + log hai lần |
| 7 | Giải thích bản sửa và tác dụng từng lớp bảo vệ; nếu có source lab thì kiểm tra lại với input cũ | `notes/` và slide sửa lỗi |

Mỗi ảnh có chú thích trong `evidence/README.md`: ngày, lệnh, binary, điều ảnh chứng minh. Phân biệt **ghi vượt / crash / chiếm luồng / gọi được hàm thư viện với đối số đúng / đạt mục tiêu CTF**.

Dự phòng: bộ ảnh và log từ lần chạy thật, kèm video nếu có. Dừng demo trực tiếp và trình bày theo bằng chứng đã lưu khi VM emulation quá chậm.

## 6. Bố cục 14 slide và thời gian

| Slide | Nội dung | Phút |
|---|---|---|
| 1 | Chủ đề, mục tiêu và bối cảnh | 1 |
| 2 | Ôn buffer overflow, saved return address và CWE | 2 |
| 3 | NX và ý tưởng return-to-libc | 1,5 |
| 4 | ABI; phân biệt ret2plt, direct ret2libc và ROP | 1,5 |
| 5–6 | CVE: nguyên nhân, điều kiện, tác động, bản vá, giới hạn liên hệ | 4 |
| 7 | Môi trường challenge và bảo vệ đã đo | 1 |
| 8 | Sink, vùng đệm, offset và điều kiện chiếm luồng | 2 |
| 9 | Sơ đồ gọi hàm thư viện và truyền đối số | 2 |
| 10 | Demo, debugger và kết quả challenge | 4 |
| 11 | Đối chiếu bằng chứng, điểm vào PLT và địa chỉ libc trực tiếp | 1 |
| 12 | Sửa lỗi và bảng các cơ chế bảo vệ | 2 |
| 13 | Điều kiện, giới hạn và kết luận | 2 |
| 14 | Nguồn tham khảo và hỏi đáp | 2 |
| **Tổng** | **Gồm hỏi đáp** | **26** |

Nếu chỉ có 20 phút: nền 4, CVE 3, phân tích/demo 8, sửa lỗi/kết luận 3, hỏi đáp 2. Giữ đủ 10 mục, rút phần mở rộng.

## 7. Tiến độ theo mốc và phân công

Ngày bắt đầu, hạn nộp và tên người phụ trách: `[CHƯA CHỐT]`. Ba mốc dưới đây theo thứ tự phụ thuộc, tương ứng ba tuần nếu còn đủ thời gian; có thể gộp lịch, giữ các điều kiện nghiệm thu.

| Mốc | Phụ trách, review | Việc làm | Đầu ra để chuyển mốc |
|---|---|---|---|
| 1 — nền và chốt demo | A; B review | Ôn ABI/NX/libc; bài tập chung; tải challenge đúng kiến trúc và kiểm tra bảo vệ | Binary chạy được; bảng môi trường; phân tích lỗi, cách gọi thư viện và phạm vi demo đã chốt |
| 2 — phân tích và bằng chứng | A: demo; B: sơ đồ/slide; C: CVE/nguồn | Đo offset, theo dấu đối số và thư viện; kiểm chứng CVE; làm slide nháp | Log/ảnh S05; demo đạt mục tiêu hai lần liên tiếp; bản nháp đủ 10 mục |
| 3 — hoàn thiện và tập nói | A/B/C; review chéo | Soát phát biểu về CWE, NX và ASLR; chuẩn bị dự phòng; tập hỏi đáp | 14 slide hoàn chỉnh; nói 20–30 phút; checklist nộp hoàn tất |

Mỗi lần cập nhật tiến độ ghi vào [../ROADMAP.md](../ROADMAP.md): việc xong, bằng chứng, vướng mắc, bước tiếp. Chỉ đánh dấu hoàn thành khi có đầu ra S05 tương ứng.

## 8. Tài liệu chính

- [MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html), [CWE-787](https://cwe.mitre.org/data/definitions/787.html): phân loại lỗi nền.
- [ROP Emporium split](https://ropemporium.com/challenge/split.html), [guide](https://ropemporium.com/guide.html): challenge và các khái niệm ROP/NX.
- [x86-64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI): quy ước gọi hàm; đọc lại phần truyền tham số và căn lề khi triển khai demo.
- [GCC instrumentation](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html), [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html): stack protector và công cụ phát hiện lỗi khi kiểm thử.
- Nguồn CVE và bài direct ret2libc: xem mục 4; kiểm tra lại trước khi đưa lên slide.
