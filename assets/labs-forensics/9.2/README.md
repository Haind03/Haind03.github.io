# Lab 9.2 - MITRE ATT&CK mapping (EXERCISE)

Day la mot EXERCISE (bai tap tu duy), KHONG phai lab phat hien tu dong. Mapping
artifact -> technique la viec cua nguoi phan tich; khong co cong cu nao "chay ra ket qua"
thay ban. Script o day chi ho tro: no lay bang mapping da soan san (dua tren cac lab
2.2 / 7.1 / 7.2 / 7.3 / 9.1) va xuat ra mot ATT&CK Navigator layer + liet ke tactic con trong.

## Chay (phan ho tro)
```
python3 -I build_layer.py    # in bang mapping, chi ra tactic con trong, ghi navigator_layer.json
```
Import `navigator_layer.json` vao https://mitre-attack.github.io/attack-navigator/ (Open Existing Layer).

## File trong lab
- `build_layer.py` - bang mapping + sinh Navigator layer.
- `navigator_layer.json` - artifact layer (< 2 MB), import thang vao ATT&CK Navigator.
- `transcript.txt` - output THAT.
- README nay.

## Bang mapping (dua tren cac lab khac)
| Technique  | Tactic              | Artifact                                  | Nguon     |
|------------|---------------------|-------------------------------------------|-----------|
| T1105      | command-and-control | HTTP tai payload MZ                        | 7.1 / 7.2 |
| T1071.001  | command-and-control | C2 beacon nhip deu + jitter :443          | 7.3       |
| T1071.004  | command-and-control | DNS tunnel base32 tren domain cha         | 7.3       |
| T1048.003  | exfiltration        | Du lieu tuon ra qua DNS                    | 7.3       |
| T1190      | initial-access      | upload.php webshell                        | 9.1       |
| T1505.003  | persistence         | webshell ton tai lau dai                   | 9.1       |
| T1059.004  | execution           | ELF dropper /tmp/.cache/sysupd             | 9.1       |
| T1053.003  | persistence         | /etc/cron.d/apache-check                   | 9.1       |
| T1098.004  | persistence         | /root/.ssh/authorized_keys                 | 9.1       |
| T1560.001  | collection          | exfil.tar.gz staging                       | 9.1       |
| T1070.004  | defense-evasion     | file bi xoa (exfil.tar.gz, lab 2.2)        | 2.2 / 9.1 |

## Nhiem vu EXERCISE
1. Voi moi tactic CON TRONG (script in ra: reconnaissance, resource-development,
   privilege-escalation, credential-access, discovery, lateral-movement, impact),
   viet mot gia thuyet + noi se di kiem chung (log nao, artifact nao).
2. Bo sung technique khi tim them bang chung; sua `MAPPING` trong `build_layer.py` roi chay lai.
3. Mo layer trong Navigator, comment moi o bang artifact nguon va thoi diem (lay tu timeline 9.1).
4. Viet mot doan 5 cau ke lai chuoi tan cong theo dung thu tu thoi gian.

## Luu y
- Thieu cong cu ghi nhan KHAC voi thieu hanh vi. Khong thay Credential Access chua chac khong co,
  co the chi vi khong bat log phu hop. "Khong tim thay" cung la mot ket luan, nhung phai noi ro ly do.
