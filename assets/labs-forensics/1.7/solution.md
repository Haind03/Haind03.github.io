# Dap an Lab 1.7

## Nhiem vu 1: verify va phat hien sua 1 byte

- `sha256sum disk.img > disk.img.sha256` luu hash goc. `sha256sum -c` doc lai va so.
- Sau khi `dd` sua dung 1 byte, `sha256sum -c` in `FAILED` va canh bao 1 checksum khong khop (xem `transcript.txt` B2).
- Tinh chat: avalanche effect. Doi 1 bit o input lam thay doi trung binh nửa so bit o output, va hash la
  one-way + collision-resistant, nen khong the sua noi dung ma giu nguyen hash. Do la co so de niem phong bang chung.

## Nhiem vu 2: hash mat ma khong goi y quan he, fuzzy hash thi co

- `v1.txt` va `v2.txt` chi khac 2 dong, nhung MD5 va SHA-256 cua chung khac hoan toan (xem B3). Hash mat ma
  duoc thiet ke de KHONG lo quan he gan-giong.
- `fuzzyhash.py` (minh hoa, Jaccard tren shingle 8-byte): v1 vs v2 = 66/100 (gan giong), v1/v2 vs disk.img = 0.
  Cong cu that la `ssdeep -m` / `ssdeep -b`: no dung context-triggered piecewise hashing, cho diem 0..100 tuong tu.
  Dung de tim file "gan giong" (bien the malware, tai lieu sua doi) ma hash mat ma bo sot.

## Nhiem vu 3: tra loi luat su ve MD5 (3 cau)

1. MD5 bi pha o kha nang chong COLLISION (co the co tinh dung ra hai file khac nhau cung MD5), chu khong bi pha
   second-preimage (chua ai dung duoc file khac co MD5 trung voi mot file da cho truoc).
2. Trong vu nay bang chung la file co san, ta chi can phat hien thay doi (second-preimage), nen MD5 van bat duoc moi sua doi.
3. Du vay best practice la DUAL HASH (ghi ca MD5 va SHA-256): neu mot thuat toan bi nghi ngo, cai con lai van bao chung,
   va toa khong con cho tranh cai.

## Nhiem vu 4 (bai tap, can tai file ngoai)

Tai 1 cap block va cham MD5 cong khai, ghep vao 2 file: `md5sum` hai file trung nhau trong khi `sha256sum` khac.
Day la minh hoa truc quan vi sao khong dung MD5 o noi can chong collision (vd ky so, chong trung lap tin cay).

## Ghi nho
- Hash de niem phong toan ven: sua 1 byte la lo ngay.
- MD5 con dung duoc de phat hien thay doi, nhung luon kem SHA-256.
- Fuzzy hash (ssdeep) tim file gan giong, bo tro cho hash mat ma.
