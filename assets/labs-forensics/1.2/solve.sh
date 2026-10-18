#!/usr/bin/env bash
# Lab 1.2 - solve: chung minh du lieu cu con nam tren dia sau khi xoa, doc bang blkls/blkcat.
set -u
cd "$(dirname "$0")"
IMG=lab12.ext4
source blocks.txt   # big_first_block, probe_block

echo "=== B1: block size + layout ==="
fsstat "$IMG" 2>/dev/null | grep -iE 'Block Size|Block Range|Content Block' | head

echo
echo "=== B2: file hien tai va kich thuoc (khai niem file slack) ==="
fls -r "$IMG" 2>/dev/null | grep -i small
SMINO=$(fls -r "$IMG" 2>/dev/null | awk '/small.bin/{gsub(/:/,"",$2);print $2;exit}')
echo "-- istat small.bin (inode $SMINO): size vs 1 block = slack --"
istat "$IMG" "$SMINO" 2>/dev/null | grep -iE 'size:|Direct Blocks' -A1 | head

echo
echo "=== B3: trich toan bo unallocated bang blkls, tim pattern file da xoa ==="
blkls "$IMG" > unalloc.raw 2>/dev/null
ls -l unalloc.raw
echo -n "so lan xuat hien pattern cu trong unallocated: "
strings unalloc.raw | grep -o 'OLD-SECRET-DATA' | wc -l

echo
echo "=== B4: doc truc tiep mot block cu (probe_block=$probe_block) bang blkcat ==="
blkcat "$IMG" "$probe_block" 2>/dev/null | xxd | head -2

echo
echo "=== B5: GHI CHU trung thuc ve slack trong block da tai su dung ==="
echo "Block ma file nho chiem lai (first block cua big cu = $big_first_block):"
blkcat "$IMG" "$big_first_block" 2>/dev/null | xxd | head -3
echo "-> debugfs khi 'write' zero-pad tron block cua file moi, nen phan slack NGAY TRONG"
echo "   block vua ghi doc ra la 0 trong lab khong-root nay. Tren o that (OS ghi qua mount)"
echo "   OS khong zero duoi block nen slack giu lai du lieu cu. Du vay, du lieu cu VAN con"
echo "   o cac block unallocated khac (B3/B4) va do la diem forensic cot loi."
