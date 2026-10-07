---
title: "Bài 17.3: Hooking trên Windows, IAT hook và inline hook"
date: 2026-10-06 09:42:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Hook nghĩa là chen vào giữa một lời gọi hàm để lời gọi đó chạy qua code của bạn trước. Nghe giống chuyện của malware, nhưng thực ra đây là nền tảng của rất nhiều thứ hợp pháp: EDR giám sát hành vi bằng hook, Frida instrument bằng hook, tool tương thích vá API cũ bằng hook, và chính bạn khi phân tích sẽ hook để xem tham số. Hiểu cơ chế hook giúp bạn vừa dùng được nó, vừa phát hiện được khi người khác dùng nó.

Có hai họ hook trên Windows mà bạn gặp suốt: IAT hook và inline hook. Chúng khác nhau về chỗ chen vào.

## IAT hook: đổi địa chỉ trong bảng import

Nhớ lại [Bài 1.7](/posts/tr-1-7-dinh-dang-pe/): khi một chương trình gọi `MessageBoxW`, nó không nhảy thẳng tới hàm trong user32.dll. Nó đọc địa chỉ từ một ô trong Import Address Table (IAT), rồi `call` qua ô đó. Loader điền sẵn địa chỉ thật vào ô này lúc nạp.

IAT hook lợi dụng đúng chỗ đó: tìm ô IAT của hàm muốn chặn, ghi đè địa chỉ thật bằng địa chỉ hàm của bạn. Từ đó mọi lời gọi qua IAT sẽ chạy vào hàm bạn. Hàm bạn làm việc của mình (log, sửa tham số) rồi gọi tiếp địa chỉ thật đã lưu.

```
Trước hook:   call [IAT_MessageBoxW]  ->  user32!MessageBoxW
Sau hook:     call [IAT_MessageBoxW]  ->  my_hook  ->  (gọi tiếp) user32!MessageBoxW
```

Ưu điểm: sạch, không sửa code của hàm đích, dễ gỡ. Nhược điểm quyết định: chỉ chặn được lời gọi **đi qua IAT**. Nếu chương trình lấy địa chỉ hàm bằng `GetProcAddress` rồi gọi trực tiếp, hoặc gọi hàm nội bộ không có trong IAT, thì IAT hook không thấy gì. Vì thế IAT hook hợp cho giám sát ở mức thô, không toàn diện.

## Inline hook: ghi đè đầu hàm bằng một jump

Inline hook (còn gọi trampoline hook hoặc detour) chen vào tận thân hàm đích, nên bắt được mọi lời gọi dù đi đường nào.

Ý tưởng: ghi đè vài byte đầu của hàm đích bằng một lệnh `jmp` nhảy tới hook của bạn. Nhưng làm vậy thì mất mấy byte gốc, không gọi lại hàm thật được nữa. Nên trước khi ghi đè, bạn chép mấy byte đầu đó ra một vùng riêng gọi là trampoline, rồi nối thêm một `jmp` quay lại phần còn lại của hàm đích. Muốn gọi hàm thật, bạn gọi trampoline.

```
Hàm gốc (prologue điển hình Win64):
    mov  [rsp+8], rcx      ; 4 byte
    push rdi               ; ...

Sau inline hook, đầu hàm bị thay bằng:
    jmp  my_hook           ; thường E9 + offset 32-bit, hoặc FF25 jmp [addr] 64-bit

Trampoline (vùng riêng) giữ lại việc đã mất rồi quay về:
    mov  [rsp+8], rcx      ; byte gốc đã chép ra
    jmp  func+N            ; nhảy về hàm gốc sau phần đã ghi đè
```

Chi tiết phiền phức: lệnh x86 dài ngắn khác nhau, nên bạn phải chép trọn các lệnh bị đè chứ không cắt giữa lệnh (cần một disassembler độ dài nhỏ, gọi là length disassembler). Nếu trong mấy byte đó có lệnh dùng địa chỉ tương đối (`rip`-relative, `call rel32`), chép thô sang chỗ khác sẽ sai, phải sửa lại offset. Mấy thư viện dưới đây lo hết việc này cho bạn.

## Thư viện làm sẵn

Không ai tự tay vá byte trong thực tế. Ba thư viện hay gặp:

- **Microsoft Detours**: kinh điển, của chính Microsoft, API gọn (`DetourAttach`/`DetourDetach`), xử lý trampoline và relocation tự động.
- **MinHook**: nhỏ, nhẹ, mã nguồn mở, hỗ trợ x86 và x64 tốt, rất phổ biến trong cộng đồng. API `MH_CreateHook`, `MH_EnableHook`.
- **PolyHook2**: hiện đại, nhiều kiểu hook (inline, IAT, VMT cho C++ vtable), C++.

Khi reverse một binary, thấy nó link hoặc nhúng một trong mấy cái này là gần như chắc nó đang đi hook thứ gì đó, đáng để xem nó hook cái gì.

## EDR và góc nhìn phát hiện

Phần mềm bảo mật endpoint (EDR) thường inline hook các API nhạy cảm trong ntdll (như `NtAllocateVirtualMemory`, `NtWriteVirtualMemory`) để quan sát hành vi đáng ngờ. Đây là lý do khi bạn mở ntdll của một máy có EDR trong debugger, đầu nhiều hàm `Nt*` lại là một `jmp` lạ thay vì prologue chuẩn.

Và đó cũng chính là cách **phát hiện** hook, nối lại [Bài 15.7](/posts/tr-15-7-anti-attach-dump-hook/): so byte đầu của hàm trong bộ nhớ với byte gốc đọc từ file DLL trên đĩa. Khác nhau ở prologue, nhất là một `jmp` (`E9` hoặc `FF 25`) nằm ngay đầu, là dấu hiệu hàm đã bị hook.

```
Đầu hàm sạch:     mov [rsp+8], rcx   (48 89 4C 24 08 ...)
Đầu hàm bị hook:  jmp <somewhere>    (E9 xx xx xx xx ...)
```

Malware tinh vi phát hiện EDR hook theo cách này rồi tự khôi phục byte gốc (unhook) để né giám sát. Bạn khi phân tích cũng dùng chính kỹ thuật so sánh đó để biết hàm nào đang bị can thiệp.

## Phân biệt nhanh hai loại khi phân tích

- Thấy một ô trong IAT trỏ tới vùng không thuộc DLL gốc (ví dụ trỏ vào một module lạ hay vùng cấp phát động): nghi IAT hook.
- Thấy đầu một API là `jmp`/`push+ret` bất thường thay vì prologue quen: nghi inline hook.
- Cả hai đều dẫn bạn tới hàm hook, cứ follow để biết nó làm gì.

## Lab tự làm

Xem [labs/17.3/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/17.3): quan sát một inline hook trong bộ nhớ, nhận ra `jmp` ở đầu hàm, và so prologue để phân biệt hàm bị hook với hàm sạch.

## Checklist ghi nhớ
- Hook = chen vào giữa lời gọi hàm, nền tảng của EDR, Frida, tool tương thích, và phân tích.
- IAT hook: đổi con trỏ trong Import Address Table, chỉ bắt lời gọi qua IAT, sạch nhưng không toàn diện.
- Inline hook: ghi đè đầu hàm bằng `jmp`, trampoline giữ byte gốc để gọi lại hàm thật, bắt mọi lời gọi.
- Inline hook phải chép trọn lệnh và sửa địa chỉ tương đối, nên dùng Detours/MinHook/PolyHook2.
- Phát hiện hook: so prologue trong bộ nhớ với byte gốc trên đĩa, một `jmp` (E9 / FF 25) ở đầu hàm là cờ đỏ.
