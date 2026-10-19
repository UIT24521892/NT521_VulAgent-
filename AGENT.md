# AGENT.md — Hướng dẫn cho trợ lý AI xuyên suốt dự án NT521

Đọc file này đầu tiên ở mọi phiên làm việc. Ngôn ngữ làm việc và tài liệu: **tiếng Việt** (giữ nguyên thuật ngữ kỹ thuật tiếng Anh, tên lệnh, tên file).

## 1. Dự án gồm hai sản phẩm tách biệt

Nhóm 3 sinh viên, môn **NT521 – Lập trình khai thác lỗ hổng**. Hai phần dùng chung một cách phân tích (source → sink → điều kiện → guard → kết luận có bằng chứng) nhưng **là hai sản phẩm riêng, không trộn tài liệu, mã hay kết quả**.

| Phần | Thư mục | Sản phẩm | Trạng thái |
|---|---|---|---|
| Mini seminar **S05 – Return-to-libc (ret2libc)** | [seminar_S05/](seminar_S05/) | Slide 12–14 trang + demo CTF + CVE, 20–30 phút | **ĐANG LÀM (đổi chủ đề ngày 2026-10-19)** |
| Đề tài **VulAgent** – phát hiện lỗ hổng bằng lập và kiểm chứng giả thuyết | [vulagent/](vulagent/) | Mã pipeline, dữ liệu đánh giá, báo cáo, slide | Chưa bắt đầu; chỉ làm khi nhóm chuyển trọng tâm |

**Quy tắc trọng tâm:** trừ khi người dùng nói rõ, chỉ làm việc trong `seminar_S05/`. Không tạo mã/thư mục triển khai trong `vulagent/` cho tới khi trọng tâm được chuyển (ghi vào [ROADMAP.md](ROADMAP.md)). Một ngoại lệ hợp lý: ghi chú nối hai phần đặt ở `notes/` của phần phát sinh và trỏ sang phần kia, không copy.

**S05 là phạm vi làm việc độc lập:** chọn kiến thức, challenge và CVE theo mức độ liên quan trực tiếp đến ret2libc. Mọi kết quả, offset, slide và bằng chứng phải được xác nhận cho chính S05; không lấy chủ đề seminar trước làm cơ sở chọn nội dung.

## 2. Bản đồ thư mục

```
project_521/
├── AGENT.md            # file này – quy tắc xuyên suốt
├── CLAUDE.md           # trỏ tới AGENT.md để Claude Code tự nạp
├── ROADMAP.md          # kế hoạch tổng + trạng thái hiện tại + nhật ký
├── seminar_S05/        # PHẦN 1 – mini seminar đang làm
│   ├── README.md       #   tổng quan, quyết định đã chốt
│   ├── REQUIREMENTS.md #   yêu cầu nguyên văn của đề seminar (nguồn chuẩn)
│   ├── PLAN.md         #   kế hoạch theo 10 mục của đề + kịch bản demo + lịch
│   ├── KNOWLEDGE.md    #   kiến thức cần học cho S05
│   ├── CHECKLIST.md    #   checklist nộp bài và tự kiểm tra
│   ├── slides/         #   slide và nguồn slide
│   ├── demo/           #   binary challenge, script/lệnh demo, kịch bản dự phòng
│   ├── cve/            #   ghi chú CVE, advisory, bản vá
│   ├── evidence/       #   ảnh minh chứng + chú thích (ảnh 1–6)
│   └── notes/          #   phân tích thủ công, bài tập 3 đoạn mã, nháp
├── vulagent/           # PHẦN 2 – đề tài chính
│   ├── README.md
│   ├── PLAN.md         #   giai đoạn A–D, thực nghiệm, lịch
│   ├── KNOWLEDGE.md    #   kiến thức cần học cho VulAgent
│   ├── CHECKLIST.md
│   └── references/     #   tài liệu gốc của nhóm (prompt_nhom_3.md, kien_thuc_can_hoc.md)
└── _archive/           # bản gốc đã tách; không sửa, không dùng làm nguồn chính
```

Khi cần thư mục mới, đặt đúng phần của nó và cập nhật bản đồ này. Mã/dữ liệu VulAgent (`configs/`, `src/`, `scripts/`, `tests/`, `results/`, `experiment_manifest.yaml`…) tạo trong `vulagent/` theo mục 7 của [vulagent/references/prompt_nhom_3.md](vulagent/references/prompt_nhom_3.md) khi bắt đầu phần đó.

Các thư mục sản phẩm `slides/`, `demo/`, `cve/`, `evidence/`, `notes/` của S05 tạo khi bắt đầu thực hiện phần tương ứng; bản đồ trên mô tả vị trí quy ước.

## 3. Cách làm việc mỗi phiên

1. Đọc `AGENT.md` → [ROADMAP.md](ROADMAP.md) (trạng thái hiện tại) → `PLAN.md` và `CHECKLIST.md` của phần đang làm.
2. Làm việc tuần tự theo kế hoạch; mỗi việc phải tạo ra **đầu ra kiểm tra được** (file, ảnh, lệnh chạy được), không dừng ở đề xuất.
3. Cuối phiên: tick checklist, thêm một dòng vào "Nhật ký" trong [ROADMAP.md](ROADMAP.md) (ngày, việc đã xong, bằng chứng ở đâu, vướng mắc, bước tiếp theo), nêu rõ cho người dùng: file đã đổi, lệnh đã chạy, kết quả thực tế, điều chưa xác minh.
4. Không chắc về yêu cầu của đề hoặc hạn nộp → hỏi người dùng; điền placeholder `[CHƯA CHỐT: …]` thay vì tự bịa.

## 4. Quy tắc trung thực và bằng chứng (bắt buộc)

- **Không bịa**: số đo, trích dẫn, kết quả chạy, screenshot, offset, output debugger, hay claim "đã tái hiện/khai thác thành công" khi chưa có bằng chứng thật trong `evidence/` hoặc `results/`.
- **Mức bằng chứng tách bạch** (S05): "có ghi vượt", "chương trình crash", "đã thay đổi địa chỉ trả về", "gọi được hàm thư viện với đối số đúng", "đạt mục tiêu challenge" là các nhận định khác nhau. Chỉ phát biểu điều đã kiểm chứng. Phân biệt gọi libc qua PLT với nhảy trực tiếp vào libc; không suy ra đã vượt ASLR chỉ từ demo có NX.
- Sơ đồ stack **minh họa** không dùng để khẳng định offset của binary thật; offset phải **đo trên binary đang dùng**.
- Nguồn tham khảo (tác giả, năm, URL) tên trong [vulagent/references/kien_thuc_can_hoc.md](vulagent/references/kien_thuc_can_hoc.md) được nêu từ trí nhớ, **chưa tra cứu**: kiểm tra lại trước khi đưa vào slide/báo cáo.
- Với VulAgent: số trích từ paper là "tham chiếu lịch sử", không phải kết quả chạy cùng điều kiện; ghi rõ phiên bản paper (ACL 2026 là mốc chính, arXiv 2509.11523 để đối chiếu).
- Thông tin CVE, phạm vi phiên bản, bản vá: xác nhận theo advisory của nhà cung cấp; các bản phân phối có thể backport.

## 5. An toàn và đạo đức

- Chỉ phân tích/chạy challenge trong **môi trường cô lập, được phép** (VM Kali qua UTM, challenge CTF như ROP Emporium). Không nhắm vào hệ thống thật.
- **CVE chỉ nghiên cứu và trình bày**, không tái hiện khai thác, không viết exploit hoàn chỉnh cho phần mềm đang chạy ngoài thực tế.
- Không commit hoặc ghi log **API key/token/`.env`**. Repo VulAgent gốc có thể chứa key nhúng cứng: không dùng, không in giá trị.
- Không tải/chạy mã hoặc dữ liệu chưa kiểm tra nguồn, giấy phép; không ghi đè dữ liệu gốc.
- Hành động khó hoàn tác (xóa, ghi đè, gọi API tốn phí, gửi nội dung ra ngoài) → xác nhận trước.

## 6. Vai trò nhóm 3 người (để gắn người phụ trách trong bảng tiến độ)

| Vai trò | S05 | VulAgent |
|---|---|---|
| **A** – lỗ hổng & seminar | Chính: stack/ABI, ret2libc, debugger, phân tích và demo | Nắm luồng source–sink–guard và ý chính pipeline |
| **B** – phương pháp & hiện thực | Sơ đồ gọi thư viện, slide, review điều kiện và bảo vệ | Chính: paper, CFG/data-flow, agent, schema, mã pipeline |
| **C** – dữ liệu & đánh giá | CVE, nguồn tham khảo và phản biện chéo | Chính: PrimeVul/SVEN, metric, baseline, ablation, error analysis |

Mọi mốc cần review chéo ít nhất một người khác. Tên thành viên: `[CHƯA CHỐT: A=…, B=…, C=…]`.

## 7. Quy ước tài liệu

- Markdown, tiêu đề rõ, link tương đối giữa các file; checklist dạng `- [ ]` / `- [x]`.
- Ảnh minh chứng: `seminar_S05/evidence/NN_mo_ta.png` kèm dòng chú thích (ảnh chứng minh điều gì, lệnh nào, ngày nào) trong `evidence/README.md`.
- Mỗi lần chạy demo/thí nghiệm ghi: lệnh, môi trường (`uname -m`, phiên bản công cụ), ngày, kết quả.
- Đổi tên/di chuyển file thì sửa link và bản đồ ở mục 2.
- Đừng thêm tài liệu thừa; sửa file hiện có nếu đã có chỗ phù hợp.

## 8. Tiêu chuẩn hoàn thành

- **S05:** mọi mục 1–10 của đề có chỗ trong slide; giải thích được ret2libc, quan hệ với buffer overflow và bảo vệ; demo tái sử dụng hàm thư viện chạy được ít nhất hai lần liên tiếp trên môi trường đã chốt; ảnh có chú thích; tổng thời gian 20–30 phút; checklist trong [seminar_S05/CHECKLIST.md](seminar_S05/CHECKLIST.md) xong.
- **VulAgent:** người khác clone đúng commit, dùng key riêng, chạy theo README và tạo lại bảng từ kết quả thô; xem [vulagent/CHECKLIST.md](vulagent/CHECKLIST.md).
