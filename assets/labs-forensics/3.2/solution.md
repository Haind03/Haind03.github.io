# Dap an Lab 3.2

## Nhiem vu 1-3 (chay lab)

Offset binwalk tim duoc (xem `transcript.txt` B1) va carver python (B2) KHOP nhau:

| File | Offset dec | Offset hex | Ket qua |
|---|---|---|---|
| JPEG | 300  | 0x12C  | mo duoc, 200x140 |
| PNG  | 4760 | 0x1298 | mo duoc, 160x100 |
| ZIP  | 5249 | 0x1481 | unzip -t OK, chua doc.txt |
| PDF  | 5674 | 0x162A | mo duoc, 1 trang |

- `carve.py` cat tu header den footer: JPEG `FF D8 FF ... FF D9`, PNG signature `.. IEND` + 4 byte CRC,
  ZIP `PK\x03\x04 .. PK\x05\x06` (EOCD) + 22 byte + comment, PDF `%PDF .. %%EOF`.
- JPG va PNG carve ra KHOP tung byte voi ban goc (`cmp` im lang, md5 trung): carving thanh cong tuyet doi khi file lien tuc, khong phan manh.
- `xxd carve.img | grep -i 'ffd8 ff'` thay header JPEG o dong 0x120, byte `FF D8 FF E0` roi vao, dung offset 300 = 0x12C nhu binwalk.

## Nhiem vu 4-5 (bai tap)

- `foremost` carve theo header/footer giong `carve.py`, de loi voi file phan manh. `photorec` hieu cau truc nhieu dinh dang
  nen ghep lai tot hon -> nhieu file dung duoc hon, it rac hon.
- `bulk_extractor` KHONG carve nguyen file ma quet trich noi dung dang chu y (email, URL, the tin dung, ...). No se bat duoc
  `billing@example.com` va `http://evil.example.org/c2` da nhet trong ZIP.
- Phan manh: khi file bi mot file khac de len mot phan, carver header/footer se cat ca phan rac xen giua -> file loi.
  Do la ly do PhotoRec (hieu cau truc) thuong thang carver thuan header/footer.

## Diem chot
- Carving khong can metadata FS, chi can byte -> cuu duoc file tu vung unallocated, dia format, mang image.
- Carver header/footer don gian, de loi voi file phan manh; cong cu hieu cau truc file manh hon.
