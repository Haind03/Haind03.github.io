#!/usr/bin/env python3
# solve.py: timing attack khoi phuc tag MAC qua so sanh KHONG hang thoi gian.
#
# Kich ban: server kiem tag bang vong lap so sanh tung byte, dung som ngay khi
# gap byte sai (giong toan tu == cua nhieu ngon ngu). Moi byte khop ton them
# mot it thoi gian xu ly. Do thoi gian phan hoi, ke tan cong doan duoc da
# khop bao nhieu byte, tu do khoi phuc tag tung byte ma khong biet key.
#
# De tin hieu thoi gian on dinh trong demo, "cong viec moi byte" duoc mo phong
# bang busy-wait (spin) thay vi sleep. Trong thuc te tin hieu nho hon nhieu,
# phai do hang nghin lan va loc nhieu, nhung co che thi y het.
#
# Chay:  python3 solve.py
import hmac
import hashlib
import os
import time

KEY = os.urandom(16)                       # ke tan cong KHONG biet
WORK_US = 300.0                            # moi byte khop ton ~300us xu ly
TAGLEN = 6                                 # so byte tag can khoi phuc (demo)
TRIALS = 9                                 # so lan do moi ung vien, lay min


def real_tag(msg):
    return hmac.new(KEY, msg, hashlib.sha256).digest()


def _spin(us):
    end = time.perf_counter() + us / 1e6
    while time.perf_counter() < end:
        pass


# --- phia server: so sanh KHONG hang thoi gian, dung som khi byte sai ---
def insecure_verify(msg, tag_guess):
    correct = real_tag(msg)
    n = min(len(tag_guess), len(correct))
    for i in range(n):
        if tag_guess[i] != correct[i]:
            return False                   # dung som: lo thong tin thoi gian
        _spin(WORK_US)                      # moi byte khop ton them thoi gian
    return tag_guess == correct


# --- phia tan cong: chi goi insecure_verify, do thoi gian ---
def time_call(msg, tag_guess, trials):
    best = float("inf")
    for _ in range(trials):
        t0 = time.perf_counter()
        insecure_verify(msg, tag_guess)
        dt = time.perf_counter() - t0
        if dt < best:                       # min = lan it bi nhieu nhat
            best = dt
    return best


def attack(msg, taglen, trials):
    recovered = bytearray()
    for _pos in range(taglen):
        best_t, best_b = -1.0, 0
        for b in range(256):
            guess = bytes(recovered) + bytes([b]) + b"\x00" * (taglen - len(recovered) - 1)
            t = time_call(msg, guess, trials)
            if t > best_t:                  # byte dung = cham nhat (khop them 1 byte)
                best_t, best_b = t, b
        recovered.append(best_b)
        print("    byte %d -> %02x" % (_pos, best_b))
    return bytes(recovered)


def main():
    msg = b"amount=100&to=alice"
    print("[*] thong diep:", msg.decode())
    print("[*] bat dau timing attack, khoi phuc %d byte dau cua tag..." % TAGLEN)
    t0 = time.time()
    rec = attack(msg, TAGLEN, TRIALS)
    dt = time.time() - t0
    truth = real_tag(msg)[:TAGLEN]
    print("[*] khoi phuc :", rec.hex())
    print("[*] tag that  :", truth.hex())
    print("[*] khop?     :", rec == truth, "(%.1fs)" % dt)
    assert rec == truth, "timing attack that bai, chay lai (nhieu he thong)"
    print("[+] timing attack THANH CONG, khong biet key")

    # chung minh so sanh HANG thoi gian chan duoc don nay
    print()
    print("[*] cach lam dung: hmac.compare_digest (hang thoi gian).")
    correct = real_tag(msg)
    almost = bytearray(correct)
    almost[-1] ^= 1                         # chi sai dung byte cuoi
    allwrong = b"\x00" * len(correct)       # sai ngay byte dau

    def measure(cmp_fn, a, b, trials=200000):
        best = float("inf")
        for _ in range(trials):
            t0 = time.perf_counter()
            cmp_fn(a, b)
            dt = time.perf_counter() - t0
            if dt < best:
                best = dt
        return best * 1e9                   # nano giay

    t_almost = measure(hmac.compare_digest, correct, bytes(almost))
    t_wrong = measure(hmac.compare_digest, correct, allwrong)
    print("    sai byte cuoi : %.0f ns" % t_almost)
    print("    sai byte dau  : %.0f ns" % t_wrong)
    print("    => chenh lech khong tuyen tinh theo prefix -> khong con oracle thoi gian")


if __name__ == "__main__":
    main()
