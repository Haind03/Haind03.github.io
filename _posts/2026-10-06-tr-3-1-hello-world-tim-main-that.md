---
title: "Bài 3.1: Hello world dưới kính hiển vi, tìm cho ra main thật"
date: 2026-10-06 08:25:00 +0700
categories: ["Technique Reverse", "Phần 3 · C: ngôn ngữ gốc của mọi thứ"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
Bạn viết đúng ba dòng C, biên dịch, mở trong Ghidra. Đáng lẽ thấy ngay `main`, nhưng cái đập vào mặt bạn lại là một hàm tên lạ hoắc như `entry`, `start`, hay `__scrt_common_main_seh`, bên trong gọi cả chục hàm chẳng liên quan gì tới "hello world". Chào mừng tới sự thật đầu tiên của reverse native: **entry point không phải main của bạn.** Bài này dạy cách len qua đống khởi tạo đó để tới đúng dòng code tác giả viết.

## Vì sao có đống code trước main

![Từ entry point qua CRT startup tới main thật](/assets/img/technique-reverse/assets/phan-03/crt-to-main.svg)

Khi hệ điều hành nạp chương trình, nó không nhảy thẳng vào `main`. Nó nhảy vào **entry point** ghi trong header (trường `AddressOfEntryPoint` của PE, hay `e_entry` của ELF). Entry point này trỏ tới code khởi tạo của C runtime (CRT), không phải code bạn viết.

CRT startup phải làm một mớ việc dọn đường trước khi `main` chạy được:

- Dựng môi trường C: khởi tạo heap, luồng, locale.
- Lấy `argc`, `argv`, biến môi trường `envp` để truyền cho `main`.
- Chạy các **global constructor**: biến toàn cục cần khởi tạo, hàm đánh dấu `__attribute__((constructor))`, và trên C++ là constructor của mọi object toàn cục.
- Gọi `main`.
- Lấy giá trị `main` trả về, truyền cho `exit` để kết thúc gọn gàng.

Nói cách khác, `main` chỉ là một hàm được CRT gọi ở giữa, không phải điểm bắt đầu thật. Hiểu điều này thì bạn không hoảng khi thấy rừng code lạ, mà biết mình chỉ cần lướt qua nó để tới `main`.

## Trên Linux: đi theo __libc_start_main

Binary ELF động trên Linux theo một khuôn rất dễ nhận. Entry point `_start` làm vài việc nhỏ rồi gọi `__libc_start_main`, và đây là chỗ hay: **con trỏ main được truyền làm tham số đầu tiên.**

Nhìn đoạn `_start` điển hình trên x86-64 (cú pháp Intel):

```asm
_start:
    xor  ebp, ebp
    mov  r9, rdx            ; rtld_fini
    pop  rsi                ; argc
    mov  rdx, rsp           ; argv
    and  rsp, 0FFFFFFFFFFFFFFF0h
    push rax
    push rsp
    lea  r8,  [init]        ; __libc_csu_init (hoặc tương đương)
    lea  rcx, [fini]        ; __libc_csu_fini
    lea  rdi, [main]        ; <-- ĐÂY: tham số đầu của __libc_start_main chính là main
    call __libc_start_main
```

Quy tắc vàng: tìm lời gọi `__libc_start_main`, rồi nhìn **rdi** (tham số đầu trên Linux x64). Giá trị nạp vào rdi ngay trước đó, thường bằng một `lea rdi, [sub_xxxx]`, chính là địa chỉ `main`. Nhảy vào đó là bạn đã ở nhà.

Với libc mới hơn (glibc dùng `__libc_start_call_main`) chi tiết có đổi chút, nhưng nguyên tắc "main là tham số truyền vào hàm start của libc" vẫn đúng. Ghidra và IDA thường tự nhận ra và đặt tên `main` giúp bạn, nhưng khi chúng đoán sai hoặc binary bị tước symbol (stripped), bạn tự lần bằng tay như trên.

## Trên Windows: main là hàm nhận 3 tham số

Binary PE do MSVC biên dịch rắc rối hơn. Entry point thường là `mainCRTStartup` (cho app console) hoặc `wWinMainCRTStartup` (cho app GUI), bên trong gọi một hàm bọc như `__scrt_common_main_seh` làm đủ thứ khởi tạo, cài đặt SEH, chạy constructor, rồi mới gọi `main`.

Không có một hàm tên đẹp như `__libc_start_main` để bám. Thay vào đó dùng mấy dấu hiệu sau, theo thứ tự tiện dùng:

1. **Đi từ chuỗi.** Đây là cách nhanh nhất. Chuỗi "Hello, world" của bạn nằm trong `.rdata`. Mở Strings window, bấm vào nó, xem xref. Nơi dùng chuỗi đó gần như chắc là `main` (hoặc hàm `main` gọi trực tiếp). Với hello world, xref từ chuỗi đưa bạn tới đúng chỗ gọi `printf`/`puts`, tức là thân `main`.

2. **Tìm hàm nhận 3 tham số argc/argv/envp.** Trong rừng hàm CRT, `main` nổi bật ở chỗ nó được gọi với ba tham số (rcx=argc, rdx=argv, r8=envp theo Win64), và giá trị nó trả về được dùng làm mã thoát. Hàm bọc cuối cùng gọi tới một hàm có hình dạng đó chính là nơi gọi `main`.

3. **Theo call tới CRT I/O.** `printf`, `puts`, `std::cout` chỉ xuất hiện trong code người dùng, không có trong phần dọn dẹp CRT. Tìm chúng là khoanh được vùng code thật.

## Đọc thử: main của hello world

Sau khi lần tới nơi, thân `main` của một hello world tối giản trông cỡ thế này (MSVC, rút gọn):

```asm
main:
    sub  rsp, 28h              ; dựng stack frame + shadow space
    lea  rcx, aHelloWorld      ; rcx = con trỏ tới "Hello, world\n"
    call printf                ; printf("Hello, world\n")
    xor  eax, eax              ; eax = 0  (return 0)
    add  rsp, 28h
    ret
```

Dịch ngược ra C:

```c
int main(void) {
    printf("Hello, world\n");   // lea rcx, chuỗi; call printf
    return 0;                   // xor eax, eax
}
```

Đúng ba dòng bạn viết. Tất cả phần còn lại trong file là CRT, và một khi đã biết nó là CRT thì bạn lướt qua không cần đọc. Đó chính là kỹ năng cốt lõi: không phải đọc hết, mà là biết chỗ nào bỏ qua.

## Mẹo nhận diện nhanh

- **FLIRT/signature.** IDA Pro có thư viện signature nhận ra hàm CRT và thư viện chuẩn, tự đặt tên chúng, nhờ đó code của bạn nổi bật giữa đống đã được gắn nhãn. Bài 3.4 nói kỹ.
- **Binary tĩnh (static) thì CRT phình to.** Biên dịch với `-static` hay link tĩnh khiến cả libc nằm trong file, số hàm tăng vọt. Đừng sợ, kỹ thuật tìm main vẫn vậy.
- **Stripped binary** mất hết tên hàm, nhưng entry point và cấu trúc start thì không mất, nên cách lần theo tham số vẫn chạy.

## Lab tự làm

Mã nguồn và hướng dẫn: [labs/3.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/3.1).

Tóm tắt nhiệm vụ:
- Build cùng một `hello.c` bằng `gcc` (Linux) và MSVC (Windows).
- Mở trong Ghidra hoặc IDA, bắt đầu từ entry point, tự lần tới `main` thật bằng hai cách: theo `__libc_start_main`/hàm 3 tham số, và đi ngược từ chuỗi.
- So sánh lượng code CRT trước main giữa hai compiler.

Lời giải chi tiết trong [labs/3.1/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/3.1/solution.md), nhưng tự làm trước đã.

## Checklist ghi nhớ
- Entry point trong header trỏ tới CRT startup, không phải `main` của bạn.
- CRT dựng môi trường, lấy argc/argv/envp, chạy global constructor, rồi mới gọi `main`.
- Linux: tìm `call __libc_start_main`, `main` là tham số trong **rdi**.
- Windows: không có hàm tên đẹp, đi từ chuỗi (xref) hoặc tìm hàm nhận 3 tham số argc/argv/envp.
- `printf`/`puts`/`cout` chỉ có trong code người dùng, bám chúng để khoanh vùng.
- Biết nhận ra CRT để bỏ qua nó mới là kỹ năng, không phải đọc hết.

---
Phần trước: [Bộ công cụ](/posts/tr-2-8-giam-sat-he-thong/) · [Về mục lục](/technique-reverse/) · Bài tiếp: 3.2 Biến, con trỏ, mảng, chuỗi trong assembly
