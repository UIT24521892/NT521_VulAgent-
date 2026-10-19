# Yêu cầu của đề — Mini seminar S05

## Chủ đề được đổi ngày 2026-10-19

Mô tả do người dùng cung cấp:

> Phân tích kỹ thuật điều khiển luồng thực thi để sử dụng lại các hàm có sẵn trong thư viện hệ thống, thường trong bối cảnh hạn chế hoặc không thực thi được mã trên stack. Làm rõ mối liên hệ với lỗi tràn bộ đệm và cơ chế bảo vệ.

Tên làm việc trong kế hoạch: **S05 — Return-to-libc (ret2libc)**. Trọng tâm là kỹ thuật tái sử dụng mã thư viện, mối liên hệ với buffer overflow và tác dụng/giới hạn của các cơ chế bảo vệ.

## Quy định cấu trúc bài trình bày

Các yêu cầu chung do nhóm cung cấp ngày 2026-10-05 được trình bày đầy đủ dưới đây và áp dụng cho chủ đề S05. Tài liệu này là nguồn yêu cầu độc lập của S05.

Slide thuyết trình của mỗi nhóm được khuyến nghị trình bày theo cấu trúc sau:

1. Giới thiệu lỗ hổng và bối cảnh sử dụng.
2. Trình bày nguyên lý, điều kiện phát sinh và các dạng phổ biến của lỗ hổng.
3. Xác định, giải thích CWE tương ứng và mối liên hệ với chủ đề được phân công.
4. Phân tích vị trí và nguyên nhân lỗ hổng trong mã nguồn hoặc binary/chương trình mục tiêu.
5. Giải thích nguyên lý và chuỗi khai thác ở mức phù hợp.
6. Phân tích ít nhất một CVE thực tế có liên quan, gồm sản phẩm bị ảnh hưởng, nguyên nhân, tác động, điều kiện khai thác và biện pháp khắc phục.
7. Demo một challenge CTF thuộc mảng Pwnable trong môi trường được cấp phép, cô lập và an toàn.
8. Trình bày biện pháp khắc phục, phòng ngừa và các cơ chế bảo vệ liên quan.
9. Phân tích điều kiện, giới hạn và các yếu tố ảnh hưởng đến khả năng khai thác thành công.
10. Nêu bài học rút ra và kết luận.

Phần phân tích CVE chỉ yêu cầu nghiên cứu và trình bày thông tin; không bắt buộc reproduce hoặc tái hiện việc khai thác CVE.

## Phân bổ thời gian gợi ý (20–30 phút)

- 5–6 phút: kiến thức nền tảng và CWE.
- 3–4 phút: phân tích CVE thực tế.
- 8–12 phút: phân tích mã nguồn/binary và demo CTF.
- 3–5 phút: khắc phục, phòng ngừa, giới hạn và kết luận.
- 2–3 phút: trả lời câu hỏi.

Ngày seminar và tên thành viên: `[CHƯA CHỐT]`. Chưa có thông tin thay đổi yêu cầu chung hoặc thời lượng.
