#!/usr/bin/env bash
# Lab 1.7 - hashing & toan ven: tao disk.img nho (tai lap duoc) + 2 bien the van ban.
set -eu
cd "$(dirname "$0")"
rm -f disk.img disk.img.sha256 v1.txt v2.txt work.img work.sha256

# disk.img 64KB, noi dung co dinh (seed) de tai lap duoc hash
python3 -I -c "
import random
random.seed(1337)
open('disk.img','wb').write(bytes(random.getrandbits(8) for _ in range(65536)))
"
sha256sum disk.img > disk.img.sha256

# hai bien the van ban: v2 khac v1 dung 2 dong
cat > v1.txt <<'EOF'
BAO CAO DIEU TRA
ma vu: 2024-09-15
dieu tra vien: HaiND
ket luan: du lieu bi ro ri qua USB
hanh dong: niem phong thiet bi
EOF
cat > v2.txt <<'EOF'
BAO CAO DIEU TRA
ma vu: 2024-09-15
dieu tra vien: HaiND
ket luan: du lieu bi ro ri qua email ca nhan
hanh dong: niem phong thiet bi va thu hoi tai khoan
EOF

echo "[make] da tao disk.img (64KB), disk.img.sha256, v1.txt, v2.txt"
ls -l disk.img v1.txt v2.txt
