# Lab 1.3: Content discovery

App Flask có vài route ẩn (không có link nào trỏ tới), để tập brute force đường dẫn bằng ffuf / gobuster / curl. Dùng cho [Bài 1.3](../../phan-01-cong-cu-recon/1.3-recon-content-discovery.md).

## Yêu cầu
- Python 3 và Flask: `pip install flask`
- `ffuf` (khuyến nghị) hoặc `gobuster`, và `curl`
  - Cài ffuf nhanh: `go install github.com/ffuf/ffuf/v2@latest`

## Chạy
```bash
cd labs/1.3
python3 app.py          # lắng nghe 127.0.0.1:8011
```
Chỉ lắng nghe loopback (127.0.0.1).

## Bề mặt công khai và route ẩn
Trang chủ chỉ liên kết tới `/` và `/about`. Các route sau tồn tại nhưng không có link:

| Route ẩn | Nội dung |
|---|---|
| `/admin` | trang quản trị đáng lẽ không public |
| `/backup` | file `config.bak` lộ mật khẩu DB và một `FLAG` |
| `/.git/config` | lộ thư mục `.git` (lỗi cấu hình kinh điển) |
| `/old` | trang cũ còn sót |
| `/api/v1/users` | endpoint API lộ danh sách user (không nằm trong wordlist, phải đoán sâu hơn) |

Mọi đường dẫn không tồn tại trả về `404` thật, để brute-force phân biệt được.

## Khai thác
```bash
# brute force, lọc bỏ 404
ffuf -w wordlist.txt -u http://127.0.0.1:8011/FUZZ -fc 404 -c

# xác nhận route tìm được
curl -s http://127.0.0.1:8011/backup
curl -s http://127.0.0.1:8011/.git/config

# đoán sâu hơn cho endpoint API
curl -s http://127.0.0.1:8011/api/v1/users
```

`wordlist.txt` là wordlist nhỏ kèm sẵn để demo nhanh. Thực tế dùng SecLists (`Discovery/Web-Content/common.txt`).

## Tắt app
Nhấn `Ctrl+C` ở terminal đang chạy `python3 app.py`.

## Transcript
`transcript.txt` là output thật của một lần brute-force và xác nhận đầy đủ.
