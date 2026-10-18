# Lab 4.4: File and folder access (LNK, Jump List, Shellbag)

Lab CHAY THAT tren Linux. Ba artifact, ba cong cu:
- LNK: tu sinh mot shortcut benign bang `pylnk3`, parse bang `LnkParse3`.
- Jump List: parse mot CustomDestinations cong khai, cho thay no la container cua nhieu LNK.
- Shellbag: parse `UsrClass.dat` bang `regipy` de thay thu muc user da duyet.

Tat ca la artifact DU LIEU, khong co file thuc thi.

Nguon: Jump List tu LnkParse3 tests (github.com/Matmaus/LnkParse3); UsrClass.dat tu regipy
test data (github.com/mkorman90/regipy, MIT). `.lnk` do `make.py` tu sinh.

## Cong cu
`LnkParse3`, `pylnk3`, `regipy[cli]`, `tabulate`, `libfwsi-python`, `libfwps-python`,
`libolecf-python`, `python3`, `curl`, `xz`.

```bash
pip install LnkParse3 pylnk3 'regipy[cli]' tabulate libfwsi-python libfwps-python libolecf-python
```
Luu y: shellbag parser cua regipy can `pyfwsi`/`pyfwps`/`pyolecf` (ba goi libyal o tren).
Neu thieu, buoc [3] se bao `No module named 'pyfwsi'`.

## Chay lab
```bash
bash fetch.sh    # tai Jump List + UsrClass.dat, va sinh .lnk
bash solve.sh    # parse LNK, Jump List, Shellbag
```
`transcript.txt` la output THAT. `bang_luong.xlsx.lnk` do `make.py` sinh (timestamp header
phan anh luc sinh, nen moi lan chay se khac ngay).

## Nhiem vu (co lab chay that)
1. LNK: tu target IDList, dung lai duong dan `My Computer / E:\ / Du_an_mat / bang_luong.xlsx`.
   O: VolumeSerial va DriveType=Removable nam trong khoi LinkInfo cua LNK Windows that; LNK
   tu sinh o day minh hoa phan target IDList. Doc LinkInfo day du bang LECmd (bai tap).
2. Jump List: dem so LNK nhung ben trong (9), moi cai tro toi `GettingStarted.exe`. Day la
   diem mau chot: mot Jump List la container cua nhieu Shell Link + mot stream DestList dong
   vai MRU.
3. Shellbag (UsrClass.dat): liet ke thu muc user da DUYET bang Explorer, kem mtime. Hive nay
   co cay `D:\AKMonitor\logs\pic` va vai thu muc Desktop. Shellbag chung minh user da mo
   thu muc do, ke ca tren o roi hay thu muc da xoa.

## Nhiem vu la bai tap (can Windows that de co artifact day du)
4. Tren VM, cam USB, mo file tu USB bang Explorer va Open dialog, luu mot file sang Desktop.
   Trich thu muc `Recent` (gom `AutomaticDestinations`), `NTUSER.DAT`, `UsrClass.dat`.
   Parse LNK bang `LECmd.exe -d Recent` de doc `VolumeSerialNumber`, `DriveType`,
   `MachineID`, `TargetCreated/Modified/Accessed`.
5. Noi `VolumeSerialNumber` trong LNK voi `USBSTOR` (Lab 4.1) de khang dinh cung mot USB,
   roi dung timeline 6 dong cho mot file bi copy ra USB.

## Dap an rut gon
- LNK target: `E:\Du_an_mat\bang_luong.xlsx` (o Removable qua IDList).
- Jump List: 9 LNK, deu tro `C:\Windows\System32\GettingStarted.exe`.
- Shellbag: user duyet `D:\AKMonitor\logs\pic` va vai thu muc Desktop/Downloads/Documents.
