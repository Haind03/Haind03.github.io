---
title: "Bài 18.5: Reverse firmware và thiết bị IoT"
date: 2026-10-06 09:51:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Cái router cũ trong góc nhà, con camera giá rẻ, ổ khoá thông minh, tất cả đều chạy một mẩu Linux nhúng nhét trong vài MB flash. Reverse firmware là mở cái hộp đen đó ra: lấy được filesystem, đọc code dịch vụ, tìm backdoor và credential cắm cứng, rồi nếu muốn thì chạy giả lập cả con firmware trên máy mình mà không cần phần cứng thật. Bài này đi từ lấy firmware tới chạy được một binary trong đó.

Đây là chặng ghép lại gần như mọi thứ đã học: binary thường là MIPS hoặc ARM (nối [Bài 1.9](/posts/tr-1-9-arm-arm64-co-ban/)), định dạng ELF ([Bài 1.8](/posts/tr-1-8-elf-va-mach-o/)), và bạn vẫn mở chúng bằng Ghidra như mọi khi.

## Lấy firmware vào tay đã

Không có firmware thì không có gì để reverse. Bốn đường quen thuộc, từ dễ tới khó:

- **Tải từ trang hãng.** Mục support/download của nhà sản xuất thường có file cập nhật firmware. Dễ nhất, và hợp pháp nhất khi là thiết bị của chính bạn.
- **Bắt gói lúc thiết bị tự update.** Thiết bị tải firmware qua HTTP, chặn bằng mitmproxy là có.
- **Dump qua UART hoặc JTAG/SWD.** Hàn vào chân serial trên board, vào được bootloader (U-Boot) hay shell, đọc flash ra. JTAG cho quyền debug phần cứng sâu hơn (OpenOCD).
- **Tháo chip flash ra đọc trực tiếp.** Dùng chip programmer (CH341A) hoặc kẹp SOIC8 với flashrom để đọc con SPI flash. Khi mọi cách mềm đều bị khoá thì đây là cách cuối.

Trong khuôn khổ bài này ta giả định đã có một file firmware image (`.bin`).

## binwalk: con dao đầu tiên

Firmware image là nhiều thứ xếp cạnh nhau: header của hãng, bootloader, kernel nén, và một filesystem. `binwalk` quét toàn file tìm chữ ký magic của từng thành phần.

```
$ binwalk firmware.bin

DECIMAL     HEXADECIMAL   DESCRIPTION
----------------------------------------------------------
0           0x0           uImage header, ... OS: Linux, CPU: MIPS
64          0x40          LZMA compressed data
1310720     0x140000      Squashfs filesystem, little endian, version 4.0
```

Đọc ra ngay: đây là firmware MIPS Linux, kernel nén LZMA ở đầu, và một SquashFS (filesystem chỉ đọc hay dùng cho nhúng) bắt đầu ở offset `0x140000`. Trích hết ra:

```
$ binwalk -e firmware.bin        # extract, ra thư mục _firmware.bin.extracted/
```

Thêm `-M` để đệ quy (extract trong extract). Một mẹo nhỏ nhưng quan trọng: nhìn **entropy**. `binwalk -E firmware.bin` vẽ đồ thị entropy, vùng phẳng sát 1.0 là dữ liệu nén hoặc mã hoá. Nếu cả file entropy cao đều thì firmware có thể bị mã hoá, phải tìm key giải (thường nằm trong bootloader hoặc một bản firmware cũ chưa mã hoá).

## unblob: khi binwalk bó tay

`binwalk` kinh điển nhưng đôi khi trích sai hoặc bỏ sót định dạng lạ. `unblob` là lựa chọn hiện đại hơn: nhận diện và trích đệ quy hàng trăm định dạng, xử lý nhiều trường hợp binwalk trượt.

```
$ unblob -e out/ firmware.bin
```

Thói quen thực tế: chạy cả hai. Cái nào ra filesystem sạch hơn thì dùng. Mục tiêu là lấy được **root filesystem** đầy đủ (có `/bin`, `/etc`, `/sbin`, `/www`...).

## Lục root filesystem

Có được rootfs rồi, đây là lúc tìm vàng. Vài chỗ luôn đáng xem:

- **`/etc/passwd`, `/etc/shadow`.** Credential cắm cứng, hash mật khẩu root yếu, tài khoản backdoor. `john` hoặc `hashcat` crack hash nếu cần.
- **`/etc/` nói chung.** Config dịch vụ, chuỗi kết nối, chứng chỉ, key riêng (`*.pem`, `*.key`).
- **`/www` hoặc web root.** Giao diện quản trị, script CGI, chỗ hay có command injection.
- **`/bin`, `/sbin`, `/usr/bin`.** Các binary dịch vụ (httpd, telnetd, binary độc quyền của hãng). Đây là thứ bạn đưa vào Ghidra.

Quét nhanh toàn rootfs tìm manh mối:

```
$ grep -riIn "password\|admin\|backdoor\|secret\|telnet" rootfs/etc rootfs/www
$ find rootfs -name "*.pem" -o -name "*.key"
$ file rootfs/bin/httpd      # xem kiến trúc: MIPS? ARM?
```

Lệnh `file` cho biết binary là MIPS hay ARM, 32 hay 64 bit, endian nào. Đó là thông tin bạn cần để nạp đúng vào Ghidra và để emulate.

## Phân tích binary nhúng bằng Ghidra

Binary dịch vụ của firmware thường là ELF cho MIPS hoặc ARM. Ghidra mở được tất cả: nó tự nhận kiến trúc, có decompiler cho MIPS/ARM. Quy trình giống hệt reverse một ELF x86, chỉ khác tập lệnh. Nếu binary strip hết symbol, bạn vẫn đi từ chuỗi và lời gọi hàm thư viện (`system`, `strcpy`, `popen`) như thường. Những hàm đó trong thiết bị IoT là nơi command injection hay nằm.

## Emulate để chạy và debug thật

Đọc tĩnh có giới hạn. Cho binary chạy sẽ nhanh hơn nhiều, nhưng bạn không có con router thật để cắm vào. QEMU giải quyết: nó emulate CPU MIPS/ARM ngay trên máy x86 của bạn.

**User-mode (chạy một binary lẻ).** Chép `qemu-arm-static` (hoặc `qemu-mips-static`) vào rootfs rồi chroot vào đó, binary tưởng mình đang chạy trên thiết bị thật:

```
$ sudo cp $(which qemu-mipsel-static) rootfs/usr/bin/
$ sudo chroot rootfs /usr/bin/qemu-mipsel-static /bin/httpd
```

Cần `binfmt_misc` và gói `qemu-user-static` cài sẵn. Cách này tốt để chạy một dịch vụ đơn, nhưng dễ vấp khi binary cần hạ tầng (nvram, các process khác).

**System-mode (boot cả firmware).** QEMU dựng nguyên một máy ảo MIPS/ARM và boot kernel + rootfs của firmware, gần với thiết bị thật nhất. Dựng tay khá cực, nên có framework tự động:

- **FirmAE** (và tiền thân **firmadyne**): tự trích, tự đoán cấu hình mạng, boot firmware trong QEMU và cho bạn truy cập giao diện web của thiết bị ảo. Tỉ lệ boot thành công khá cao, rất hợp để test lỗ hổng web của router mà không cần mua thiết bị.

Khi đã boot được, bạn gắn `gdbserver` vào để debug động binary MIPS/ARM y như debug trên Linux x86 (nối [Bài 2.6](/posts/tr-2-6-gdb-pwndbg-windbg/)).

## Một lời về pháp lý và an toàn

Hai điều đừng quên. Thứ nhất, reverse firmware của thiết bị **của chính bạn** để học thì ổn, nhưng phát tán firmware vá sẵn, bẻ khoá khoá vùng, hay tấn công thiết bị của người khác là chuyện khác hẳn, xem lại [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/). Thứ hai, firmware tải về từ nguồn lạ cũng là dữ liệu không tin được: trích và phân tích trong VM cô lập ([Bài 0.3](/posts/tr-0-3-dung-lab-an-toan/)), đừng chroot chạy binary lạ trên máy chính.

## Checklist ghi nhớ
- Lấy firmware: tải từ hãng, bắt update, dump UART/JTAG, hoặc đọc chip flash trực tiếp.
- `binwalk` quét và trích; xem entropy để biết có bị nén/mã hoá; `unblob` khi binwalk trượt.
- Mục tiêu là root filesystem: lục `/etc/passwd`, `/etc`, `/www`, và binary trong `/bin` `/sbin`.
- `file` cho biết kiến trúc (MIPS/ARM) để nạp đúng Ghidra và chọn đúng QEMU.
- Emulate: QEMU user-mode (chroot + qemu-*-static) chạy một binary, system-mode (FirmAE/firmadyne) boot cả firmware.
- Chỉ đụng thiết bị của mình, trích firmware trong VM cô lập.
