---
title: "Bài 0.3: Dựng lab an toàn trước khi chạm vào thứ gì nguy hiểm"
date: 2026-10-06 08:02:00 +0700
categories: ["Technique Reverse", "Phần 0 · Nhập môn"]
tags: [reverse-engineering, nhap-mon]
render_with_liquid: false
---
Có một quy tắc trong nghề này mà bạn chỉ phá một lần: **đừng bao giờ chạy mẫu lạ trên máy thật của mình.** Người ta học nó bằng cách mất một buổi tối dọn dẹp máy sau khi "chỉ chạy thử xem nó làm gì". Ta học bằng cách đọc bài này.

Với crackme và CTF thì rủi ro gần như bằng không, chạy trên máy thường cũng được. Nhưng ngay khi đụng tới malware thật hoặc binary không rõ nguồn gốc, bạn cần một cái lab. Dựng một lần, dùng mãi.

## Vì sao phải có máy ảo riêng

Ba lý do, theo thứ tự quan trọng:

1. **Cô lập.** Malware chạy trong VM không đụng được tới máy thật nếu bạn cấu hình đúng.
2. **Snapshot.** Đây mới là thứ thay đổi cuộc chơi. Bạn chụp lại trạng thái "sạch" của VM, chạy mẫu, phân tích thoả thích, rồi bấm một nút quay về đúng trạng thái sạch ban đầu trong vài giây. Không cài lại Windows, không dọn dẹp gì cả.
3. **Môi trường ổn định.** Cài sẵn đủ tool một lần, sau này clone ra nhiều bản.

## Chọn hypervisor

Phần mềm tạo VM gọi là hypervisor. Ba lựa chọn phổ biến:

- **VMware Workstation** (Windows/Linux) hoặc **Fusion** (macOS). Ổn định, snapshot tốt, là lựa chọn của phần lớn dân malware. Bản cá nhân giờ miễn phí.
- **VirtualBox.** Hoàn toàn miễn phí, mã nguồn mở, đủ dùng để học. Snapshot có nhưng kém mượt hơn VMware một chút.
- **Hyper-V** sẵn trên Windows Pro, dùng được nhưng ít tool RE hỗ trợ sẵn hơn.

Người mới cứ VirtualBox hoặc VMware bản free mà chạy. Đừng phân vân chuyện này quá lâu.

## Cấu hình mạng, chỗ hay sai nhất

Mặc định VM nối thẳng ra internet qua NAT. Với malware, đó là lúc nó gọi về server điều khiển (C2) và có khi còn lây sang máy khác trong mạng nhà bạn. Có ba chế độ cần nhớ:

- **Host-only / Internal network.** VM chỉ nói chuyện với host hoặc với VM khác, không ra internet. Đây là chế độ mặc định khi phân tích malware.
- **NAT.** VM ra được internet. Chỉ bật khi bạn cố tình muốn quan sát lưu lượng mạng thật của mẫu, và chấp nhận rủi ro.
- **Giả lập internet.** Dùng một VM thứ hai chạy **INetSim** hoặc **FakeNet-NG** để đóng giả mọi dịch vụ mạng (DNS, HTTP, SMTP...). Malware tưởng mình đã ra được internet và tiết lộ hành vi, còn gói tin thì không đi đâu cả. Đây là thiết lập chuẩn cho lab nghiêm túc.

Mô hình hai máy ảo kinh điển: một VM Windows chạy mẫu (máy nạn nhân), một VM Linux làm cổng mạng giả và bắt gói. Cả hai nối với nhau qua host-only network, tách hẳn khỏi mạng nhà.

## Những thiết lập nhỏ nhưng quan trọng

- **Chụp snapshot "sạch" ngay sau khi cài xong tool**, trước khi chạy mẫu nào. Đặt tên rõ ràng kiểu `clean-base`.
- **Tắt shared folder và clipboard chung** khi phân tích malware thật. Đó là hai đường thoát hay bị bỏ quên. Bật lại khi chỉ làm crackme.
- **Tắt auto-mount USB.**
- Cân nhắc **không cài VM Guest Additions / VMware Tools** khi phân tích mẫu tinh vi, vì nhiều malware dò sự hiện diện của chúng để biết mình đang bị theo dõi (anti-VM, nói ở [Bài 15.5](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse)).
- Giữ **tool trên host hoặc trên một ổ chia sẻ chỉ-đọc**, đừng lẫn với thư mục chứa mẫu.

## Lắp sẵn tool: FLARE-VM và REMnux

Bạn không phải cài tay hàng trăm công cụ. Hai bộ dựng sẵn làm hết việc đó:

- **FLARE-VM** (của Mandiant). Chạy một script PowerShell trên VM Windows sạch, nó tự tải và cài cả rừng tool RE và malware analysis: x64dbg, IDA Free, Ghidra, PE-bear, dnSpy, Detour, và rất nhiều nữa. Cài xong nhớ snapshot ngay.
- **REMnux.** Một bản Linux dựng sẵn cho phân tích malware, đủ tool phân tích file, mạng, maldoc, memory. Thường đóng vai VM Linux trong mô hình hai máy.

Quy trình gọn cho người mới: cài Windows vào VM, chạy FLARE-VM, snapshot `clean-base`. Cài thêm một VM REMnux làm cổng mạng. Xong, bạn có một lab tử tế.

## Khi nào cần nghiêm túc tới mức nào

Đừng dựng lab quá phức tạp cho việc không cần. Thang đo nhanh:

| Bạn đang làm gì | Mức lab cần |
|---|---|
| Crackme, CTF, binary tự viết | Máy thật cũng được, hoặc VM thường |
| Phần mềm lạ không rõ nguồn | VM có snapshot, mạng host-only |
| Malware thật | VM cô lập + mạng giả lập + snapshot, host-only tuyệt đối |
| Mẫu APT tinh vi, có anti-VM | Lab chuyên dụng, cân nhắc máy vật lý riêng (bare-metal) |

## Checklist ghi nhớ
- Không chạy mẫu lạ trên máy thật. Chấm hết.
- Snapshot "sạch" trước khi chạy bất cứ thứ gì, quay về trong vài giây khi xong.
- Malware: mạng host-only hoặc giả lập (INetSim/FakeNet), tắt shared folder và clipboard.
- FLARE-VM (Windows) + REMnux (Linux) giúp bạn có lab đầy đủ mà không cài tay.
- Mức độ lab tương xứng với mức độ nguy hiểm của mẫu.
