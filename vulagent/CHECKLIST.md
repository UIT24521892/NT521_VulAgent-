# Checklist VulAgent

- [ ] Nhóm diễn giải được vai trò từng giai đoạn bằng một ca mã nguồn thật.
- [ ] Prototype chạy trọn một cặp vulnerable/fixed và lưu bằng chứng trung gian. (2026-11-15: đã chạy cặp SEVEN idx 71/72 bằng **phát lại output công bố**, trace ở `results/raw/`; còn thiếu lượt chạy bằng model của nhóm.)
- [x] Schema, parse error và trường hợp thiếu context được xử lý rõ. (2026-11-15: lỗi LLM/parse → `unknown`, có test; `--skip context` cho ca thiếu context — chưa chạy với model thật.)
- [ ] Tập mẫu, phiên bản paper/metric, cấu hình và ngày chạy được ghi lại.
- [ ] Metric được kiểm tra bằng tay trên mẫu nhỏ; baseline dùng cùng tập mẫu.
- [ ] Có một ablation đúng điều kiện so sánh và ít nhất 3 ca error analysis.
- [ ] Báo cáo nêu phần nhóm thực sự hiện thực, phần dùng lại và giới hạn kết quả.
- [ ] Không có API key/token trong repo hay log.
- [ ] Người khác clone đúng commit, dùng key riêng, chạy theo README và tạo lại bảng từ kết quả thô.
