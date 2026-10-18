# Lab 1.7: Hashing va toan ven du lieu

Lab chay that tren Linux (khong can root).

## Cong cu
`sha256sum`, `md5sum`, `dd`, `python3`. (ssdeep khong co trong may nay, dung `fuzzyhash.py` minh hoa.)

## Chay lab
```bash
bash make.sh     # tao disk.img (64KB, tai lap duoc), disk.img.sha256, v1.txt, v2.txt
bash solve.sh    # verify hash, sua 1 byte, so hash 2 bien the, fuzzy hash
```
`transcript.txt` la output THAT. Cac artifact nhe (`disk.img` 64KB, `v1.txt`, `v2.txt`) GIU trong repo.

## Nhiem vu
1. Hash SHA-256 cua `disk.img` cat vao manifest. Tao ban lam viec, sua dung 1 byte bang `dd ... conv=notrunc`,
   dung `sha256sum -c` chung minh phat hien duoc. Giai thich tinh chat avalanche cua hash.
2. Hai bien the `v1.txt`/`v2.txt` (khac nhau vai dong): cho thay MD5/SHA-256 cua chung khac hoan toan,
   khong goi y gi ve quan he; roi dung fuzzy hash chi ra chung gan giong va doc diem so.
3. Tra loi bang loi (xem `solution.md`): neu luat su hoi "vi sao dung MD5 khi no da bi pha", dap 3 cau
   (phan biet collision va second-preimage, va best practice dual hash).
4. Nang cao (bai tap): tai 1 cap block va cham MD5 cong khai (vd cap cua Marc Stevens), ghep vao 2 file,
   cho thay `md5sum` trung nhung `sha256sum` khac. Can tai file tu ngoai nen de o muc bai tap.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
