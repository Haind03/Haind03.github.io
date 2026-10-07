---
title: "Bài 1.2: Bộ nhớ tiến trình, bản đồ nơi mọi thứ diễn ra"
date: 2026-10-06 08:05:00 +0700
categories: ["Technique Reverse", "Phần 1 · Nền tảng máy tính cho RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Khi bạn double-click một file `.exe`, hệ điều hành không chạy thẳng từ đĩa. Nó tạo ra một tiến trình (process), cấp cho tiến trình đó một vùng bộ nhớ riêng, nạp code vào, rồi mới cho chạy. Hiểu bố cục vùng bộ nhớ này là hiểu nơi debugger của bạn sẽ đi lại suốt ngày. Thiếu nó, bạn nhìn một địa chỉ mà không biết nó là code, là biến, hay là rác.

## Mỗi tiến trình có một thế giới riêng

Điều đầu tiên gây bất ngờ: hai tiến trình cùng thấy địa chỉ `0x401000`, nhưng đó là hai ô nhớ vật lý hoàn toàn khác nhau. Mỗi tiến trình sống trong một không gian địa chỉ ảo (virtual address space) riêng, được cách ly. Tiến trình A không thể vô tình đọc bộ nhớ của tiến trình B.

Cơ chế này do CPU và hệ điều hành phối hợp: địa chỉ bạn thấy trong IDA hay debugger là **địa chỉ ảo** (virtual address), hệ điều hành dịch ngầm sang địa chỉ vật lý thật trong RAM. Với người làm RE, bạn gần như luôn làm việc ở mức địa chỉ ảo, nên cứ coi tiến trình có nguyên một dải địa chỉ liền mạch cho riêng mình.

Hệ quả thực tế: muốn đọc hay ghi bộ nhớ của tiến trình khác (chính là nền tảng của mọi kỹ thuật injection ở Phần 17), bạn phải nhờ hệ điều hành qua các API đặc biệt như `ReadProcessMemory`, `WriteProcessMemory`. Không có chuyện với tay sang trực tiếp.

## Bản đồ bộ nhớ của một tiến trình

![Bản đồ bộ nhớ tiến trình: code, data, heap mọc lên, stack mọc xuống, thư viện](/assets/img/technique-reverse/assets/phan-01/bo-nho-tien-trinh.svg)

Không gian địa chỉ chia thành nhiều vùng, mỗi vùng một nhiệm vụ. Từ thấp lên cao, đại khái:

```
địa chỉ thấp
  +-------------------------+
  |  Code (.text)           |  lệnh máy, chỉ đọc + thực thi
  +-------------------------+
  |  Dữ liệu đã khởi tạo    |  .data: biến toàn cục có giá trị ban đầu
  |  (.data)                |
  +-------------------------+
  |  Dữ liệu chưa khởi tạo  |  .bss: biến toàn cục = 0
  |  (.bss)                 |
  +-------------------------+
  |  Heap  --->             |  cấp phát động (malloc/new), lớn dần lên trên
  |                         |
  |         ...             |
  |                         |
  |              <--- Stack |  biến cục bộ, lời gọi hàm, lớn dần xuống dưới
  +-------------------------+
  |  Thư viện (DLL/.so)     |  kernel32, libc... được nạp vào đây
  +-------------------------+
địa chỉ cao
```

Trong x64dbg bạn mở tab Memory Map là thấy đúng bản đồ này với địa chỉ thật, quyền truy cập (R/W/X), và module nào chiếm vùng nào. Đây là một trong những cửa sổ bạn mở nhiều nhất.

### Các section chính

Một file PE hay ELF được chia thành section, và khi nạp vào bộ nhớ mỗi section thành một vùng:

- **.text** (code): chứa lệnh máy. Quyền thường là đọc + thực thi, không ghi. Khi thấy một vùng R-X, gần như chắc đó là code. (Code tự sửa mình, self-modifying code, sẽ cần quyền ghi, và đó là một dấu hiệu đáng ngờ, nói ở Phần 15.)
- **.data**: biến toàn cục đã có giá trị khởi tạo. Đọc + ghi.
- **.bss**: biến toàn cục khởi tạo bằng 0. Không tốn chỗ trên đĩa, chỉ cấp vùng rỗng lúc nạp.
- **.rdata / .rodata**: dữ liệu chỉ đọc, như hằng số và chuỗi. Chuỗi "Sai mật khẩu" của bạn thường nằm ở đây.

## Stack, nơi hàm sống và chết

Stack là vùng bạn phải hiểu kỹ nhất vì gần như mọi hàm đều dùng nó. Đặc điểm:

- Nó là một chồng (stack) đúng nghĩa: vào sau ra trước (LIFO). `push` đẩy lên, `pop` lấy ra.
- Trên x86/x64 stack **mọc xuống**: push làm con trỏ đỉnh (rsp) **giảm** địa chỉ. Nghe ngược nhưng nhớ là được.
- Mỗi lần gọi hàm, một khối gọi là stack frame được dựng lên để chứa: địa chỉ trở về (do `call` đẩy vào), các biến cục bộ của hàm, và đôi khi tham số.
- Khi hàm `ret`, frame đó bị bỏ, stack co lại về chỗ cũ.

Vì biến cục bộ nằm trên stack, trong assembly bạn thấy chúng dưới dạng `[rbp-4]`, `[rbp-8]` (tham chiếu lùi từ base pointer) hoặc `[rsp+8]` (từ đỉnh stack). Khi IDA đặt tên `var_4`, `var_8` chính là nó đang gọi tên các biến cục bộ này. Bài [1.4](/posts/tr-1-4-assembly-2-stack-calling-convention/) mổ xẻ stack frame chi tiết.

Stack cũng là trung tâm của cả mảng lỗ hổng bảo mật (stack buffer overflow): ghi quá một biến cục bộ có thể đè lên địa chỉ trở về, và kiểm soát được địa chỉ trở về là kiểm soát được luồng thực thi. Đó là chuyện của mảng exploit, nhưng gốc rễ nằm ở cách stack hoạt động.

## Heap, bộ nhớ xin lúc chạy

Khi chương trình cần vùng nhớ mà kích thước chỉ biết lúc chạy (đọc một file bao nhiêu byte, người dùng nhập chuỗi dài bao nhiêu), nó xin từ heap qua `malloc`, `new`, `HeapAlloc`. Khác stack ở chỗ:

- Lập trình viên (hoặc runtime) tự quản lý: xin thì phải trả (`free`, `delete`), quên trả là memory leak.
- Vùng heap sống lâu, không tự dọn khi hàm return như biến stack.
- Trong RE, thấy một con trỏ trỏ vào vùng heap (thường là dải địa chỉ riêng trong Memory Map) là biết đó là dữ liệu cấp phát động, ví dụ một struct hay một mảng.

## Địa chỉ không cố định: ASLR

Ngày xưa một chương trình luôn nạp ở cùng địa chỉ, ví dụ `0x400000`. Giờ hệ điều hành bật ASLR (Address Space Layout Randomization): mỗi lần chạy, code và thư viện được đặt ở địa chỉ ngẫu nhiên khác nhau, để kẻ tấn công khó đoán.

Với bạn, điều này nghĩa là: địa chỉ bạn thấy trong IDA (địa chỉ tĩnh, dựa trên base mặc định) sẽ **khác** địa chỉ thật trong debugger lúc chạy. Để khớp hai bên, người ta dùng khái niệm offset so với base của module. x64dbg có nút "follow in disassembler" và tính năng rebase giúp đồng bộ. Đừng hoảng khi địa chỉ trong IDA là `0x401500` mà trong debugger lại là `0x7FF6xx401500`, phần đuôi `401500` mới là cái cần so.

## Quyền truy cập, manh mối miễn phí

Mỗi vùng nhớ có quyền: R (read), W (write), X (execute). Đọc quyền là đọc được ý đồ:
- R-X: code bình thường.
- RW-: dữ liệu bình thường.
- RWX: vừa ghi được vừa chạy được. Hiếm trong phần mềm sạch, rất hay gặp trong malware và packer vì chúng ghi code đã giải mã vào đó rồi nhảy tới chạy. Thấy một vùng RWX trong Memory Map là giỏng tai lên.

## Checklist ghi nhớ
- Mỗi tiến trình có không gian địa chỉ ảo riêng, cách ly. Địa chỉ bạn thấy là địa chỉ ảo.
- Bố cục: code (.text), data (.data/.bss/.rdata), heap (mọc lên), stack (mọc xuống), thư viện.
- Stack: LIFO, mọc xuống, chứa biến cục bộ và địa chỉ trở về. Biến cục bộ hiện dưới dạng `[rbp-x]`.
- Heap: cấp phát động lúc chạy, phải tự giải phóng.
- ASLR làm địa chỉ đổi mỗi lần chạy, so phần offset chứ đừng so địa chỉ tuyệt đối.
- Vùng RWX là cờ đỏ, hay thấy ở packer/malware.
