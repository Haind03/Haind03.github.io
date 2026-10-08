#!/usr/bin/env python3
# solve.py: khai thac giao thuc token. Ta chi la user thuong, khong biet key.
# CTR: ct = pt XOR keystream. Vi khong co MAC, ta lat tung byte ct de doi
# "role=guest" thanh "role=admin" ma server van chap nhan.
from server import issue_token, is_admin

def flip(ct, offset, old, new):
    # ct[offset+i] moi = ct[offset+i] XOR old[i] XOR new[i]
    out = bytearray(ct)
    for i in range(len(old)):
        out[offset + i] ^= old[i] ^ new[i]
    return bytes(out)

if __name__ == "__main__":
    # 1) Xin mot token hop le cho username cua minh
    token = issue_token("bob")
    plain_known = b"user=bob&role=guest"       # ta BIET cau truc plaintext nay
    print("token goc (hex):", token.hex())
    print("role hien tai  :", is_admin(token))  # (False, None)

    # 2) Vi tri cua "guest" trong plaintext da biet
    off = plain_known.index(b"guest")
    forged = flip(token, off, b"guest", b"admin")

    # 3) Gui token da che: server giai ma ra role=admin
    ok, flag = is_admin(forged)
    print("token che (hex):", forged.hex())
    print("ket qua        :", (ok, flag))
    assert ok, "khong len duoc admin"
    print("FLAG           :", flag)
