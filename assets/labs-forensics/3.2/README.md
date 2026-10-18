# Lab 3.2: File carving

Lab chay that tren Linux (khong can root): mot image nhet san JPG + PNG + ZIP + PDF (ghep bytes, co junk xen giua),
carve lai bang `binwalk` va bang carver python tu viet, roi verify file trich ra mo duoc.

## Cong cu
`binwalk`, `python3`, `file`, `unzip`, `xxd`, `md5sum`, ImageMagick (`convert`), `zip`.

Luu y binwalk: moi truong binh thuong chay thang `binwalk carve.img`. May nay co binwalk 2.x ket voi capstone moi,
nen `solve.sh` chay qua `binwalk_shim.py` (va lai hang so `CS_ARCH_ARM64`). Noi dung ket qua giong het binwalk goc.

## Chay lab
```bash
bash make.sh     # tao carve.img (6KB) + cac file goc j.jpg p.png z.zip d.pdf
bash solve.sh    # binwalk, carver python, verify, so khop byte
```
`transcript.txt` la output THAT. `carve.img` va cac file goc deu nhe nen GIU trong repo. Thu muc `out/` la ket qua carve.

## Scripts
- `carve.py IMG OUTDIR` : carver theo header/footer (JPEG FFD8..FFD9, PNG ..IEND, ZIP PK0304..EOCD, PDF %PDF..%%EOF).
- `binwalk_shim.py`      : wrapper cho binwalk 2.x tren may capstone moi.

## Nhiem vu
1. Carve bang binwalk, ghi lai offset moi chu ky. Carve lai bang `carve.py`, so offset co khop binwalk khong.
2. Mo cac file carve ra (`file`, `unzip -t`), dem bao nhieu file mo dung. So khop byte voi ban goc bang `cmp`/`md5sum`
   (JPG, PNG carve dung tron nen khop tung byte).
3. Tu tim header JPEG trong image bang `xxd carve.img | grep -i ffd8ff`, doi chieu offset voi binwalk.

## Nhiem vu la bai tap (cong cu chuyen chua cai o may nay)
4. Carve bang `foremost` va `photorec`, so so file dung duoc va luong rac; giai thich vi sao PhotoRec tot hon voi file phan manh
   (hieu cau truc file chu khong chi header/footer). Thu `bulk_extractor` xem co bat duoc email/URL nhung trong ZIP/PDF khong
   (chuoi `billing@example.com`, `http://evil.example.org/c2` da nhet san trong `doc.txt`).
5. Thu tinh huong phan manh: chep file lon vao roi xoa, chep file khac de len mot phan, carve file dau -> thay no loi vi bi xen giua.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
