# Báo cáo cá nhân — Nguyễn Võ Thái Bảo

## 1. Thông tin thành viên

- Họ tên: Nguyễn Võ Thái Bảo
- MSSV: 2A202603638
- Email: baonguyenvothai@gmail.com
- GitHub: https://github.com/baonvt

## 2. Phần việc phụ trách

- Triển khai Shape A — workflow xác định.
- Thêm test cho workflow.
- Chạy benchmark public và crash suite, lưu report do công cụ sinh.

## 3. Đóng góp cụ thể

- Hoàn thiện `src/lab8/shapes/workflow.py`: đọc claim qua tool allowlist, kiểm tra quyền sở hữu order, tính quote từ dữ liệu order/policy có cấu trúc và giao quote đầy đủ cho `durability.issue_refund`.
- Không dùng ticket để quyết định số ngày trễ hoặc số tiền; truyền `crash_at` tới host và để crash exception truyền ra.
- Thêm `src/tests/test_workflow_shape.py` cho ticket khai sai ngày trễ, quote đầy đủ khi order đã có refund trước, và trace hợp lệ ở nhánh thiếu order.
- Chạy benchmark bốn shape và crash suite; lưu `src/reports/benchmark.json`, `src/reports/crash.json`.

## 4. Bằng chứng

- Commit kỹ thuật: `cb1cb3f`.
- Test thêm: `src/tests/test_workflow_shape.py`; workflow student slice đạt 62/62.
- Benchmark: run tiêu biểu `R-workflow-C-001-s11`; workflow đạt 70/70 trial, pass rate `1.000`, pass^5 `1.000`, seed variance `0.000000`, cost/success `27.86` VND mô phỏng và mean steps `3.50`.
- Crash suite: `20/20` trong `src/reports/crash.json`.
- Cổng host toàn nhóm: `63 passed`; student matrix: `248 passed`.

## 5. Công cụ AI đã dùng

Đã dùng Codex để đọc hướng dẫn/contract, hỗ trợ triển khai và rà soát test. Tự kiểm bằng cách chạy pytest, đối chiếu kết quả với luật trong `docs/business_rules.md` và `docs/contracts.md`, rồi sinh benchmark/crash report bằng CLI của lab. Không sửa tay JSON report.

## 6. Tự đánh giá

Workflow đạt toàn bộ trial public với chi phí mô phỏng thấp nhất trong bốn shape. Cách làm giữ việc tính tiền và ghi ledger ở code/host, giúp flow dễ kiểm tra và tránh tin vào nội dung ticket. Kết quả hiện chỉ phản ánh 14 claim public và MockLLM; cần dựa thêm vào hidden grade trước khi kết luận về dữ liệu ngoài bộ public.

## 7. Bổ sung Lab 9 — evaluation và failure analysis

- **Phần việc:** tích hợp overlay Lab 9 trên nhánh `starter/d09`; hoàn thiện taxonomy FM-01–FM-09, eval set tách nhãn v1/v2, grader tiền/reply, bootstrap, gate, slices và integrity traps; cập nhật Eval Card, PRD v1.1, judge audit và regression trace case.
- **Commit/test:** `19bb28e`; `src/tests/test_lab9_trace_regression.py` cùng bộ `test_lab9_*`.
- **Tự kiểm:** `lab9.smoke` PASS; `evalset --check` và `evalset --v2` có 0 problem; student tests 16/16 core + 14/14 advanced; host suite 66 passed. Baseline `E-swarm-20261117-1704`; fixed qua gate; seeded regression bị chặn ở `pass_rate` với Δ −0.271, CI [−0.500, −0.057].
- **Advanced:** baseline v2 `E-swarm-20261117-1330`; A/A Δ=0; mutation 3/3 với 0 false alarm; bốn trap công khai đều bị gate chặn.
- **Công cụ AI:** dùng Codex để đọc kỹ README/Markdown, hỗ trợ triển khai grader/statistics/gate và điền tài liệu từ kết quả script. Kết quả được kiểm bằng smoke, pytest, CLI eval/gate và đối chiếu report; JSON report chỉ được sinh bằng script, không sửa tay.
- **Giới hạn:** MockLLM, 14 public + 14 adversarial item, 5 seed; judge replay public; swarm không ghi event reply nên metric FM-08 không chứng minh độ chính xác văn bản của swarm.
