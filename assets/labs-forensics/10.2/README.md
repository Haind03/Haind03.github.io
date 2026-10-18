# Lab 10.2: Full disk encryption (BitLocker, LUKS, FileVault)

Buoc NHAN DIEN FDE (signature) chay THAT tren Linux. Buoc tao/mo/crack container la BAI TAP:
`cryptsetup` khong co trong moi truong nay (va can root de map dm-crypt), BitLocker/dislocker
can Windows hoac goi rieng. KHONG bia output: cac lenh crack duoi la that, chay khi ban co
cong cu + container.

`make_sig_samples.py` tao vai STUB signature (chi vai byte header, KHONG phai container ma hoa
that, khong crack duoc) de chay thu `identify_fde.py`. `transcript.txt` la output that cua
buoc nhan dien.

## Cong cu
- Nhan dien: `python3` (co san).
- Bai tap: `cryptsetup`, `luks2john` + `john`/`hashcat`, `dislocker`, `bitlocker2john`,
  `fvdemount` (libfvde), `mmls`/`fsstat` (TSK), Volatility 3.

## Chay phan nhan dien (that)
```bash
bash solve.sh
# hoac:
python3 -I make_sig_samples.py
python3 -I identify_fde.py luks_header.sig bitlocker.sig filevault.sig
# tren image that:
python3 -I identify_fde.py /evidence/disk.raw
```
identify_fde.py quet magic `LUKS\xba\xbe` (LUKS) va `-FVE-FS-` (BitLocker) trong 1MB dau.

## Bai tap A: nhan dien bang TSK tren image that
```bash
mmls LAPTOP01.E01
fsstat -o 2048 LAPTOP01.E01                 # bao "Bitlocker" neu nhan ra
dd if=LAPTOP01.E01 bs=512 skip=2048 count=1 | xxd | grep -i FVE   # thay "-FVE-FS-"
```

## Bai tap B: LUKS (can cryptsetup, co the can root)
```bash
# tao container LUKS tren FILE (khong can o that):
dd if=/dev/zero of=luks.img bs=1M count=64
cryptsetup luksFormat luks.img          # dat passphrase yeu de luyen crack
# doc header KHONG can mount, KHONG can root:
cryptsetup luksDump luks.img            # version, cipher, slot nao dang dung
# mo (can root cho dm-crypt):
sudo cryptsetup open luks.img secure
sudo mount -r /dev/mapper/secure /mnt/clear
# crack passphrase yeu offline:
luks2john luks.img > luks.hash
john --wordlist=rockyou.txt luks.hash
```

## Bai tap C: BitLocker (can Windows / dislocker)
```bash
# trich partition BitLocker ra file (offset tu mmls):
dd if=LAPTOP01.E01 of=bde.img bs=512 skip=206848
# co recovery key -> mo bang dislocker:
mkdir /mnt/bde /mnt/clear
dislocker -V bde.img -p123456-...-654321 -- /mnt/bde
mount -r -o loop /mnt/bde/dislocker-file /mnt/clear
# chi co mat khau yeu -> trich hash va crack:
bitlocker2john -i bde.img > bde.hashes
john --wordlist=rockyou.txt bde.hashes        # hoac hashcat -m 22100
# RecoveryKeyID de hoi IT dung khoa nao:
dislocker -V bde.img            # (hoac repair-bde -rp)
```

## Bai tap D: lay khoa tu RAM (khi co dump luc may mo khoa)
```bash
vol -f LAPTOP01.mem windows.bitlocker        # Volatility 3 tra ve FVEK
# dung FVEK voi dislocker -K hoac tool giai ma offline
```

## Bai tap E: chien luoc hien truong (viet 5 dong)
Neu gap may dang chay nghi co FDE: can nhac LIVE acquisition (chup RAM va/hoac image o trang
thai da mo) TRUOC khi tat may. Tat may xoa khoa trong RAM, con lai khoi byte ma hoa. Di het
nguon khoa de (AD/MBAM, Microsoft account, recovery key, hiberfil) truoc khi nghi toi crack.

## Dap an rut gon (phan nhan dien)
- `LUKS\xba\xbe` o offset 0 => LUKS, doc tiep bang `cryptsetup luksDump`.
- `-FVE-FS-` => BitLocker, lay RecoveryKeyID bang `dislocker -V`.
- Khong co magic quen => co the chua ma hoa, hoac VeraCrypt (khong co magic ro rang).
