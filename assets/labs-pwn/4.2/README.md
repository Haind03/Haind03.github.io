# Lab 4.2: shellcode tren stack khi NX tat (jmp rsp)

Bai: [4.2-nhay-vao-shellcode-jmprsp.md](../../phan-04-shellcode/4.2-nhay-vao-shellcode-jmprsp.md)

## File

- `src.c`: binary `vuln` co buffer overflow (`read(0, buf, 400)` vao `buf[64]`), kem mot ham `gadget` chua san lenh `jmp rsp` (ff e4) o dia chi co dinh.
- `build.sh`: bien dich voi NX TAT: `-z execstack -fno-stack-protector -no-pie -fcf-protection=none -O0 -g`, roi in GNU_STACK de xac nhan RWE.
- `exploit.py`: hai cach.
  - Mac dinh: `jmp rsp` (chay duoc CA KHI ASLR bat).
  - `DIRECT BUF=0x...`: nhay thang vao dia chi stack, chi khi ASLR tat, co NOP sled.
- `transcript.txt`: output THAT (ca hai cach).

## Chay

```bash
bash build.sh

# Cach 1 (mac dinh): jmp rsp, ASLR co the de bat
/root/techlabs/venv/bin/python3 exploit.py

# Cach 2: nhay thang vao stack, phai tat ASLR truoc
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
# lay &buf: gdb -q -batch -ex 'break read' -ex 'run < /dev/null' -ex 'printf "%p\n", $rsi' ./vuln
/root/techlabs/venv/bin/python3 exploit.py DIRECT BUF=0x7fffffffe9f0
echo 2 | sudo tee /proc/sys/kernel/randomize_va_space   # khoi phuc
```

## Moi truong kiem thu

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0, pwntools.

- Cach jmp rsp: 8/8 lay shell voi ASLR BAT.
- Cach DIRECT: lay shell voi ASLR TAT.

## Ket qua

- offset toi saved RIP = 72 (do bang cyclic).
- gadget `jmp rsp` @ `0x40114a`.
- Lay shell `uid=0(root)` ca hai cach.

## Luu y

Lan dau exploit chay chap chon (~50%) vi `read(0, buf, 400)` greedy nuot luon lenh shell
gui ngay sau payload. Them `sleep(0.3)` truoc khi go lenh la on dinh. Day la cam bay harness,
khong phai loi ky thuat jmp rsp (xem phan Cam bay cua bai hoc).
