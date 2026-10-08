# Lab 11.3: Đồ án, mổ xẻ giao thức session token

Kèm Bài 11.3 (đồ án cuối). Một giao thức cấp session token tự chế dùng AES-CTR nonce cố định, không MAC. Khai thác malleability để lật `role=guest` thành `role=admin` và lấy flag.

## File

- `server.py`: giao thức mẫu. Ba lỗi: nonce cố định (keystream lặp), không MAC (ciphertext malleable), tin mù dữ liệu sau giải mã.
- `solve.py`: exploit bit-flipping. Xin một token guest, lật 5 byte ciphertext ở vị trí `guest`, gửi lại, chiếm quyền admin.
- `nonce_reuse_demo.py`: minh họa lỗi nonce cố định. XOR hai ciphertext lộ phần plaintext trùng nhau.

## Chạy

```bash
python3 solve.py
python3 nonce_reuse_demo.py
```

## Kết quả mong đợi

```
# solve.py
role hien tai  : (False, None)
ket qua        : (True, 'flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}')
FLAG           : flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}

# nonce_reuse_demo.py
ct1 XOR ct2 (hex): 000000000003030b52570000000000000000000000
so byte 0 o duoi : 16 / 21
```

Xem `transcript.txt` để đối chiếu output thật.

## Yêu cầu

PyCryptodome. Chạy trong cùng thư mục với `server.py` vì `solve.py` import nó.

## Đồ án mở rộng (xem Bài 11.3 mục 3)

- Viết `server_fixed.py` dùng AES-GCM nonce ngẫu nhiên, chứng minh exploit bị chặn.
- Viết `server_ecb.py` dùng ECB, thực hiện ECB cut-and-paste.
- Viết writeup hoàn chỉnh theo khung Bài 11.2.

## Điểm mấu chốt

- Mã hóa không phải xác thực. CTR malleable: `ct'[i] = ct[i] XOR old[i] XOR new[i]`, đổi plaintext mà không cần khóa.
- Vá bằng AEAD (GCM) hoặc Encrypt-then-MAC, kiểm tag trước khi tin dữ liệu.
