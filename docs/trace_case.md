# Trace case: từ trace tới quyết định sai đầu tiên

## Case đã đối chiếu

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run `E-seeded_regression-20261117-1704` |
| Triệu chứng | `TrialPass` fail vì agent trả `resolved` và ledger ghi 20.000đ, trong khi nhãn yêu cầu `denied` và 0đ. |
| Bước sai đầu tiên | Event 3 `model_override`: `{"delay_days": 5}`. |
| Vì sao là bước đầu tiên | Event 1 chỉ handoff các tool đọc; event 2 đọc order O-202 từ DB. Hai bước này chưa thay đổi dữ kiện. Event 3 ghi đè delay trong DB bằng số ngày ở ticket; event 4 vì thế tạo quote 20.000đ thay vì 0đ. |
| Failure mode | FM-03 `ticket_trust`. |
| Đối chứng | `fixed C-002@11` giữ nguyên order facts ở event 2, không có `model_override`; event 3 quote 0đ, ledger 0đ, status `denied`. |
| Regression test | `tests/test_lab9_trace_regression.py::test_ticket_override_is_the_first_wrong_step`; fail trên seeded regression, pass trên fixed. |
| Chưa chắc chắn | Trace chứng minh agent dùng số ngày trong ticket và host đã ghi 20.000đ; riêng trace không chứng minh vì sao người gửi ticket đưa số 5 ngày. |

Run ID của report có thể trùng giữa nhiều lần chạy cùng ngày và eval-set hash vì các item/seed cố định; từng trial được tái tạo từ shape, claim và seed.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
