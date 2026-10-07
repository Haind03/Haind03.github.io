---
title: "Bài 18.6: Reverse code ring-0, driver Windows và kernel module Linux"
date: 2026-10-06 09:52:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Tới giờ mọi thứ ta mổ đều chạy ở ring-3, user-mode, nơi một lỗi chỉ làm sập một tiến trình. Bước xuống ring-0, kernel-mode, là một thế giới khác: code ở đây chạy với toàn quyền, một lỗi nhỏ không làm sập chương trình mà làm sập cả máy (BSOD trên Windows, kernel panic trên Linux). Rootkit, anti-cheat, nhiều driver anti-debug (như TitanHide ở bài 15.9) sống ở đây, nên sớm muộn bạn cũng phải xuống.

Bài này không dạy viết driver, mà dạy đọc một driver bạn không có source, và làm sao debug nó mà không đốt cháy máy.

## Nguyên tắc đầu tiên: luôn làm trong VM

Nhắc lại cho chắc: reverse code ring-0 là lúc lab VM của bài 0.3 không còn là lựa chọn mà là bắt buộc. Lý do kỹ thuật: debug kernel cần dừng toàn bộ hệ điều hành lại, nên bạn cần hai máy, một máy chạy driver (target) và một máy điều khiển debugger (host). VM giải quyết việc này gọn gàng: target là VM, host là máy thật, nối với nhau qua named pipe hoặc network. Driver lỗi thì chỉ VM sập, snapshot lại trong vài giây.

Đừng bao giờ nạp một driver lạ lên máy thật để xem nó làm gì. Một lần là đủ nhớ.

## Windows kernel driver: file .sys

Một driver Windows (`.sys`) vẫn là file PE, y như `.exe` và `.dll` ở bài 1.7, chỉ khác subsystem là Native và nó link với `ntoskrnl.exe` thay vì `kernel32.dll`. Mở bằng IDA hay Ghidra như bình thường, nhưng các API bạn thấy sẽ là họ hàng kernel: `IoCreateDevice`, `ObReferenceObjectByHandle`, `MmGetSystemRoutineAddress`, `ZwOpenKey`, chứ không phải `CreateFileW`.

### DriverEntry, điểm vào thật

Điểm vào của driver không phải `main` mà là `DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)`. Đây là nơi bắt đầu đọc. Trong `DriverEntry`, driver thường làm mấy việc đáng chú ý:

- Tạo device object (`IoCreateDevice`) và symbolic link (`IoCreateSymbolicLink`) để user-mode gọi tới được. Tên device (ví dụ `\\Device\\MyDriver`) là manh mối tìm chương trình user-mode điều khiển nó.
- Gán các major function vào bảng `DriverObject->MajorFunction[]`. Đây là chỗ quan trọng nhất.

### Bảng MajorFunction và IOCTL

Driver giao tiếp với user-mode qua cơ chế IRP (I/O Request Packet). `DriverObject->MajorFunction` là một mảng con trỏ hàm, mỗi slot ứng với một loại request:

```
MajorFunction[IRP_MJ_CREATE]         = DriverCreateClose;   // index 0
MajorFunction[IRP_MJ_CLOSE]          = DriverCreateClose;   // index 2
MajorFunction[IRP_MJ_DEVICE_CONTROL] = DriverDeviceControl; // index 14, quan trọng nhất
```

Slot `IRP_MJ_DEVICE_CONTROL` (giá trị 0xE) gần như luôn là trái tim của driver, vì đây là nơi xử lý `DeviceIoControl` từ user-mode. Khi reverse, tìm chỗ gán slot 0xE trong `DriverEntry` rồi nhảy tới hàm đó là bạn vào ngay phần logic chính.

Trong hàm device control, driver đọc IOCTL code từ IRP (qua `IoGetCurrentIrpStackLocation`, trường `Parameters.DeviceIoControl.IoControlCode`) rồi switch theo từng mã. Mỗi IOCTL là một lệnh mà user-mode gửi xuống. Dựng lại bảng IOCTL code tương ứng với hành vi là đã hiểu được API riêng của driver.

### Lần ngược từ phía user-mode

Mẹo thực chiến: nếu bạn có cả chương trình user-mode điều khiển driver, hãy tìm lời gọi `DeviceIoControl` trong đó. Tham số thứ hai là IOCTL code, tham số buffer vào/ra cho bạn biết cấu trúc dữ liệu. Ghép hai phía user và kernel lại là hiểu trọn giao thức. Đây là lý do nhiều khi reverse driver dễ hơn khi có kèm phần user-mode.

### Debug bằng WinDbg kernel mode

Debug driver dùng WinDbg (nhắc ở bài 2.6) ở chế độ kernel:

- Trên VM target, bật kernel debugging: `bcdedit /debug on` và cấu hình transport (`bcdedit /dbgsettings net ...` hoặc serial/named pipe), rồi khởi động lại.
- Trên host, mở WinDbg, attach vào kernel qua đúng transport.
- Vài lệnh hay dùng: `lm` liệt kê module đã nạp (tìm driver của bạn), `!drvobj MyDriver 7` xem driver object và bảng major function, `bp MyDriver!DriverDeviceControl` đặt breakpoint, `!irp` xem IRP hiện tại, `dt` đọc struct.

VM target sẽ đứng hình khi bị breakpoint, đó là bình thường, host điều khiển mọi thứ.

## Linux kernel module: file .ko

Bên Linux, kernel module là file `.ko`, một ELF relocatable (nhắc bài 1.8). Mở bằng Ghidra/IDA như ELF thường.

Hai điểm vào do macro định nghĩa:

- `module_init(ham)` đăng ký hàm chạy khi nạp module (`insmod`). Đây là `DriverEntry` của Linux.
- `module_exit(ham)` chạy khi gỡ (`rmmod`).

Thông tin module (tên, license, tác giả, tham số) nằm trong section `.modinfo`, đọc nhanh bằng `modinfo file.ko`. Symbol thường còn khá nhiều vì kernel module hay giữ tên hàm, nên đọc dễ hơn driver Windows stripped.

Những gì module hay làm và đáng soi:

- Đăng ký character device hoặc entry trong `/proc`, `/sys` để nói chuyện với user-mode (tương đương device object + IOCTL của Windows). Tìm `file_operations` struct với các con trỏ `.read`, `.write`, `.unlocked_ioctl`.
- Hook syscall (một kỹ thuật rootkit kinh điển: sửa `sys_call_table` để chặn `getdents` giấu file, hoặc `kill` nhận lệnh ẩn). Thấy module đọc/ghi `sys_call_table` là cờ đỏ cần đọc kỹ.

Debug: `kgdb` nối từ một máy khác (hoặc QEMU, nối bài 18.5), hoặc dùng `qemu` chạy kernel với gdbstub (`-s -S`) rồi attach gdb từ host. In log bằng `printk` xem qua `dmesg` là cách quan sát nhẹ nhàng nhất khi chưa cần dừng kernel.

## Vì sao ring-0 khác hẳn

Vài thứ làm người quen user-mode vấp:

- Không có libc hay Win32 quen thuộc, chỉ có API kernel. Phải tra tên hàm kernel để hiểu (nối bài 1.13).
- Địa chỉ kernel dùng chung cho mọi tiến trình, không cô lập như user-mode (bài 1.2). KASLR làm base kernel ngẫu nhiên mỗi lần boot.
- Một lỗi là sập cả máy, nên vòng lặp thử sai chậm hơn nhiều. Đọc tĩnh kỹ trước khi chạy động là xứng công.
- Driver thường nhỏ và tập trung, nên một khi tìm được hàm device control thì phần còn lại gọn.

## Phạm vi và đạo đức

Nhắc lại tinh thần bài 0.2: phân tích một driver để hiểu nó làm gì, kiểm tra an toàn sản phẩm của mình, hay nghiên cứu một rootkit trong lab phòng thủ đều ổn. Dùng kiến thức này để vô hiệu hoá anti-cheat của game online hay viết rootkit thì không, cả về luật lẫn về nghề. Code ring-0 là nơi ranh giới giữa nghiên cứu và phá hoại mỏng nhất, nên giữ mình cẩn thận.

## Lab tự làm

Xem `labs/18.6/`: đọc một kernel module Linux đơn giản (có source kèm để đối chiếu), build thành `.ko`, rồi mở `.ko` trong Ghidra để tìm `module_init`, `file_operations` và hàm ioctl, so với source.

## Checklist ghi nhớ
- Reverse ring-0 luôn làm trong VM: target là VM, host chạy debugger, snapshot trước khi nạp driver.
- Windows `.sys` là PE, điểm vào `DriverEntry`, trái tim là `MajorFunction[IRP_MJ_DEVICE_CONTROL]` (slot 0xE) xử lý IOCTL.
- Lần ngược từ `DeviceIoControl` phía user-mode để hiểu IOCTL code và cấu trúc buffer.
- Linux `.ko` là ELF, điểm vào `module_init`, tìm `file_operations` và dấu hiệu hook `sys_call_table`.
- Debug: WinDbg kernel mode (Windows), kgdb hoặc QEMU gdbstub (Linux).
- Một lỗi ring-0 là sập máy, nên đọc tĩnh kỹ trước khi chạy động.
