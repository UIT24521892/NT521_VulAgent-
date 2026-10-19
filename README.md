# NT521 — VulAgent và mini seminar S05

Repository học phần **NT521 – Lập trình khai thác lỗ hổng**, gồm hai sản phẩm:

| Phần | Vai trò | Nội dung | Thư mục |
|---|---|---|---|
| **VulAgent** | **Đồ án chính của môn học** | Phát hiện lỗ hổng mã nguồn bằng quy trình lập và kiểm chứng giả thuyết | [vulagent/](vulagent/) |
| **S05 — Return-to-libc (ret2libc)** | **Mini seminar** | Tìm hiểu kỹ thuật tái sử dụng hàm thư viện, liên hệ với buffer overflow và các cơ chế bảo vệ | [seminar_S05/](seminar_S05/) |

## Đồ án chính — VulAgent

Mục tiêu là nghiên cứu phương pháp VulAgent, triển khai pipeline và thực hiện đánh giá khả năng phát hiện lỗ hổng mã nguồn. Sản phẩm dự kiến gồm mã nguồn, dữ liệu và kết quả thí nghiệm, báo cáo và slide.

Hiện đã có tài liệu định hướng và kế hoạch; chưa triển khai mã nguồn. Xem [tổng quan](vulagent/README.md), [kế hoạch](vulagent/PLAN.md) và [checklist](vulagent/CHECKLIST.md).

## Mini seminar S05 — Return-to-libc

S05 là bài mini seminar với thời lượng **20–30 phút**, gồm phần trình bày lý thuyết, demo CTF và phân tích một CVE liên quan đến chủ đề ret2libc.

Đây là phần đang được ưu tiên thực hiện. Hiện đã có bộ tài liệu kế hoạch; chưa có kết quả demo hoặc slide S05. Xem [tổng quan](seminar_S05/README.md), [yêu cầu](seminar_S05/REQUIREMENTS.md), [kế hoạch](seminar_S05/PLAN.md) và [checklist](seminar_S05/CHECKLIST.md).

## Tài liệu chung

- [ROADMAP.md](ROADMAP.md): tiến độ, kế hoạch tổng và nhật ký dự án.
- [AGENT.md](AGENT.md): quy tắc làm việc và tổ chức tài liệu.
- [seminar_S01/](seminar_S01/): tài liệu seminar chủ đề trước, được giữ lại để tham khảo.
- [_archive/](_archive/): tài liệu gốc lưu trữ.
