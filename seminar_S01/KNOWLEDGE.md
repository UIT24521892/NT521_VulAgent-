# Kiến thức cần học cho S01

Học theo thứ tự ưu tiên. Cả nhóm học phần nền chung; người phụ trách (A) đào sâu debugger/CVE.

| Ưu tiên | Chủ đề | Cần tự làm được | Dùng ở đâu |
|---|---|---|---|
| 1 | C căn bản: mảng, con trỏ, `char[]`, `sizeof`, độ dài chuỗi, ký tự `\0` | Tính dung lượng vùng đệm và lượng dữ liệu có thể ghi; chỉ ra lỗi off-by-one | Phân tích mã, sơ đồ bộ nhớ |
| 1 | Bộ nhớ tiến trình: stack frame, biến cục bộ, heap, địa chỉ trả về | Vẽ stack frame **minh họa**, rồi xác nhận bố cục thực tế trong binary | Phân tích binary |
| 1 | Source–sink–guard | Chỉ ra input, sink, mọi phép kiểm tra trên đường tới sink; guard có chặn mọi đường không | Trọng tâm cả seminar |
| 1 | CWE-121 và CWE-787 | Phân biệt tràn bộ đệm **trên stack** với ghi ngoài biên tổng quát; phân biệt CWE với CVE | Mục 3 của đề |
| 2 | CFG, data flow, call graph, reachability, feasibility | Vẽ CFG hàm nhỏ có `if`/`return`; nêu một đường có trên CFG nhưng không thực thi được | Điều kiện khai thác, mục 9 |
| 2 | Debugger và binary: kiến trúc, thanh ghi, stack, disassembly | Dùng GDB quan sát hàm lỗi, trạng thái trước/sau input; không suy kết quả chỉ từ crash | Demo |
| 2 | Stack canary, NX, ASLR, PIE; kiểm tra biên; AddressSanitizer | Mỗi cơ chế tác động ở đâu và giới hạn; đề xuất sửa mã tận gốc | Mục 8 |

Nội dung ưu tiên 3 (CWE-125/416/476/78/862, Joern/CPG, metric…) thuộc phần VulAgent: xem [../vulagent/KNOWLEDGE.md](../vulagent/KNOWLEDGE.md).

## Bài tập đầu tiên

Xem [PLAN.md mục 2](PLAN.md#2-học-nền-theo-thứ-tự).

## Tự kiểm tra trước khi lên slide

- [ ] Giải thích được vì sao crash ≠ điều khiển được luồng thực thi.
- [ ] Nói được offset của binary đang dùng và cách đo (không lấy từ sơ đồ minh họa).
- [ ] Nói được canary/NX/ASLR/PIE của binary đang bật hay tắt, và mỗi cái chặn bước nào.
- [ ] Phân biệt CWE-121 và CWE-787; phân biệt CWE và CVE.
