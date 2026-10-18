# Dap an Lab 1.2

## Nhiem vu 1 (tinh tay)

Cho sector 512 byte, cluster 8192 byte, file 20000 byte.

1. So cluster: ceil(20000 / 8192) = 3 cluster. Byte cap phat = 3 * 8192 = 24576 byte.
2. Sector cuoi chua du lieu: 20000 mod 512 = 288 byte. RAM slack = 512 - 288 = 224 byte (phan con lai cua sector cuoi, OS cu dem bang 0).
3. Drive slack = 24576 - 20000 - 224 = 4352 byte (cac sector trong con lai cua cluster cuoi).
4. Offset tuyet doi cua phan vung bat dau o LBA 2048 = 2048 * 512 = 1048576 byte = 0x100000 = 1 MiB.

## Nhiem vu 2-3 (chay lab)

- `fsstat` cho Block Size 1024. File `small.bin` size 19 byte nhung chiem tron 1 block 1024 byte (`istat` -> Direct Blocks co 1 block). Chenh lech 1024 - 19 = 1005 byte la file slack cua block do.
- `blkls` trich toan bo unallocated ra `unalloc.raw` (~6.7MB). `strings unalloc.raw | grep -o OLD-SECRET-DATA | wc -l` dem ra vai nghin lan: do la noi dung file lon da xoa VAN nam nguyen tren cac block chua bi cap phat lai.
- `blkcat lab12.ext4 <probe_block>` doc truc tiep mot block cu, `xxd` thay nguyen pattern `OLD-SECRET-DATA-...`.

Diem cot loi: xoa file chi go metadata, du lieu con nam vat ly tren dia cho den khi bi ghi de. Day la nen tang cua khoi phuc file (bai 3.3) va carving (bai 3.2).

## Ghi chu trung thuc ve slack

Trong lab khong-root, `debugfs write` zero-pad tron block cua file moi ghi, nen slack NGAY TRONG block vua ghi doc ra 0. Tren o that (OS ghi qua mount), OS khong zero phan duoi block cuoi, nen slack giu lai manh du lieu cu. Bai 3.4 (muc Slack) trich slack bang `blkls -s`. O day ta chung minh cung mot su that (byte cu ton tai tren dia) qua vung unallocated, cai ma lab khong-root doc duoc chac chan.
