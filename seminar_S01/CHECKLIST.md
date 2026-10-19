# Checklist mini seminar S01

- [x] Mọi mục 1–10 của đề đều có vị trí trong slide hoặc phần nói.
- [x] Có bối cảnh sử dụng của lỗ hổng (mục 1).
- [x] CWE-121 được giải thích, gắn với đúng vùng đệm stack của ca minh họa và nêu liên hệ với chủ đề S01.
- [x] CVE có phần biện pháp khắc phục; không tái hiện khai thác CVE.
- [x] Demo chạy trong môi trường được cấp phép, cô lập, an toàn.
- [x] Có sơ đồ input → sink → ghi vượt → hậu quả, cùng bằng chứng trong code/binary.
- [x] CVE có sản phẩm, nguyên nhân, tác động, điều kiện và bản vá; nguồn tham khảo rõ.
- [ ] Demo challenge chạy được ít nhất hai lần liên tiếp trên môi trường đã chốt. *(exploit.py đã chạy ra flag 1 lần; cần chạy thêm 1 lần nữa cho đủ ≥2 lần liên tiếp)*
- [x] Ảnh minh chứng có chú thích giải thích điều ảnh chứng minh. *(evidence/README.md)*
- [x] Phân biệt crash với bằng chứng điều khiển luồng thực thi. *(slide 8: "Well done"+SIGSEGV vs slide 9: flag)*
- [x] Có mã sửa lỗi và phân tích canary/NX/ASLR/PIE theo binary cụ thể. *(slide 12 + notes/bai_tap_3_doan_ma)*
- [ ] Tổng thời gian có hỏi đáp nằm trong 20–30 phút. *(cần tập bấm giờ)*
- [ ] Có phương án dự phòng (video/ảnh + lệnh) nếu demo trực tiếp lỗi. *(đã có bộ ảnh 01–05 trong evidence/; nên chuẩn bị nói theo ảnh nếu demo lỗi)*
- [ ] Mọi nguồn/tác giả/URL trên slide đã được tra cứu lại. *(CVE-2015-7547 đã tra NVD; còn MITRE CWE, ROP Emporium, GCC/Clang links chưa tra lại)*
