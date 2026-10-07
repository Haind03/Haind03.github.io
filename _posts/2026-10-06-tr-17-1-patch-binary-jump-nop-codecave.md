---
title: "Bài 17.1: Patch binary, đổi một byte để đổi số phận chương trình"
date: 2026-10-06 09:40:00 +0700
categories: ["Technique Reverse", "Phần 17 · Patch, Hook, Injection & Instrumentation"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
Reverse để hiểu là một chuyện, nhưng nhiều lúc bạn muốn chương trình **cư xử khác đi**: bỏ qua một check phiền phức, tắt một thông báo, cho một nhánh luôn chạy. Patch là việc sửa trực tiếp vài byte của binary để làm điều đó. Nghe to tát nhưng bản chất thường chỉ là đổi một byte `74` thành `90`. Bài này cho bạn thấy đúng điều đó, trên một binary thật.

Nhắc lại ranh giới ở [Bài 0.2](/posts/tr-0-2-phap-ly-dao-duc/): patch crackme của mình, binary CTF, hay phần mềm bạn có quyền thì thoải mái. Patch rồi phát tán bản crack của phần mềm thương mại thì phạm luật.

## Hai cặp kỹ thuật nền tảng

Gần như mọi patch bạn làm trong đời rơi vào một trong hai nhóm.

**Đổi lệnh nhảy có điều kiện.** Nhớ từ [Bài 1.3](/posts/tr-1-3-assembly-1-thanh-ghi-lenh-co-ban/): cặp `cmp`/`test` rồi `j*` chính là một câu `if`. Muốn đổi kết quả câu `if` đó, bạn sửa chính lệnh nhảy. Vài opcode nhảy ngắn (short jump, 1 byte toán hạng) hay gặp:

| Lệnh | Opcode | Ý nghĩa |
|---|---|---|
| `je` / `jz` | `74` | nhảy nếu bằng / ZF=1 |
| `jne` / `jnz` | `75` | nhảy nếu khác / ZF=0 |
| `jmp` short | `EB` | nhảy vô điều kiện |

Ba cách sửa một lệnh nhảy:
- Đổi `74` thành `75` (hoặc ngược lại): **đảo** điều kiện, nhánh nào đang chạy thì đổi sang nhánh kia.
- Đổi `74` thành `EB`: biến nhảy có điều kiện thành **luôn nhảy**.
- Ghi đè `74 xx` bằng `90 90`: **NOP**, xoá luôn lệnh nhảy, chương trình luôn rơi xuống nhánh ngay sau.

**NOP một lệnh.** `90` là opcode của `nop` (no operation), chẳng làm gì. Muốn vô hiệu một lệnh (một `call` kiểm tra license, một lệnh gán giá trị phiền phức) mà không làm lệch địa chỉ các lệnh khác, bạn ghi đè nó bằng đúng số byte `90`. Một `call` dài 5 byte thì thay bằng năm con `90`.

Quy tắc vàng khi NOP: **đếm cho đúng số byte**. Lệnh cũ dài bao nhiêu byte thì phải phủ bấy nhiêu con `90`, không thừa không thiếu. Thiếu một byte là phần đuôi lệnh cũ trở thành một lệnh rác, lệch toàn bộ phần sau, chương trình crash ngay.

## Làm thật: patch một crackme

Lấy crackme `patchme` trong [labs/17.1](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/17.1). Nó so mật khẩu với `s3cr3t`. Đây là `main` sau khi `objdump -d -M intel` (số liệu thật từ build gcc trên Linux):

```asm
4011f2:  e8 7f ff ff ff   call  401176 <check>   ; gọi hàm check, kết quả ở eax
4011f7:  85 c0            test  eax, eax         ; eax == 0 (sai) ?
4011f9:  74 16            je    401211           ; nếu sai, nhảy tới nhánh "Wrong"
4011fb:  48 8d 05 ...     lea   rax, [rip+0xe1e] ; nhánh "Correct! Access granted."
401205:  e8 56 fe ff ff   call  401060 <puts>
...
401211:  48 8d 05 ...     lea   rax, [rip+0xe21] ; nhánh "Wrong password."
```

Logic rõ ràng: `check` trả 0 khi sai, `test eax,eax` rồi `je` nhảy tới `401211` in "Wrong". Mật khẩu đúng thì eax khác 0, `je` không nhảy, rơi xuống `4011fb` in "Correct".

Muốn chương trình **luôn** báo Correct, ta cần `je` tại `4011f9` không bao giờ nhảy. Cách sạch nhất: NOP nó. Hai byte `74 16` thành `90 90`.

Tìm vị trí trên đĩa. Chuỗi byte đứng ngay trước nó là `85 c0` (test eax,eax), nên pattern cần tìm là `85 c0 74 16`. Trong file này nó nằm ở **file offset 0x11f7**, nghĩa là byte `74` ở **0x11f9**. Sửa hai byte đó thành `90 90`:

```
trước:  85 c0 74 16 ...
sau:    85 c0 90 90 ...
```

Kết quả chạy thật trên bản đã patch, nhập một mật khẩu **sai**:

```
$ ./patchme_patched baisai
Correct! Access granted.
```

Một chương trình từng từ chối mọi mật khẩu sai giờ chấp nhận tất. Toàn bộ thay đổi: hai byte.

## Patch trên đĩa vs patch runtime

Vừa rồi là **patch trên đĩa**: sửa file, thay đổi vĩnh viễn, lần sau chạy vẫn còn. Công cụ: hex editor (HxD, ImHex) nếu bạn biết offset, hoặc x64dbg (sửa trong cửa sổ CPU bằng phím Space rồi menu Patches > Patch file để ghi ra file mới).

**Patch runtime** là sửa byte trong bộ nhớ lúc đang debug, chỉ sống trong phiên đó. Dùng khi bạn muốn thử nhanh một thay đổi mà chưa muốn đụng file, hoặc khi code được giải mã/unpack lúc chạy nên trên đĩa không có để sửa. Trong x64dbg, chọn lệnh rồi Space để assemble lại tại chỗ.

Mối quan hệ offset: địa chỉ bạn thấy trong debugger là địa chỉ ảo (ví dụ `0x4011f9`), còn trên đĩa là file offset (`0x11f9` ở ví dụ trên). Với một PE/ELF nạp ở base mặc định không ASLR, chênh lệch là một hằng số theo section; x64dbg và IDA tự quy đổi giúp bạn, nhưng khi tự sửa bằng hex editor thì phải tính đúng file offset (nhắc lại cách quy đổi RVA sang file offset ở [Bài 1.7](/posts/tr-1-7-dinh-dang-pe/)).

## Code cave: khi không đủ chỗ tại chỗ

Patch kiểu trên chỉ đổi được vài byte sẵn có. Nếu bạn cần **chèn thêm code** (ví dụ một đoạn tính toán mới) mà chỗ đó không đủ không gian, dùng code cave: một vùng byte `00` trống có sẵn trong binary (hay nằm cuối một section do căn lề). Quy trình:

1. Tìm một cave đủ lớn (x64dbg có plugin tìm cave, hoặc tự dò vùng `00` dài trong section thực thi).
2. Viết đoạn code mới của bạn vào cave.
3. Tại chỗ cần can thiệp, đặt một `jmp` tới cave (thay cho lệnh gốc, nhớ chép lại lệnh gốc bị đè vào cave để chạy xong còn chạy nó).
4. Cuối cave, `jmp` quay về ngay sau chỗ đã chèn.

Cave biến giới hạn "chỉ sửa được tại chỗ" thành "chèn code tuỳ ý", đổi lại phải cẩn thận với địa chỉ nhảy.

## Những cú vấp kinh điển

- **Lệch kích thước lệnh.** Như đã nói, NOP thiếu/thừa byte là hỏng. Luôn xem lệnh cũ dài mấy byte trước khi ghi đè.
- **Integrity check.** Nhiều chương trình tự tính checksum code của mình (xem [Bài 15.8](/posts/tr-15-8-integrity-check-anti-tamper/)). Patch code xong chạy lại thì nó phát hiện và thoát. Cách xử lý: đừng sửa code bị kiểm, mà vô hiệu hoá chính hàm check.
- **Relocation và ASLR.** Nếu bạn chèn địa chỉ tuyệt đối trong code cave, hãy để ý binary có relocation không, nếu không địa chỉ sẽ sai khi base đổi.
- **Patch nhầm chỗ.** Cùng một byte `74` xuất hiện hàng nghìn lần trong file. Luôn định vị bằng ngữ cảnh (cặp byte đứng trước, ví dụ `85 c0 74`) chứ đừng sửa đại.

## Patch hay keygen?

Hai con đường để "qua" một check serial, chọn theo bản chất bài:

- **Patch** khi chương trình chỉ hỏi đúng/sai một lần: NOP cái check, hoặc đảo cái nhảy. Nhanh, không cần hiểu thuật toán. Nhược: phải phát tán bản đã sửa, và dễ vỡ nếu có integrity check.
- **Keygen** khi serial được sinh theo thuật toán từ username (xem [Bài 3.6](/posts/tr-3-6-lab-viet-keygen/)): bạn hiểu thuật toán rồi tự sinh serial hợp lệ, không đụng tới binary. Sạch hơn, nhưng đòi hiểu sâu logic.

Người mới hay patch, người giỏi chọn công cụ theo bài.

## Checklist ghi nhớ
- `74`=je, `75`=jne, `EB`=jmp, `90`=nop. Nhớ bốn con này là patch được phần lớn check đơn giản.
- Ba cách sửa nhảy: đảo (74<->75), luôn nhảy (->EB), xoá nhảy (->90 90).
- NOP phải phủ đúng số byte của lệnh cũ, không thừa không thiếu.
- Định vị chỗ patch bằng ngữ cảnh byte, đừng sửa theo giá trị đơn lẻ.
- Patch trên đĩa là vĩnh viễn, patch runtime chỉ sống trong phiên debug.
- Code cave để chèn thêm code khi không đủ chỗ tại chỗ.
- Gặp integrity check thì vô hiệu hàm check, đừng sửa code bị nó kiểm.
