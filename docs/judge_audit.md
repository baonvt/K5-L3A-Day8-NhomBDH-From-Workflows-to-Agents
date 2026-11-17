# Judge audit — replay công khai

Lệnh: `python -m lab9.judge --csv <file> --audit 5`. Nhãn dương tính là `FAIL`; floors là κ ≥ 0.6, precision ≥ 0.8, recall ≥ 0.7.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có | Dùng để gợi ý/triage tone, không gate tiền hay approval |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không | Loại khỏi gate: bỏ sót 21/30 lỗi do sai tiền hoặc xưng hô |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 1 | tone H-008 | PASS | FAIL | Người | “Em … nha” quá suồng sã; thêm tiêu chí xưng hô và mức thân mật vào rubric. |
| 2 | tone H-029 | PASS | FAIL | Người | Câu “không cần nhắn thêm” mang giọng ra lệnh; chấm hành động/cách nói thay vì chỉ từ mở đầu lịch sự. |
| 3 | tone H-042 | FAIL | PASS | Người | Cập nhật ngắn, rõ và đủ thông tin; rubric không được bắt buộc câu xin lỗi trong mọi trường hợp. |
| 4 | tone H-051 | FAIL | PASS | Người | Từ “refund” được CS LogiX cho phép; thêm danh sách từ tiếng Anh được chấp nhận. |
| 5 | tone H-081 | FAIL | PASS | Judge | Người gán nhãn đọc nhầm ticket; sửa nhãn gốc và thêm bước đối chiếu ticket khi audit. |
| 6 | helpful HL-015 | PASS | FAIL | Người | Reply nói 55.000đ trong khi ledger 40.000đ; judge không có kiểm tra số tiền bằng code. |
| 7 | helpful HL-047 | PASS | FAIL | Người | “Ok bạn … nhé” sai xưng hô; bổ sung tiêu chí giọng điệu, dù riêng lỗi này không giải thích được recall rất thấp. |
| 8 | helpful HL-020 | PASS | FAIL | Người | Reply nói 90.000đ nhưng ledger là 120.000đ; bắt buộc code so reply với ledger. |
| 9 | helpful HL-091 | PASS | FAIL | Người | Sai xưng hô; thêm ví dụ xưng hô không phù hợp vào rubric và tập hiệu chỉnh. |
| 10 | helpful HL-100 | PASS | FAIL | Người | Reply sai tiền; tiếp tục dùng grader code làm chuẩn cho số tiền. |

## Kết luận
- `tone_ok`: κ=.757, P=.857, R=.800; đạt sàn trên replay. Dùng để sắp xếp nội dung cần review, không làm quyết định tiền/approval.
- `helpful`: confusion `{tp: 9, fp: 0, fn: 21, tn: 70}`. P=1.0 che lấp recall=.3; Rogan–Gladen điều chỉnh tỉ lệ lỗi quan sát .09 thành .30 (sens=.3, spec=1.0). Loại khỏi gate.
- Bằng chứng chỉ là judge replay trên CSV public, chưa phải tập held-out có nhãn người mới. Mọi quyết định số tiền và approval vẫn do grader code kiểm tra.
