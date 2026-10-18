# Lab 5.2: macOS artifact, truy mot app la tu khoi dong (mo phong tren Linux)

Lab chay that di kem [Bai 5.2](../../phan-05-linux-macos/5.2-macos-artifact.md). Khong co
may Mac van tap duoc: ta tai tao DUNG CAU TRUC cac artifact macOS roi doc chung bang cong
cu co san tren Linux. Day la mo phong, khong dung du lieu rieng tu that.

Anh xa cong cu (macOS -> cong cu dung trong lab):
- `plutil`  -> `plistlib` (doc binary plist truc tiep, khong can `cat`)
- `xattr com.apple.quarantine` -> `os.setxattr`/`os.getxattr` tren namespace `user.*`
  (tren may Linux that co the dung `setfattr -n user.com.apple.quarantine -v ... file` va
  `getfattr -n user.com.apple.quarantine file`; may nay khong co setfattr nen dung Python)
- `mdls kMDItemWhereFroms` -> doc binary plist luu trong xattr metadata
- `log show` -> bo qua (unified log nhi phan khong tai tao gon duoc tren Linux)
- `sqlite3` -> module `sqlite3` (knowledgeC.db, TCC.db giong het macOS)

## File trong lab
- `make_artifacts.py` dung cay `mac/`: binary gia `Users/Shared/.updater/softwareupdated`
  (kem quarantine + WhereFroms), LaunchAgent binary plist `com.apple.softwareupdated.plist`,
  `knowledgeC.db` (ZOBJECT, Mac absolute time), `TCC.db` (bang access).
- `solve.py` doc tat ca va ket luan: app vao may bang gi, autostart ra sao, quyen gi.
- `transcript.txt` output that.

## Chay
```bash
python3 -I make_artifacts.py mac
python3 -I solve.py mac
```
Neu fs khong ho tro xattr `user.*`, script tu ghi sidecar vao `mac/.../.xattr/` va van doc lai duoc.

## Nhiem vu (khop muc 3 cua bai hoc)
1. Tim plist persistence, trich `ProgramArguments`, `RunAtLoad`, `KeepAlive`.
2. Lay URL tai va app tai tu `com.apple.quarantine` + `kMDItemWhereFroms`.
3. Tu knowledgeC dem so lan va khung gio app foreground (nho `+978307200`).
4. Kiem TCC xem binary la duoc cap quyen gi.
5. Viet ket luan ngan: vao may bang cach nao, autostart co che gi, co quyen gi.

## Dap an rut gon
- Tai `http://cdn-update.example.bad/su.zip` bang Google Chrome luc `2026-01-07 09:15:02 UTC`
  (giai timestamp hex trong quarantine).
- Autostart: LaunchAgent `com.apple.softwareupdated` gia danh Apple, `RunAtLoad`+`KeepAlive`,
  tro toi `/Users/Shared/.updater/softwareupdated` (Apple khong de binary o `/Users/Shared`).
- knowledgeC: app foreground 3 lan, dung sau moi lan login.
- TCC: cap `kTCCServiceAccessibility` va `kTCCServiceSystemPolicyAllFiles` (auth=2) -> du suc
  keylog, nang nghi van tu adware len stalkerware.

## Cai bay da cai san trong lab
- plist la binary, `cat` ra rac; phai `plistlib`/`plutil`.
- knowledgeC dung Mac absolute time (tu 2001); quen `+978307200` se lech 31 nam.
- TCC co ca ban system va ban user; lab nay dat o ban system.
