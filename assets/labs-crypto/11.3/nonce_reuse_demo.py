# nonce_reuse_demo.py: nonce co dinh => ct1 XOR ct2 = pt1 XOR pt2 (lo thong tin)
from server import issue_token
t1 = issue_token("alice")
t2 = issue_token("bob12")
x = bytes(a ^ b for a, b in zip(t1, t2))
# x bang (pt1 XOR pt2); vi phan sau "&role=guest" giong het nhau nen XOR = 0 o do
print("ct1 XOR ct2 (hex):", x.hex())
print("so byte 0 o duoi :", x.count(0), "/", len(x), "-> phan plaintext trung nhau lo ra")
