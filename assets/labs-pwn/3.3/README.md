# Lab 3.3 - Truyen tham so bang pop rdi + can stack (movaps)

Thuoc Bai 3.3. Nap tham so vao RDI bang gadget `pop rdi ; ret`, va xu ly bay
can stack 16 byte (movaps) bang mot gadget `ret` thua.

## File

- `callme.c` - demo: `win(magic)` goi system; gadget `pop rdi ; ret` nhet san.
- `keycheck.c` - lab: `win(code)` chi cho shell khi code == 0x1337c0de.
- `build.sh` - bien dich (gadget nhet san, -fcf-protection=none giu gadget sach).
- `exp_callme_nostack.py` - buoc 1: CO TINH quen can stack -> dinh movaps crash.
- `exp_callme.py` - buoc 2: them `ret` can stack -> shell.
- `exploit.py` - lab keycheck (offset 88) -> shell.
- `transcript.txt` - output THAT (gom ca crash movaps trong glibc 2.39).

## Build va chay

```bash
bash build.sh
python3 exp_callme_nostack.py   # in banner win roi crash (movaps)
python3 exp_callme.py           # them ret -> ===SHELL_OK=== uid=...
python3 exploit.py              # keycheck -> ===SHELL_OK=== uid=...
```

## Offset va gadget (do, khong doan)

- `callme` offset = 72, `keycheck` offset = 88 (cyclic + corefile).
- `pop rdi ; ret` = 0x401166, `ret` = 0x40101a, `win` (callme/keycheck) = 0x401168.

## Ve movaps (glibc 2.39)

Khi quen can stack, win() chay (in banner) nhung `system("/bin/sh")` crash tai
`movaps %xmm0,0x50(%rsp)` (ngay truoc `call posix_spawn` trong duong di cua
system). Them 1 gadget `ret` dua RSP ve boi so 16 la het crash.

## Moi truong

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0.
