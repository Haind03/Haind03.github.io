---
title: "Bài 15.5: Anti-VM và anti-sandbox, khi mẫu biết nó đang bị soi"
date: 2026-10-06 09:30:00 +0700
categories: ["Technique Reverse", "Phần 15 · Anti-Reverse chuyên sâu và cách vượt qua"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
Bạn dựng một lab tử tế theo Bài 0.3, kéo mẫu vào VM, nhấn chạy, và nó chẳng làm gì. Không gọi mạng, không ghi file, thoát êm ru. Dễ tưởng mẫu hỏng hoặc vô hại. Thật ra nó vừa nhìn quanh, thấy mình đang ngồi trong máy ảo, và quyết định đóng kịch. Đây là anti-VM và anti-sandbox, và hiểu nó là điều kiện để phân tích động thành công.

Khác với anti-debug (nhắm vào người đang gắn debugger), anti-VM nhắm vào môi trường: VMware, VirtualBox, QEMU, hay các sandbox tự động như Cuckoo, CAPE, các dịch vụ online. Logic của malware rất đơn giản: nhà nghiên cứu chạy tôi trong VM, người dùng thật chạy tôi trên máy thật, nên nếu thấy VM thì im lặng để khỏi bị phân tích.

Bài này đi qua các cách kiểm tra phổ biến, cách nhận ra chúng khi đọc code, và cách làm cho VM của bạn đủ giống thật để mẫu chịu diễn.

## CPUID, câu hỏi thẳng thừng nhất

Lệnh `cpuid` của CPU trả về thông tin về bộ xử lý, và nó có hai chỗ lộ hypervisor.

Thứ nhất, khi gọi `cpuid` với `eax = 1`, bit 31 của `ecx` là "hypervisor present bit". Trên máy thật bit này là 0, trong gần như mọi VM nó là 1. Chỉ một bit, nhưng đủ để tố cáo.

```asm
    mov  eax, 1
    cpuid
    bt   ecx, 31        ; kiểm bit 31
    jc   running_in_vm  ; carry = 1 thì đang trong hypervisor
```

Thứ hai, khi gọi `cpuid` với `eax = 0x40000000`, VM trả về một vendor string trong `ebx:ecx:edx`. VMware trả "VMwareVMware", VirtualBox/KVM trả "KVMKVMKVM", Hyper-V trả "Microsoft Hv", Xen trả "XenVMMXenVMM". Máy thật trả rác hoặc rỗng.

```asm
    mov  eax, 0x40000000
    cpuid
    ; ebx, ecx, edx giờ chứa chuỗi kiểu "VMwareVMware"
```

Thấy `cpuid` với hằng `0x40000000` trong code là gần như chắc chắn đang có một bài kiểm tra hypervisor. Đây là chỗ nên đặt breakpoint đầu tiên.

## Dấu vết để lại trên hệ thống (artefact)

VM và tool khách của nó để lại hàng loạt dấu vết mà malware quét tìm:

- **Registry**: các key như `HKLM\SOFTWARE\VMware, Inc.\VMware Tools`, `HKLM\HARDWARE\...\SystemBiosVersion` chứa "VBOX" hoặc "VMWARE", key của VirtualBox Guest Additions.
- **File và driver**: `C:\Windows\System32\drivers\vmmouse.sys`, `vmhgfs.sys`, `VBoxMouse.sys`, `VBoxGuest.sys`, thư mục cài VMware Tools.
- **Service và process**: `vmtoolsd.exe`, `VBoxService.exe`, `vmware.exe`.
- **Device**: tên ổ đĩa chứa "VMware" hay "VBOX", card màn hình "VirtualBox Graphics Adapter".

Trong code, các check này hiện ra dưới dạng lời gọi `RegOpenKeyEx`, `CreateFile`, `Process32Next`, `GetAdaptersInfo` với tham số là các chuỗi đặc trưng ở trên. Mẹo: chạy `strings` hay FLOSS trên mẫu, thấy một đống chuỗi "VBoxGuest", "vmtoolsd", "VMware" là biết ngay nó có anti-VM.

## MAC address và phần cứng

Mỗi nhà sản xuất card mạng có một tiền tố MAC (OUI) riêng. VM dùng tiền tố cố định: VMware hay dùng `00:05:69`, `00:0C:29`, `00:1C:14`, `00:50:56`; VirtualBox dùng `08:00:27`. Malware đọc MAC qua `GetAdaptersInfo` rồi so ba byte đầu.

Phần cứng khác cũng bị soi: số nhân CPU (`GetSystemInfo`, VM phân tích thường chỉ 1-2 nhân), dung lượng RAM (`GlobalMemoryStatusEx`, dưới 2-4 GB là đáng ngờ), kích thước ổ đĩa (dưới 60 GB). Máy phân tích thường được cấu hình tối thiểu, và chính sự tối thiểu đó tố cáo nó.

## Dấu hiệu của sandbox tự động

Sandbox khác VM thủ công ở chỗ không có người ngồi điều khiển, và nó tua nhanh để kịp phân tích hàng nghìn mẫu mỗi ngày. Malware khai thác đúng hai điểm đó:

- **Thiếu tương tác người dùng**: kiểm tra chuột có di chuyển không (`GetCursorPos` hai lần cách nhau, nếu y hệt thì không có người), có cửa sổ foreground đổi không, có double-click không. Không có ai tương tác thì khả năng cao là sandbox.
- **Sleep skipping**: malware gọi `Sleep(600000)` (10 phút) rồi làm việc. Sandbox để kịp giờ thường "tua nhanh" sleep, trả về ngay. Malware đo thời gian thật trước và sau `Sleep` (bằng `GetTickCount` hay thời gian hệ thống); nếu 10 phút trôi qua mà đồng hồ chỉ nhảy vài giây thì biết đang bị tua, và im lặng.
- **Tên máy/user đặc trưng**: nhiều sandbox dùng username như "sandbox", "malware", "virus", "john doe", hay computer name mẫu. Malware so danh sách này.

## Cách vượt qua: làm VM giống thật

Khi phân tích, mục tiêu của bạn là làm mẫu tin rằng nó đang trên máy thật. Có hai hướng.

Hướng thứ nhất, hardening cái VM: gỡ VMware Tools/Guest Additions (hoặc không cài), đổi MAC sang tiền tố của card thật, tăng số nhân CPU và RAM, tạo file và lịch sử sử dụng giả cho giống máy người dùng, đổi tên máy và user sang bình thường, thêm nhiều nhân và ổ đĩa lớn. Có các script cộng đồng như VBoxHardenedLoader, hoặc dùng QEMU với cấu hình che giấu.

Hướng thứ hai, khi đã biết chỗ check (nhờ phân tích tĩnh/động), đơn giản là patch hoặc hook: đặt breakpoint tại `cpuid` rồi sửa `ecx` xoá bit 31; đặt breakpoint tại `RegOpenKeyEx` cho các key VM rồi ép trả về lỗi "không tìm thấy"; patch nhánh `jc running_in_vm` thành không nhảy. Cách này nhanh khi bạn chỉ cần vượt qua vài check cụ thể để xem phần hành vi thật.

Trong thực tế hai hướng bổ trợ nhau: hardening để qua được phần lớn mẫu tự động, còn patch/hook cho những check tinh vi mà hardening không lo hết.

## Lab tự làm

Xem `labs/15.5/`. Bạn sẽ build một chương trình C minh hoạ CPUID hypervisor check cùng vài artefact check, chạy nó trên máy thật và trong VM để thấy kết quả khác nhau, rồi tập patch cho nó luôn báo "máy thật".

## Checklist ghi nhớ
- Mẫu "không làm gì" trong VM thường là có anti-VM, không phải hỏng.
- `cpuid` eax=1 bit 31 của ecx, và `cpuid` eax=0x40000000 trả vendor string, là hai check hypervisor kinh điển.
- Artefact: registry/file/driver/service/process của VMware và VirtualBox, lộ qua strings.
- MAC OUI (00:0C:29, 08:00:27...), ít nhân CPU, ít RAM, ổ nhỏ đều là cờ VM.
- Sandbox lộ qua thiếu tương tác chuột và sleep skipping.
- Vượt qua: hardening VM cho giống thật, hoặc patch/hook từng check đã xác định.
