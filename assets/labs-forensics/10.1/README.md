# Lab 10.1: Timestomp va log clearing, phat hien nguoc

Lab CHAY THAT tren Linux (khong can root). Phan timestomp va log-clearing duoc tai lap tren
mot ext4 image bang `e2fsprogs` (mke2fs + debugfs) o user-mode, KHONG mount, KHONG can sudo,
KHONG dung du lieu that cua ai. NTFS `$SI` vs `$FN` la khai niem GIAI THICH (xem duoi + bai hoc),
con lab chay that minh hoa dung nguyen ly bang ext4.

## Vi sao ext4 lai minh hoa duoc timestomp cua NTFS
Tren NTFS, timestomp sua duoc `$STANDARD_INFORMATION` ($SI, do user-mode nhin thay) nhung kho
sua `$FILE_NAME` ($FN, do kernel giu). Phat hien = so $SI voi $FN.

Tren ext4 co bon moc: `atime`, `mtime`, `ctime`, `crtime`. `ctime` (inode change time) va
`crtime` (inode birth) do kernel/fs cap nhat, cong cu user nhu `touch -d` chi doi duoc
`mtime`/`atime` chu khong keo lui `ctime`. He qua tuong duong NTFS: mot file co
`mtime < crtime` (sua truoc khi tao) la BAT KHA THI voi file that -> dau hieu timestomp.
Lab nay lui `mtime`/`atime` cua `report_q4.pdf` ve 2009 trong khi `crtime`/`ctime` van 2026.

## Cong cu
`e2fsprogs` (mke2fs, debugfs, dumpe2fs), `python3`. Deu co san tren hau het distro.

## Chay lab
```bash
bash solve.sh    # tu tao case_disk.img (neu chua co) roi phan tich
# hoac tung buoc:
python3 -I make.py
python3 -I solve.py case_disk.img
```
`transcript.txt` la output THAT. `case_disk.img` (8MB) khong giu trong repo, `make.py` tao lai.
`upload_server.log` va `wtmp_last.txt` la nguon doc lap (gia lap da trich tu he thong khac)
de neo su that, cung do `make.py` sinh.

## Nhiem vu (co lab chay that)
1. Quet timestamp moi file, tim file co `mtime < crtime`. O day la `report_q4.pdf`
   (mtime 2009, crtime 2026).
2. Neo su that bang `upload_server.log`: server audit ghi `report_q4.pdf` len luc 2026-10-15,
   khop `crtime`, chung minh `mtime`=2009 la gia.
3. Phat hien log clearing tren `auth.log`: dong log cuoi chi toi 02:11 nhung inode mtime la
   03:05 => co nguoi ghi de/cat log sau khi no da "ngung". Doi chieu `wtmp_last.txt`: phien
   02:45 bi mat khoi auth.log => bi xoa co chu dich.

## Khai niem NTFS tuong ung (bai tap tren Windows)
4. Tren VM Windows: tao file, timestomp `$SI` bang PowerShell `(Get-Item x).CreationTime=...`
   hoac tool timestomp. Parse `$MFT` bang `MFTECmd.exe -f $MFT --csv out`, loc cot `SI<FN`,
   chi ra ca lech nam lan phan nano giay bang 0 (dau hieu timestomp). Xac nhan bang
   `istat -o <off> image.E01 <inode>` (TSK in rieng $SI Times va $FN Times).
5. Log clearing tren Windows: tim Security event 1102 (va 104 o channel khac), doc tai khoan
   va thoi diem xoa. sdelete de lai pattern rename roi delete trong `$UsnJrnl` (UsnJrnl2Csv).

## Dap an rut gon
- File timestomp: `report_q4.pdf`, mtime lui ve 2009 trong khi crtime la 2026-10-15.
- Nguon neo: `upload_server.log` (2026-10-15 09:12) => mtime 2009 la gia.
- Log clearing: `auth.log` inode mtime 03:05 > dong log cuoi 02:11; `wtmp` con phien 02:45 da
  bi xoa khoi auth.log.
