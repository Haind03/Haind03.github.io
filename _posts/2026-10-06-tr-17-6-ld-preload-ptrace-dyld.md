---
title: "Bài 17.6: LD_PRELOAD, ptrace và DYLD_INSERT_LIBRARIES"
date: 2026-10-06 09:45:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Trên Windows bạn hook bằng Detours, IAT hay inline hook (bài [17.3](/posts/tr-17-3-hooking-windows-iat-inline-detours/)). Trên Linux và macOS có một cách sạch hơn nhiều, dựng sẵn trong chính loader của hệ điều hành: bạn bảo nó nạp thư viện của bạn trước thư viện chuẩn, thế là hàm của bạn đè lên hàm libc. Không cần ghi đè byte, không cần code cave, chỉ một biến môi trường. Bài này dùng nó để lộ password của một crackme, và nói luôn về ptrace, cơ chế đứng sau mọi debugger Linux.

## LD_PRELOAD: chen thư viện của bạn lên đầu hàng

Khi một chương trình Linux gọi `strcmp`, lời gọi đó được phân giải (resolve) tại thời điểm chạy qua dynamic linker. Linker tìm hàm trong danh sách thư viện theo thứ tự, và hàm đầu tiên khớp tên sẽ thắng. `LD_PRELOAD` chèn một thư viện của bạn lên **đầu** danh sách đó. Nếu thư viện của bạn cũng định nghĩa `strcmp`, phiên bản của bạn được gọi thay vì của libc.

Đây là tính năng hợp pháp của glibc, dùng cho debug, profiling, vá nóng, và với dân RE là để hook mà không đụng tới binary. Vì nó hoạt động ở ranh giới lời gọi hàm thư viện, nó chỉ chặn được các hàm gọi qua PLT (hàm từ thư viện động), không chặn được hàm tĩnh hay inline. Nhưng `strcmp`, `malloc`, `fopen`, `getenv` thì bắt được hết.

### Viết một hook

Mẹo quan trọng: hook của bạn thường vẫn muốn gọi hàm thật (để chương trình chạy bình thường, bạn chỉ chen vào quan sát). Lấy con trỏ hàm thật bằng `dlsym(RTLD_NEXT, "strcmp")`, nghĩa là "tìm `strcmp` tiếp theo trong chuỗi, bỏ qua cái của tôi".

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>

static int (*real_strcmp)(const char *, const char *) = NULL;

int strcmp(const char *a, const char *b) {
    if (!real_strcmp)
        real_strcmp = dlsym(RTLD_NEXT, "strcmp");
    fprintf(stderr, "[hook] strcmp(\"%s\", \"%s\")\n", a, b);
    return real_strcmp(a, b);   // gọi hàm thật, chương trình chạy như thường
}
```

Build thành shared object rồi nạp:

```sh
gcc -shared -fPIC -o hook.so hook.c -ldl
LD_PRELOAD=./hook.so ./crackme
```

Mỗi lần crackme so chuỗi, hook in ra cả hai toán hạng. Nếu crackme dùng `strcmp(input, secret)` thì password đúng lộ ngay trên màn hình, không cần mở IDA. Phần lab bên dưới làm đúng việc này, chạy thật ra kết qua.

Vì sao log ra `stderr` chứ không `stdout`: để output của hook không lẫn vào output của chương trình, tiện lọc.

## ptrace: nền móng của mọi debugger Linux

`gdb`, `strace`, `ltrace` đều đứng trên một syscall duy nhất: `ptrace`. Một tiến trình gọi `ptrace(PTRACE_ATTACH, pid, ...)` để gắn vào tiến trình khác, rồi đọc/ghi thanh ghi và bộ nhớ, đặt breakpoint, step. Hiểu điều này giải thích hai thứ.

Thứ nhất, `strace ./prog` cho bạn thấy mọi syscall chương trình gọi (open, read, write, connect), còn `ltrace ./prog` cho thấy mọi lời gọi thư viện (giống LD_PRELOAD nhưng xem hết). Hai lệnh này là cách triage động nhanh nhất trên Linux, chạy trước khi mở disassembler.

Thứ hai, ptrace là chỗ anti-debug Linux hay cài bẫy. Một tiến trình **chỉ có thể bị một tracer gắn vào tại một thời điểm**. Nên thủ thuật anti-debug kinh điển là chương trình tự gọi `ptrace(PTRACE_TRACEME, 0, 0, 0)` với chính nó: nếu thành công, nó biết chưa ai debug nó; nếu đã có gdb gắn vào thì lời gọi này thất bại (trả về -1), và chương trình biết mình đang bị theo dõi rồi thoát hoặc rẽ nhánh giả.

```c
if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) {
    // da co debugger gan vao -> thoat hoac lam sai di
    exit(1);
}
```

Cách nhận ra khi reverse: tìm lời gọi `ptrace` (syscall số 101 trên x86-64) ngay đầu chương trình. Cách vượt: dùng LD_PRELOAD hook luôn `ptrace` trả về 0, hoặc patch nhánh, hoặc chạy dưới công cụ không dùng ptrace. Vòng tròn đẹp: chính LD_PRELOAD của mục trên lại là cách bẻ anti-debug ptrace.

```c
// hook vo hieu anti-debug ptrace: luon bao "khong co ai theo doi"
long ptrace(int request, ...) { return 0; }
```

## DYLD_INSERT_LIBRARIES: bản macOS

macOS có cơ chế tương đương tên là `DYLD_INSERT_LIBRARIES` (dyld là dynamic linker của macOS). Ý tưởng y hệt: chèn một dylib nạp trước để ghi đè hàm. Hàm ghi đè cần đánh dấu để dyld biết thay thế (interpose), qua một section `__interpose` thay vì chỉ định nghĩa trùng tên.

Khác biệt lớn là **System Integrity Protection (SIP)**: macon hiện đại chặn `DYLD_INSERT_LIBRARIES` với các tiến trình hệ thống và binary có hardened runtime, nên nó chỉ dùng được với binary của bạn hoặc binary không ký cứng. Đó là lý do trên macOS người ta hay chuyển sang Frida (bài [17.2](/posts/tr-17-2-frida-toan-tap/)) cho tiện.

## Khi nào dùng cái nào

- Muốn xem nhanh chương trình Linux đụng file/mạng/syscall nào: `strace`, `ltrace`, không cần viết gì.
- Muốn hook một hàm thư viện cụ thể để đọc hoặc sửa tham số, trên binary của mình hoặc mẫu trong lab: LD_PRELOAD, gọn và sạch.
- Gặp anti-debug ptrace: LD_PRELOAD hook `ptrace` trả 0.
- Trên macOS, hoặc cần linh hoạt hơn nhiều, hoặc cần cùng một script chạy khắp nền tảng: Frida.

LD_PRELOAD không phải thần dược. Nó không chạm được hàm tĩnh, hàm inline, hay lời gọi syscall trực tiếp không qua libc. Khi đó quay lại debugger hoặc Frida.

## Lab tự làm

Thư mục [labs/17.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/17.6) có một crackme gọi `strcmp` để so password, và một thư viện `hook.c` ghi đè `strcmp` để log. Nhiệm vụ: build cả hai, chạy crackme với `LD_PRELOAD` và đọc password đúng rơi ra từ log, mà không cần disassemble. Sau đó thử tự viết một hook `ptrace` để hiểu cách vô hiệu anti-debug.

Kết quả tham chiếu (đã chạy thật bằng gcc trên Linux) nằm trong [labs/17.6/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/17.6/solution.md).

## Checklist ghi nhớ
- LD_PRELOAD nạp thư viện của bạn trước libc, hàm trùng tên của bạn thắng. Chỉ chặn hàm gọi qua PLT (thư viện động).
- Trong hook, lấy hàm thật bằng `dlsym(RTLD_NEXT, "ten")` rồi gọi lại để chương trình chạy bình thường.
- Hook `strcmp` lộ ngay password nếu crackme so chuỗi bằng strcmp.
- ptrace là nền của gdb/strace/ltrace. Một tiến trình chỉ bị một tracer gắn vào.
- Anti-debug Linux hay dùng `ptrace(PTRACE_TRACEME)`: thất bại nghĩa là đã bị debug. Vượt bằng LD_PRELOAD hook ptrace trả 0.
- macOS có `DYLD_INSERT_LIBRARIES` nhưng bị SIP hạn chế, nên thường chuyển sang Frida.
