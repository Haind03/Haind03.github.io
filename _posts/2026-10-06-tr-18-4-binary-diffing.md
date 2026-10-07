---
title: "Bài 18.4: Binary diffing, tìm lỗ hổng từ chính bản vá"
date: 2026-10-06 09:50:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Có một nghịch lý thú vị trong bảo mật: cách nhanh nhất để biết một phần mềm có lỗ hổng gì nhiều khi lại là đọc bản vá của nó. Nhà sản xuất tung ra một bản update, kèm dòng changelog chung chung kiểu "sửa vài vấn đề ổn định". Nhưng binary trước và sau bản vá khác nhau ở đâu thì nói thẳng ra chỗ bug nằm ở đó. So hai binary để tìm chỗ khác gọi là binary diffing, và khi hai binary là trước/sau một bản vá thì gọi riêng là patch diffing.

Bài này cho bạn thấy kỹ thuật đó bằng một ví dụ chạy thật: hai phiên bản của cùng một chương trình, một bản có lỗi, một bản đã vá, và cách diffing chỉ thẳng vào hàm bị sửa.

## Dùng để làm gì

Ba tình huống hay gặp:

- **Patch diffing cho vulnerability research.** So bản cũ và bản vá, tìm hàm được sửa, hiểu bug được fix. Từ đó dựng lại lỗ hổng để viết signature phát hiện, hoặc kiểm chứng rằng hệ thống của mình đã an toàn. Đây là công việc phòng thủ hợp pháp, cũng là cách người ta nghiên cứu 1-day (lỗ hổng vừa được vá nhưng nhiều máy chưa cập nhật).
- **So sánh biến thể malware.** Hai mẫu malware cùng họ chia sẻ phần lớn code, diff cho thấy kẻ tấn công đã thêm/sửa gì ở biến thể mới, giúp cập nhật rule.
- **Nhận lại hàm đã biết.** Bạn đã phân tích kỹ một binary, giờ gặp một binary khác dùng chung thư viện, diff giúp chuyển tên hàm và comment từ bản cũ sang bản mới, đỡ làm lại từ đầu.

## Công cụ

Diffing không so từng byte (byte đổi gần hết chỉ vì địa chỉ dịch đi), mà so cấu trúc hàm: control flow graph (CFG), số block, số lời gọi, hằng số. Mỗi cặp hàm được gán một similarity score từ 0 tới 1.

- **BinDiff** (Google, miễn phí). Chuẩn công nghiệp. Xuất hai binary đã phân tích từ IDA hoặc Ghidra (dạng BinExport) rồi so, hiện bảng matched/unmatched function kèm similarity. Hàm 1.00 là y hệt, hàm dưới 1.00 là chỗ đáng xem.
- **Diaphora** (mã nguồn mở, cho IDA). Rất mạnh, so cả pseudocode, nhập kết quả ngược lại IDA để port tên/comment.
- **ghidriff** (dựa Ghidra, dòng lệnh). Chạy headless, xuất báo cáo markdown, tiện cho tự động hoá và CI.
- **radiff2** (radare2). Diff nhanh từ dòng lệnh, `radiff2 -A -C v1 v2` so theo hàm.

Khái niệm cần nhớ: **matched function** (tìm được cặp tương ứng giữa hai bên), **unmatched** (chỉ có ở một bên, tức hàm bị thêm hoặc bị xoá), và **similarity** (hàm matched nhưng khác nhau là nơi có thay đổi thật). Trong patch diffing, bạn lao thẳng vào các hàm matched có similarity thấp hơn 1.00.

## Ví dụ chạy thật

Lab [18.4](https://github.com/Haind03/Technique-Reverse/tree/main/labs/18.4) có hai bản của một chương trình login nhỏ. Điểm khác duy nhất trong source nằm ở hàm `copy_name`: bản v1 chép tên người dùng bằng `strcpy` vào buffer 16 byte mà không kiểm độ dài (stack buffer overflow kinh điển), bản v2 thêm một kiểm tra độ dài trước khi chép.

Build cả hai bằng gcc `-O1` rồi `objdump -d`, đây là `copy_name` của **v1** (bản có lỗi):

```asm
<copy_name>:
    push   %rbx
    sub    $0x10,%rsp
    mov    %rdi,%rsi
    mov    %rsp,%rbx
    mov    $0x10,%edx
    mov    %rbx,%rdi
    call   __strcpy_chk       ; chep thang, khong kiem do dai
    ...
    call   __printf_chk
    ret
```

Và `copy_name` của **v2** (bản đã vá):

```asm
<copy_name>:
    push   %rbp
    push   %rbx
    sub    $0x18,%rsp
    mov    %rdi,%rbx
    call   strlen             ; MOI: do do dai truoc
    cmp    $0xf,%rax          ; MOI: so voi 15
    ja     <copy_name+0x4c>   ; MOI: dai qua thi nhay di bao loi
    mov    %rsp,%rbp
    mov    $0xf,%edx
    mov    %rbx,%rsi
    mov    %rbp,%rdi
    call   strncpy            ; doi tu strcpy sang strncpy gioi han 15
    movb   $0x0,0xf(%rsp)     ; MOI: tu tay dat NUL o cuoi
    ...
    call   __printf_chk
    ret
    ; nhanh bao loi "Ten qua dai"
    lea    ...,%rdi
    call   puts
    jmp    ...
```

Nhìn là ra ngay câu chuyện. Hàm vá có thêm một cụm `strlen` + `cmp $0xf` + `ja`, và `strcpy` biến thành `strncpy` có giới hạn. Cụm `cmp` mới chính là bound check mà bản cũ thiếu, nên lỗ hổng của v1 là buffer overflow khi tên dài hơn 15 ký tự. Bạn vừa tìm ra bug mà không cần ai nói, chỉ bằng cách so hai bản.

Hai hàm còn lại, `main` và `check_pin`, giữa v1 và v2 giống hệt nhau về cấu trúc (chỉ lệch địa chỉ). Một công cụ diffing sẽ chấm chúng similarity gần 1.00 và bỏ qua, còn `copy_name` sẽ nổi lên với similarity thấp. Đó đúng là nơi bạn cần đọc.

## Quy trình patch diffing

1. Lấy hai phiên bản: bản trước và bản sau khi vá (thường tải được từ nhà sản xuất, hoặc trích từ update package).
2. Phân tích từng bản trong IDA/Ghidra, xuất ra định dạng diff được (BinExport cho BinDiff, hoặc dùng Diaphora/ghidriff trực tiếp).
3. Chạy diff, sắp bảng theo similarity tăng dần.
4. Bỏ qua hàm 1.00, tập trung hàm matched có similarity thấp và hàm unmatched mới xuất hiện.
5. Đọc chỗ khác giữa hai hàm. Thêm một check, đổi một API nguy hiểm sang bản an toàn, sửa một so sánh kích thước, tất cả đều là dấu hiệu chỗ từng có bug.
6. Dựng lại kịch bản trigger bug ở bản cũ để hiểu và viết signature.

## Cạm bẫy

- Compiler đổi phiên bản hoặc cờ tối ưu giữa hai bản làm similarity giảm đồng loạt dù logic không đổi, dễ gây nhiễu. Cố so hai bản build cùng toolchain khi có thể.
- Hàm bị inline ở bản này mà không ở bản kia sẽ không match. Trong lab này tôi phải thêm `__attribute__((noinline))` để giữ `copy_name` là hàm riêng, nếu không compiler inline nó vào `main` và diff per-function không còn sạch.
- Một bản vá lớn đổi nhiều hàm cùng lúc, phải lọc ra hàm liên quan tới lỗ hổng chứ không phải mọi thay đổi vô hại.

## Checklist ghi nhớ
- Diffing so cấu trúc hàm (CFG), không so byte thô, nên địa chỉ dịch đi không làm sai kết quả.
- Trong patch diffing, hàm matched có similarity thấp và hàm unmatched mới là nơi đáng đọc.
- Một bound check mới, một API đổi từ strcpy sang strncpy, là dấu hiệu kinh điển của chỗ từng có bug.
- BinDiff và Diaphora cho GUI chi tiết, ghidriff và radiff2 cho dòng lệnh/tự động hoá.
- Cùng toolchain giữa hai bản để tránh nhiễu similarity.
