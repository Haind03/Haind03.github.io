# Lab 0.2: HTTP nội soi

App Flask nhỏ để tập đọc và dựng HTTP request/response bằng tay. Dùng cho [Bài 0.2](../../phan-00-nhap-mon/0.2-http-https-cot-loi.md). Đây là app tập luyện, không cài cắm lỗ hổng.

## Yêu cầu
- Python 3 và Flask: `pip install flask`
- `curl` (đã có sẵn trên hầu hết hệ thống)

## Chạy
```bash
cd labs/0.2
python3 app.py          # lắng nghe 127.0.0.1:8010
# đổi cổng nếu cần:  PORT=8010 python3 app.py
```
Chỉ lắng nghe loopback (127.0.0.1), không ra ngoài mạng.

## Các endpoint
| Đường dẫn | Việc nó làm |
|---|---|
| `GET /` | trang chủ, liệt kê các endpoint, trả kèm header `Server: Lab0.2/Flask` |
| `/echo` (mọi method) | trả về JSON mô tả request: method, query, header, cookie, body |
| `POST /login` | `user=admin&pass=admin` thì trả `Set-Cookie: session=...` |
| `GET /whoami` | đọc cookie `session`, cho biết bạn là ai |
| `GET /redirect` | trả `302` về `/` (thử với `curl -L`) |
| `GET /secret` | `401` nếu thiếu header `Authorization`, `200` nếu có |
| `GET /teapot` | `418` cho vui, để thấy status code lạ |

## Thử nhanh
```bash
curl -v http://127.0.0.1:8010/ -o /dev/null
curl -s "http://127.0.0.1:8010/echo?q=hello" -H "X-Custom: demo"
curl -i -s -X POST -d "user=admin&pass=admin" http://127.0.0.1:8010/login
curl -s -b "session=s3ss10n-demo-abc123" http://127.0.0.1:8010/whoami
curl -i -s http://127.0.0.1:8010/secret
```

## Tắt app
Nhấn `Ctrl+C` ở terminal đang chạy `python3 app.py`.

## Transcript
`transcript.txt` là output thật của một lần chạy đầy đủ các lệnh trên.
