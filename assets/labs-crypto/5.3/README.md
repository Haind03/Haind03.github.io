# Lab 5.3: Timing attack trên so sánh MAC

Script giải cho Bài 5.3. Server kiểm tag bằng vòng so sánh từng byte dừng sớm (giống toán tử `==`), làm rò rỉ thời gian theo số byte khớp. Kẻ tấn công đo thời gian và khôi phục tag từng byte mà không biết key.

## Chạy

```bash
python3 solve.py
```

Chỉ dùng thư viện chuẩn (`hmac`, `hashlib`, `os`, `time`). Để tín hiệu thời gian ổn định trong demo, chi phí xử lý mỗi byte được mô phỏng bằng busy-wait; cơ chế tấn công giống hệt thực tế, chỉ khác độ nhiễu. Lab khôi phục 6 byte đầu của tag (khoảng 10 tới 12 giây). `transcript.txt` là output thật.

## File

- `solve.py`: oracle so sánh không hằng thời gian, bộ đo thời gian và vòng khôi phục tag, kèm so sánh với `hmac.compare_digest`.
- `transcript.txt`: output thật.

## Ý chính

So sánh MAC phải hằng thời gian (`hmac.compare_digest`). Dừng sớm khi gặp byte sai là đủ để lộ cả tag qua kênh thời gian.
