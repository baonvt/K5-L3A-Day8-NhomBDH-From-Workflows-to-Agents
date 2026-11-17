# Team

## Thông tin nhóm

- Tên nhóm: NhomBDH
- Lớp: L3A
- Repo nhóm: `K5-Day8-NhomBDH-From-Workflows-to-Agents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo hiện tại: https://github.com/baonvt/K5-Day8-NhomBDH-From-Workflows-to-Agents, nhánh `main`, mã shape chốt `bbf1e76`.
- Tên repo cần đổi theo [SUBMISSION.md](SUBMISSION.md): `K5-L3A-DAY08-NhomBDH-FromWorkflowsToAgents`.

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Nguyễn Võ Thái Bảo | 2A202603638 | baonguyenvothai@gmail.com | https://github.com/baonvt | Workflow + Evidence/Benchmark |
|   2 | Nguyễn Trường Duy | 2A202603589 | ntduy279@gmail.com | https://github.com/Dizo279 | Single ReAct |
|   3 | Đoàn Văn Hiệp | 2A202603565 | hiep24042002@gmail.com | https://github.com/hiep0405 | Orchestrator + Handoff/Trace |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Võ Thái Bảo | Workflow + benchmark/crash + Lab9 evaluation | cb1cb3f, 19bb28e | `src/tests/test_workflow_shape.py`, `src/tests/test_lab9_trace_regression.py` |
| Nguyễn Trường Duy | Single ReAct + ADR/research | 67a3a24 | `src/tests/test_single_shape.py` |
| Đoàn Văn Hiệp | Orchestrator + handoff/trace | bbf1e76 | `src/tests/test_orchestrator_handoff_trace.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603638_NguyenVoThaiBao

### Phần việc phụ trách

- Triển khai Shape A (Workflow).
- Thiết lập báo cáo thực nghiệm benchmark và crash suite.

### Đóng góp cụ thể

- Hoàn thiện mã nguồn `src/lab8/shapes/workflow.py`.
- Viết test `src/tests/test_workflow_shape.py`.
- Sinh các file bằng chứng `src/reports/benchmark.json` và `src/reports/crash.json`.

### Bằng chứng

- Commit: `cb1cb3f`
- Test: `test_workflow_shape.py`

## 2A202603589_NguyenTruongDuy

### Phần việc phụ trách

- Triển khai Shape B (Single ReAct Agent).
- Quản lý vòng lặp ReAct và giới hạn công cụ chỉ đọc.

### Đóng góp cụ thể

- Hoàn thiện mã nguồn `src/lab8/shapes/single.py`.
- Viết test `src/tests/test_single_shape.py`.
- Cập nhật tài liệu kỹ thuật ADR và research card.

### Bằng chứng

- Commit: `67a3a24`
- Test: `test_single_shape.py`

## 2A202603565_DoanVanHiep

### Phần việc phụ trách

- Triển khai Shape C (Orchestrator + Read-only Investigators).
- Đảm bảo chuẩn giao tiếp Handoff v1 và Trace Contract v1.
- Xử lý Crash safety và tính lũy kế (idempotency).

### Đóng góp cụ thể

- Hoàn thiện mã nguồn `src/lab8/shapes/orchestrator.py`.
- Viết test `src/tests/test_orchestrator_handoff_trace.py`.
- Biên soạn nội dung so sánh kiến trúc trong `report/team/group_report.md`.

### Bằng chứng

- Commit: `bbf1e76`
- Test: `test_orchestrator_handoff_trace.py`
- Báo cáo cá nhân: `report/team/2A202603565_DoanVanHiep.md`
