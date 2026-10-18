#!/usr/bin/env bash
# Lab 2.2 - tao "thiet bi" nguon de thuc hanh acquisition
# Sinh mot file device.img (ext4 1MB) co: file noi dung thuong, mot file an (dotfile),
# va mot file da xoa (de minh hoa khoi phuc + bodyfile). Khong can root, khong can mount.
# Cong cu: dd, mkfs.ext4, debugfs (deu thao tac trc tiep tren file anh, khong mount).
set -euo pipefail
cd "$(dirname "$0")"

IMG=device.img
rm -f "$IMG" secret.txt notes.hidden deleted_invoice.txt

echo "[*] 1. Tao file thiet bi rong 1MB (gia lap mot USB nho)"
dd if=/dev/zero of="$IMG" bs=1M count=1 status=none

echo "[*] 2. Dinh dang ext4 (UUID co dinh de de doi chieu)"
mkfs.ext4 -q -F -L EVIDENCE -U 11111111-2222-3333-4444-555555555555 "$IMG" 2>/dev/null

echo "[*] 3. Chuan bi noi dung va nap vao thiet bi bang debugfs (khong mount)"
printf 'flag{chain_of_custody_demo}\nDay la du lieu goc can bao toan.\n' > secret.txt
printf 'ghi chu an - khong hien trong ls thuong\n'                        > notes.hidden
printf 'hoa don bi nghi pham xoa de phi tang\nso tien: 5000 USD\n'        > deleted_invoice.txt

debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
write secret.txt secret.txt
write notes.hidden .notes.hidden
write deleted_invoice.txt deleted_invoice.txt
EOF

echo "[*] 4. Xoa deleted_invoice.txt ngay tren thiet bi (tao artifact file da xoa)"
debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
rm deleted_invoice.txt
EOF

echo "[*] 5. Dat thoi gian co dinh cho secret.txt (de transcript on dinh)"
debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
set_inode_field secret.txt mtime  20260115093000
set_inode_field secret.txt atime  20260115093000
set_inode_field secret.txt ctime  20260115093000
set_inode_field secret.txt crtime 20260115093000
EOF

rm -f secret.txt notes.hidden deleted_invoice.txt
echo "[*] Xong. Thiet bi nguon: $IMG ($(stat -c%s "$IMG") bytes)"
echo "    Chay ./solve.sh de acquisition + verify toan ven."
