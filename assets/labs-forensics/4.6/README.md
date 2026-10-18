# Lab 4.6: Volume Shadow Copy

Day la BAI TAP, khong phai lab chay that o day. VSS can mot image Windows CO shadow copy
(sinh ra tu System Restore / Windows Update / backup), cong them `libvshadow` hoac Windows
`vssadmin`. Moi truong lab khong-root nay khong tao duoc shadow, nen khong co artifact that
de dung. `check_tools.sh` chi kiem tra cong cu va in buoc tiep theo; `transcript.txt` la
output that cua lan kiem tra do (o day thieu libvshadow).

KHONG bia output. Khi ban co image VSS va cong cu, chay dung cac lenh duoi se ra ket qua that.

## Cong cu can
`libvshadow` (vshadowinfo, vshadowmount), `mmls`/`fls` (TSK), hoac tren Windows: `vssadmin`,
`mklink`, ShadowExplorer, Arsenal Image Mounter.

```bash
# Debian/Ubuntu (can root de apt):
apt install libvshadow-utils sleuthkit
```

## Chay kiem tra moi truong
```bash
bash check_tools.sh            # kiem co libvshadow khong
bash check_tools.sh disk.raw   # neu co image VSS + libvshadow: liet ke shadow
```

## Bai tap A: tao du lieu (tren VM Windows)
1. Bat System Protection cho o C.
2. Tao tai lieu phien ban 1. `Checkpoint-Computer -Description v1` (ep tao restore point).
3. Sua tai lieu thanh phien ban 2, them mot Run key. `Checkpoint-Computer -Description v2`.
4. Xoa tai lieu va Run key o ban hien tai. Tao image o (export VMDK/VHDX roi convert sang raw).

## Bai tap B: khai thac VSS tren image offline (Linux)
```bash
# 1) liet ke shadow + thoi diem tao
vshadowinfo /evidence/disk.raw
#    neu image la ca o nhieu phan vung, cong offset:
mmls /evidence/disk.raw
vshadowinfo -o $((206848*512)) /evidence/disk.raw

# 2) mount tat ca shadow thanh vss1, vss2 ...
mkdir -p /mnt/vss
vshadowmount /evidence/disk.raw /mnt/vss

# 3) moi vssN la mot anh volume NTFS, mount read-only
mkdir -p /mnt/vss3_files
mount -o ro,loop,show_sys_files,streams_interface=windows /mnt/vss/vss3 /mnt/vss3_files

# 4) lay lai ban cu cua file da xoa + hive de so Run key
cp /mnt/vss3_files/Users/An/Desktop/hopdong_v1.docx /work/
cp /mnt/vss3_files/Windows/System32/config/SOFTWARE /work/SOFTWARE_vss3
regipy-plugins-run /work/SOFTWARE_vss3 -o vss3.json -p software_plugin
```

## Bai tap C: so cung artifact qua nhieu shadow (thu hep cua so thoi gian)
```bash
for v in /mnt/vss/vss*; do
  n=$(basename "$v"); mkdir -p /mnt/${n}_f
  mount -o ro,loop "$v" /mnt/${n}_f 2>/dev/null
  echo "===== $n ====="
  regipy-plugins-run /mnt/${n}_f/Windows/System32/config/SOFTWARE -o /tmp/$n.json -p software_plugin 2>/dev/null
done
# Run key `svc` chua co o shadow ngay 20/09, xuat hien o shadow 28/09 -> persistence cai trong khoang do.
```

## Bai tap D: phat hien hanh vi xoa shadow (IOC ransomware)
Trong event log / Sysmon / PowerShell, tim cac lenh:
```text
vssadmin.exe delete shadows /all /quiet
wmic shadowcopy delete
bcdedit /set recoveryenabled no
```
Neu `vssadmin list shadows` trong khi may bat System Restore ma khong con shadow nao -> nghi
co nguoi da xoa, di tim lenh xoa trong log.

## Tren Windows (bai tap E)
```text
vssadmin list shadows
mklink /d C:\vsc3 \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy3\
dir C:\vsc3\Users\An\Documents
```
Hoac dung ShadowExplorer (GUI) de duyet va export file theo tung ngay.
