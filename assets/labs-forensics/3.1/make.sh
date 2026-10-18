#!/usr/bin/env bash
# Lab 3.1 - TSK/Autopsy: dung ext4 case image co file giu lai + file da xoa, gan timestamp co that.
# Khong can root (debugfs, khong mount).
set -eu
cd "$(dirname "$0")"
IMG=case.ext4
rm -f "$IMG" keep.txt del.txt

dd if=/dev/zero of="$IMG" bs=1M count=8 status=none
mkfs.ext4 -q -F -b 1024 -L CASE01 "$IMG"

printf 'tai lieu cong ty - giu lai\n'            > keep.txt
printf 'ke hoach ro ri du lieu qua email - xoa gap\n' > del.txt

debugfs -w "$IMG" >/dev/null 2>&1 <<'EOF'
write keep.txt keep.txt
write del.txt tobedeleted.txt
EOF

KINO=$(fls "$IMG" 2>/dev/null | awk '/keep.txt/{gsub(/:/,"",$2);print $2;exit}')
DINO=$(fls "$IMG" 2>/dev/null | awk '/tobedeleted/{gsub(/:/,"",$2);print $2;exit}')

# Gan timestamp (debugfs nhan gio UTC). keep: tao 2024-09-10. del: tao 09-14, sua 09-15.
debugfs -w "$IMG" >/dev/null 2>&1 <<EOF
set_inode_field <$KINO> crtime 20240910080000
set_inode_field <$KINO> mtime  20240910080000
set_inode_field <$KINO> atime  20240910080000
set_inode_field <$KINO> ctime  20240910080000
set_inode_field <$DINO> crtime 20240914023000
set_inode_field <$DINO> mtime  20240915073000
set_inode_field <$DINO> atime  20240915073000
set_inode_field <$DINO> ctime  20240915073000
EOF

# Xoa file thu hai de tao file deleted
debugfs -w -R "rm /tobedeleted.txt" "$IMG" >/dev/null 2>&1

echo "[make] da tao $IMG (keep inode $KINO, deleted inode $DINO)"
ls -l "$IMG"
