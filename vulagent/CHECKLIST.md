# Checklist VulAgent

Xếp theo tiêu chí chấm ở [REQUIREMENTS.md](REQUIREMENTS.md); trạng thái chi tiết ở [PLAN.md](PLAN.md) §0.

## Tiêu chí 1–2 (4đ): hiểu bài toán, giải thích phương pháp
- [ ] Nhóm diễn giải được vai trò từng giai đoạn bằng một trace thật (cặp 71/72).
- [ ] Slide có bảng khác biệt arXiv ↔ ACL và lý do lấy ACL làm mốc.

## Tiêu chí 3 (5đ): tái hiện + demo + biện luận
- [x] Pipeline của nhóm chạy trọn một cặp bằng model thật, lưu trace (2026-11-23, Haiku, idx 71/72).
- [x] Schema, lỗi parse → `unknown`, ca thiếu context được xử lý rõ (có test).
- [x] Metric kiểm bằng selftest và khớp số công bố khi tính lại từ output của tác giả (Qwen3 SEVEN).
- [x] RQ1: VulAgent trên SEVEN đủ 166 mẫu, 1 lượt (2026-11-24).
- [ ] RQ1: baseline CoT cùng model, cùng ID.
- [ ] RQ1: PrimeVul (toàn bộ hoặc tập con có quy tắc).
- [x] RQ2: bảng so backend (Qwen3 công bố tính lại + Haiku) — `docs/error_analysis.md` §1.
- [x] RQ3: SEVEN không context, 166 mẫu ([error_analysis §6](docs/error_analysis.md)).
- [ ] RQ3 (a): giữ nguyên phần đầu pipeline, chỉ chạy lại Pruner + Validator với context rỗng.
- [x] RQ4: bảng per-CWE — `docs/error_analysis.md` §2.
- [ ] RQ5 và ablation ACL: ghi rõ làm hay không và vì sao.
- [ ] Kịch bản demo + video dự phòng + một ca candidate bị guard chặn.
- [ ] Error analysis ≥ 3 ca (TP, FP bị loại, FN) + ưu/nhược + threats to validity.
- [ ] Báo cáo nêu phần nhóm tự hiện thực, phần dùng lại, mọi khác biệt với bài (model, số lượt, tập mẫu).

## Tiêu chí 4 (1đ): cải tiến
- [x] Phân loại 42 FN theo khâu, chốt ba chỗ sửa — `docs/error_analysis.md` §3 (đọc tay 8 ca + thống kê toàn bộ).
- [x] Ghi giả thuyết + tiêu chí thành công trước khi chạy — `PLAN.md` §0.2.
- [x] Hiện thực hai prompt kiểm chứng tĩnh, giữ candidate theo ID, tăng trần Pruner và ghi `stop_reason`.
- [x] Hoàn tất pilot 28 FN + 28 TN theo danh sách cố định và chấm điều kiện mở rộng.
- [x] Ghi nhận kết quả âm trước lượt 166 mẫu vì 19 TN chuyển sai, vượt ngưỡng 2.

## Tái lập và an toàn
- [ ] Tập mẫu, model, prompt hash, ngày chạy, chi phí của mỗi lượt nằm trong `run_meta.json`/manifest.
- [ ] Không có API key/token trong repo hay log.
- [ ] Người khác clone đúng commit, dùng key riêng, chạy theo README và tạo lại bảng từ kết quả thô.
