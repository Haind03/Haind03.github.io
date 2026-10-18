# Lab 8.2: Email forensics, doc header va truy nguon gui

Lab chay that di kem [Bai 8.2](../../phan-08-browser-email-mobile/8.2-email-forensics.md).
Hai file `.eml` gia lap: mot email phishing gia danh PayPal va mot email that de doi chung.
Moi domain va IP deu la dia chi vi du (RFC 5737 / TEST-NET, v.v.), khong dung du lieu that.

## File trong lab
- `make_artifacts.py` tao `mail/phish.eml` (Received chain 3 hop, From/Return-Path/Reply-To
  venh nhau, `Authentication-Results` spf=fail/dkim=none/dmarc=fail, Message-ID domain la,
  link phishing trong body) va `mail/legit.eml` (spf/dkim/dmarc=pass, cac truong khop).
- `solve.py` dung module `email` parse header, lan chuoi Received tu DUOI len ra IP gui goc,
  doc Authentication-Results, soi diem venh, trich link body (khong bam), roi ket luan.
- `transcript.txt` output that cho ca hai email.

## Chay
```bash
python3 -I make_artifacts.py mail
python3 -I solve.py mail/phish.eml mail/legit.eml
```

## Nhiem vu (khop muc 3 cua bai hoc)
1. Lay header tho, xac dinh chuoi Received, chi ra IP gui goc o dong duoi cung.
2. Doc Authentication-Results, giai thich SPF/DKIM/DMARC pass hay fail va vi sao.
3. Voi email nghi phishing: so From, Return-Path, Reply-To, Message-ID; (tren may co mang)
   tra IP gui bang `whois`, doi chieu SPF cua domain bi gia danh bang `dig TXT paypal.com`.
4. (Mo rong) dung `readpst`/`pffexport` bung mot file PST ra EML roi tim theo subject.
5. Viet ket luan: server goc nao gui, bang chung gia mao gom nhung truong nao.

## Dap an rut gon (phish.eml)
- IP gui goc: `45.77.123.45` (chang Received duoi cung, host tu khai `paypa1-support.com`).
- Server trung gian dau: `relay.cheaphost.net`, khong phai ha tang PayPal.
- `spf=fail`, `dkim=none`, `dmarc=fail (p=reject) header.from=paypal.com`.
- From `service@paypal.com` nhung Return-Path ve `paypa1-support.com`, Reply-To ve
  `secure-paypal-check.info`, Message-ID sinh tu `relay.cheaphost.net`, link body ve
  `secure-paypal-check.info`. Hien thi mot dang, thuc chat mot neo -> gia mao.

## Ghi chu
- Received doc tu DUOI len; From la text de gia, Return-Path/Message-ID kho gia hon.
- `solve.py` lam offline (khong goi mang). Buoc `dig`/`whois` trong bai la tuy chon khi co mang.
- Module `email` co the chuan hoa lai thu trong tuan cua `Date`; day cung la mot diem dang
  soi (client nguoi gui dat Date sai thu).
