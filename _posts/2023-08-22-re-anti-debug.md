---
title: "Anti Debug"
date: 2023-08-22 08:35:00 +0700
categories: ["Technique Reverse", "Ghi chép 2023"]
tags: [reverse-engineering, anti-debug, malware]
render_with_liquid: false
---
-  Chống gỡ lỗi là một kỹ thuật chống phân tích phổ biến được sử dụng bởi phần mềm độc hại để nhận biết khi nào nó nằm trong tầm kiểm soát của trình gỡ lỗi hoặc để cản trở trình gỡ lỗi. tác giả phần mềm độc hại biết rằng các nhà phân tích phần mềm độc hại sử dụng trình gỡ lỗi để tìm ra cách phần mềm độc hại hoạt động và các tác giả sử dụng các kỹ thuật chống gỡ lỗi trong một program cố gắng làm chậm nhà phân tích càng nhiều càng tốt. 

- Khi phần mềm độc hại nhận ra rằng nó đang chạy trong trình gỡ lỗi, nó có thể thay đổi đường dẫn thực thi mã bình thường của nó hoặc sửa đổi mã để gây ra sự cố, do đó cản trở các nỗ lực của nhà phân tích để hiểu nó, và thêm thời gian và chi phí bổ sung cho những nỗ lực của họ. 

- Có nhiều kỹ thuật chống sửa lỗi có lẽ hàng trăm trong số đó và chúng ta sẽ chỉ thảo luận về những kỹ thuật phổ biến nhất mà chúng tôi đã gặp trong thế giới thực. 

- Chúng tôi sẽ trình bày các cách để vượt qua các kỹ thuật chống sửa lỗi, nhưng chúng tôi mục tiêu tổng thể trong chương này (ngoài việc giới thiệu cho bạn các kỹ thuật cụ thể) là giúp bạn phát triển các kỹ năng mà bạn sẽ cần để vượt qua các phương pháp chống gỡ lỗi mới và chưa từng được biết đến trước đây trong quá trình phân tích.



## Windows Debugger Detection

- Phần mềm độc hại sử dụng nhiều kỹ thuật khác nhau để quét các dấu hiệu cho thấy trình gỡ lỗi được đính kèm, bao gồm sử dụng API Windows, kiểm tra bộ nhớ theo cách thủ công cấu trúc để gỡ lỗi các tạo phẩm và tìm kiếm phần còn lại của hệ thống một trình gỡ lỗi. Phát hiện trình gỡ lỗi là cách phổ biến nhất mà phần mềm độc hại tạo ra để chống gỡ lỗi.

### Using the Windows API

- Việc sử dụng các chức năng API của Windows là cách chống gỡ lỗi rõ ràng nhất kỹ xảo. API Windows cung cấp một số chức năng có thể được sử dụng bởi một chương trình để xác định xem nó có đang được gỡ lỗi hay không. 

- Một số chức năng này được thiết kế để phát hiện trình gỡ lỗi; những cái khác được thiết kế cho những mục đích khác nhau mục đích nhưng có thể được sử dụng lại để phát hiện trình gỡ lỗi. Một số chức năng này sử dụng chức năng không được ghi lại trong API. 

- Thông thường, cách dễ nhất để vượt qua lệnh gọi tới API chống gỡ lỗi Chức năng là sửa đổi phần mềm độc hại theo cách thủ công trong quá trình thực thi để không gọi các chức năng này hoặc để sửa đổi lệnh gọi bài của cờ để đảm bảo rằng con đường được thực hiện. 

- Một lựa chọn khó khăn hơn là nối các hàm này, như với một rootkit. Các chức năng API Windows sau đây có thể được sử dụng để chống gỡ lỗi:



1. IsDebuggerPresent
   
   - Hàm API đơn giản nhất để phát hiện trình gỡ lỗi là IsDebuggerPresent. Hàm này tìm kiếm cấu trúc Khối môi trường quy trình (PEB) cho trường IsDebugged, sẽ trả về 0 nếu bạn không chạy trong ngữ cảnh của trình gỡ lỗi hoặc giá trị khác 0 nếu trình gỡ lỗi được đính kèm. Chúng ta sẽ thảo luận chi tiết hơn về cấu trúc PEB trong phần tiếp theo.



2. CheckRemoteDebuggerPresent
   
   - Hàm API này gần giống với IsDebuggerPresent. Tuy nhiên, cái tên này gây hiểu lầm vì nó không kiểm tra trình gỡ lỗi trên máy từ xa mà kiểm tra một quy trình trên máy cục bộ. Nó cũng kiểm tra cấu trúc PEB cho trường IsDebugged; tuy nhiên, nó có thể làm như vậy cho chính nó hoặc một tiến trình khác trên máy cục bộ. Hàm này lấy một trình xử lý quy trình làm tham số và sẽ kiểm tra xem quy trình đó có đính kèm trình gỡ lỗi hay không. 
   
   - CheckRemoteDebuggerPresent có thể được sử dụng để kiểm tra quy trình của riêng bạn bằng cách chuyển một điều khiển cho quy trình của bạn.



3. NtQueryInformationProcess
   
   - Đây là hàm API gốc trong Ntdll.dll để truy xuất thông tin về một quy trình nhất định. Tham số đầu tiên cho hàm này là một xử lý quy trình; cái thứ hai được sử dụng để cho hàm biết loại thông tin quy trình cần truy xuất. 
   
   - Ví dụ: việc sử dụng giá trị ProcessDebugPort (giá trị 0x7) cho tham số này sẽ cho bạn biết liệu quy trình được đề cập hiện có đang được gỡ lỗi hay không. Nếu quá trình không được gỡ lỗi, số 0 sẽ được trả về; nếu không, số cổng sẽ được trả về.
     
     

4. OutputDebugString
   
   - Chức năng này được sử dụng để gửi một chuỗi đến trình gỡ lỗi để hiển thị. Nó có thể được sử dụng để phát hiện sự hiện diện của trình gỡ lỗi. Ví dụ, Liệt kê 16-1 sử dụng SetLastError để đặt mã lỗi hiện tại thành một giá trị tùy ý. 
   
   - Nếu OutputDebugString được gọi và không có trình gỡ lỗi nào được đính kèm, GetLastError sẽ không còn chứa giá trị tùy ý của chúng ta nữa vì mã lỗi sẽ được đặt bởi hàm OutputDebugString nếu nó không thành công. 
   
   - Nếu OutputDebugString được gọi và có trình gỡ lỗi được đính kèm, lệnh gọi tới OutputDebugString sẽ thành công và giá trị trong GetLastError sẽ không bị thay đổi.

## Manually Checking Structures

- Sử dụng Windows API có thể là phương pháp rõ ràng nhất để phát hiện có trình gỡ lỗi, nhưng việc kiểm tra cấu trúc theo cách thủ công là phương pháp phổ biến nhất được các tác giả phần mềm độc hại sử dụng. Có nhiều lý do khiến phần mềm độc hại các tác giả không được khuyến khích sử dụng API Windows để chống gỡ lỗi.

- Ví dụ: các lệnh gọi API có thể bị rootkit nối vào để trả về thông tin sai lệch. Vì vậy, tác giả phần mềm độc hại thường chọn thực hiện chức năng tương đương với lệnh gọi API theo cách thủ công, thay vì dựa vào API Windows. 

- Khi thực hiện kiểm tra thủ công, một số cờ trong cấu trúc PEB cung cấp thông tin về sự hiện diện của trình gỡ lỗi. Ở đây, chúng ta sẽ xem xét một số trong số các cờ thường được sử dụng để kiểm tra trình gỡ lỗi

### Checking the BeingDebugged Flag

- Cấu trúc Windows PEB được HĐH duy trì cho mỗi quy trình đang chạy, như thể hiện trong ví dụ trong Liệt kê 16-2. Nó chứa tất cả các tham số chế độ người dùng liên kết với một quá trình. Các tham số này bao gồm dữ liệu môi trường của quy trình, bản thân dữ liệu này bao gồm các biến môi trường, các mô-đun được tải danh sách, địa chỉ trong bộ nhớ và trạng thái trình gỡ lỗi.

                                - Trong khi một tiến trình đang chạy, vị trí của PEB có thể được tham chiếu bởi vị trí fs:[30h]. Để chống gỡ lỗi, phần mềm độc hại sẽ sử dụng vị trí đó để kiểm tra cờ BeingDebugged, cờ này cho biết liệu quy trình được chỉ định có đang được gỡ lỗi. Bảng 16-1 cho thấy hai ví dụ về loại kiểm tra này.
  
  - Trong đoạn mã bên trái trong Bảng 16-1, vị trí của PEB được di chuyển vào EAX. Tiếp theo, phần bù cộng 2 này được chuyển vào EBX, tương ứng với phần bù vào PEB của vị trí cờ BeingDebugged. Cuối cùng là EBX được kiểm tra xem nó có bằng không hay không. Nếu vậy, trình gỡ lỗi không được đính kèm và bước nhảy sẽ bị lấy đi. Một ví dụ khác được trình bày ở phía bên phải của Bảng 16-1. Địa điểm của PEB được chuyển vào EDX bằng cách sử dụng kết hợp các lệnh đẩy/bật và sau đó cờ BeingDebugged ở độ lệch 2 được so sánh trực tiếp với 1. Kiểm tra này có thể có nhiều dạng và cuối cùng là bước nhảy có điều kiện xác định đường dẫn mã. Bạn có thể thực hiện một trong các cách tiếp cận sau để khắc phục vấn đề này:  
  
  - Buộc thực hiện bước nhảy (hoặc không) bằng cách sửa đổi cờ 0 theo cách thủ công ngay trước khi lệnh nhảy được thực thi. Đây là cách dễ nhất tiếp cận.  
  
  - Thay đổi cờ BeingDebugged thành 0 theo cách thủ công. 

- Cả hai lựa chọn nói chung đều có hiệu quả đối với tất cả các kỹ thuật mô tả trong phần này.

- NOTE:  Một số plugin OllyDbg thay đổi cờ BeingDebugged cho bạn. Phổ biến nhất là Hide Debugger, Hidedebug và PhantOm. Tất cả đều hữu ích để vượt qua Kiểm tra cờ BeingDebugged và cũng trợ giúp nhiều kỹ thuật khác mà chúng tôi thảo luận trong chương này.



### Checking the ProcessHeap Flag

- Một vị trí không có giấy tờ trong mảng Reserved4 (hiển thị trong Liệt kê 16-2), được gọi là ProcessHeap, được đặt thành vị trí phân bổ heap đầu tiên của quy trình bởi máy xúc. ProcessHeap nằm ở 0x18 trong cấu trúc PEB. cái này đầu tiên heap chứa một tiêu đề với các trường được sử dụng để báo cho kernel biết liệu heap đã được tạo trong trình gỡ lỗi. Chúng được gọi là các trường ForceFlags và Flags. 

- Độ lệch 0x10 trong tiêu đề heap là trường ForceFlags trên Windows XP, nhưng đối với Windows 7, nó ở mức bù 0x44 cho các ứng dụng 32 bit. Phần mềm độc hại có thể cũng xem offset 0x0C trên Windows XP hoặc offset 0x40 trên Windows 7 để biết Trường cờ.

-  Trường này hầu như luôn bằng với trường ForceFlags, nhưng thường được OR với giá trị 2. Liệt kê 16-3 hiển thị mã hợp ngữ cho kỹ thuật này. (Lưu ý rằng hai phải xảy ra các quy định riêng biệt.)

- Cách tốt nhất để khắc phục kỹ thuật này là thay đổi cờ ProcessHeap theo cách thủ công hoặc sử dụng trình cắm ẩn gỡ lỗi cho trình gỡ lỗi của bạn. Nếu bạn là bằng cách sử dụng WinDbg, bạn có thể khởi động chương trình với vùng nhớ lỗi bị vô hiệu hóa.  Ví dụ: lệnh Windbg –hd notepad.exe sẽ khởi động heap ở chế độ bình thường chế độ trái ngược với chế độ gỡ lỗi và các cờ mà chúng ta đã thảo luận sẽ không được đặt



### Checking NTGlobalFlag

- Vì các tiến trình chạy hơi khác một chút khi bắt đầu với trình gỡ lỗi nên chúng tạo ra các vùng nhớ khác nhau. Thông tin mà hệ thống sử dụng để xác định cách tạo cấu trúc heap được lưu trữ tại một vị trí không có giấy tờ trong PEB ở offset 0x68. 

- Nếu giá trị tại vị trí này là 0x70, chúng tôi biết rằng chúng tôi đang chạy trong trình gỡ lỗi. Giá trị 0x70 là sự kết hợp của các cờ sau khi có một đống được tạo bởi trình gỡ lỗi. Những cờ này được đặt cho quá trình nếu nó được bắt đầu từ trong một trình gỡ lỗi.



- Cách dễ nhất để khắc phục kỹ thuật này là thay đổi cờ theo cách thủ công hoặc bằng trình cắm ẩn gỡ lỗi cho trình gỡ lỗi của bạn. Nếu bạn đang sử dụng WinDbg, bạn có thể khởi động chương trình với tùy chọn đống lỗi bị vô hiệu hóa, như đã đề cập ở phần trước.



### Checking for System Residue

- Khi phân tích phần mềm độc hại, chúng tôi thường sử dụng các công cụ gỡ lỗi để lại phần còn lại trên hệ thống. Phần mềm độc hại có thể tìm kiếm dư lượng này để xác định khi bạn đang cố gắng phân tích nó, chẳng hạn như bằng cách tìm kiếm các khóa đăng ký để tìm tham chiếu đến trình gỡ lỗi. Sau đây là vị trí chung cho trình gỡ lỗi:
  
  - Khóa đăng ký này chỉ định trình gỡ lỗi kích hoạt khi một ứng dụng lỗi xảy ra. Theo mặc định, giá trị này được đặt thành Dr. Watson, vì vậy nếu nó được thay đổi thành thứ gì đó như OllyDbg, phần mềm độc hại có thể xác định rằng nó đang được soi dưới kính hiển vi. 

- Phần mềm độc hại cũng có thể tìm kiếm hệ thống để tìm tệp và thư mục, chẳng hạn như các chương trình thực thi chương trình gỡ lỗi phổ biến thường xuất hiện trong quá trình phân tích phần mềm độc hại. (Nhiều cửa hậu đã có sẵn mã để đi qua các hệ thống tệp.) 

- Hoặc phần mềm độc hại có thể phát hiện phần còn lại trong bộ nhớ trực tiếp, bằng cách xem danh sách quy trình hiện tại hoặc thông thường hơn bằng cách thực hiện một FindWindow để tìm kiếm trình sửa lỗi, như trong Liệt kê 16-5.

## Identifying Debugger Behavior

- Hãy nhớ lại rằng trình gỡ lỗi có thể được sử dụng để đặt điểm ngắt hoặc thực hiện từng bước một một quy trình nhằm hỗ trợ nhà phân tích phần mềm độc hại trong kỹ thuật đảo ngược. 

- Tuy nhiên, khi các thao tác này được thực hiện trong trình gỡ lỗi, chúng sẽ sửa đổi mã trong quá trình này. Một số kỹ thuật chống gỡ lỗi được phần mềm độc hại sử dụng để phát hiện loại hành vi gỡ lỗi này: quét INT, kiểm tra tổng kiểm tra, và kiểm tra thời gian.

### INT Scanning

- INT 3 là ngắt phần mềm được sử dụng bởi trình gỡ lỗi để tạm thời thay thế một hướng dẫn trong một chương trình đang chạy và để gọi trình xử lý ngoại lệ gỡ lỗi một cơ chế cơ bản để đặt điểm dừng. Opcode cho INT 3 là 0xCC. Khi bạn sử dụng trình gỡ lỗi để đặt điểm dừng, nó sẽ sửa đổi mã bằng cách chèn một 0xCC.

- Ngoài lệnh INT 3 cụ thể, lệnh INT ngay lập tức có thể đặt bất kỳ ngắt, gồm 3 (ngay lập tức có thể là một thanh ghi, chẳng hạn như EAX). Lệnh ngay lập tức INT sử dụng hai mã lệnh: giá trị 0xCD. Opcode 2 byte này ít hơn thường được sử dụng bởi các trình gỡ lỗi. 

- Một kỹ thuật chống sửa lỗi phổ biến có quy trình quét mã riêng của nó để sửa đổi INT 3 bằng cách tìm kiếm mã cho opcode 0xCC, như được hiển thị trong Liệt kê 16-6.



- Mã này bắt đầu bằng một lệnh gọi, theo sau là một cửa sổ bật lên đưa EIP vào EDI. EDI sau đó được điều chỉnh ở đầu mã. Mã sau đó được quét để tìm 0xCC byte. Nếu tìm thấy byte 0xCC, nó sẽ biết rằng có trình gỡ lỗi. Cái này kỹ thuật này có thể được khắc phục bằng cách sử dụng các điểm ngắt phần cứng thay vì các điểm ngắt phần mềm.



### Performing Code Checksums

- Phần mềm độc hại có thể tính toán tổng kiểm tra trên một phần mã của nó để hoàn thành cùng mục tiêu với việc quét các ngắt. Thay vì quét 0xCC, việc kiểm tra này chỉ cần thực hiện kiểm tra dự phòng theo chu kỳ (CRC) hoặc tổng kiểm tra MD5 của opcode trong phần mềm độc hại. 

- Kỹ thuật này ít phổ biến hơn so với quét, nhưng nó cũng hiệu quả không kém. Tìm phần mềm độc hại đang lặp lại các hướng dẫn nội bộ của nó, sau đó là so sánh với giá trị kỳ vọng. 

- Kỹ thuật này có thể được khắc phục bằng cách sử dụng các điểm ngắt phần cứng hoặc bằng sửa đổi thủ công đường dẫn thực thi với trình gỡ lỗi khi chạy.



### Timing Checks

- Kiểm tra thời gian là một trong những cách phổ biến nhất để phát hiện phần mềm độc hại trình gỡ lỗi vì các quy trình chạy chậm hơn khi được gỡ lỗi. Vì ví dụ, một bước thông qua một chương trình làm chậm đáng kể việc thực thi tốc độ.

- Có một số cách sử dụng tính năng kiểm tra thời gian để phát hiện trình gỡ lỗi:  
  
  - Ghi lại dấu thời gian, thực hiện một số thao tác, lấy dấu thời gian khác và sau đó so sánh hai dấu thời gian. Nếu có độ trễ, bạn có thể giả sử sự hiện diện của một trình gỡ lỗi.  
  
  - Lấy dấu thời gian trước và sau khi đưa ra ngoại lệ. Nếu một quá trình không được gỡ lỗi, ngoại lệ sẽ được xử lý rất nhanh chóng; một trình gỡ lỗi sẽ xử lý ngoại lệ chậm hơn nhiều. Theo mặc định, hầu hết các trình gỡ lỗi cần có sự can thiệp của con người để xử lý các trường hợp ngoại lệ, gây ra độ trễ rất lớn. Trong khi nhiều trình gỡ lỗi cho phép bạn bỏ qua các ngoại lệ và chuyển chúng vào chương trình, vẫn sẽ có độ trễ khá lớn trong quá trình đó. các trường hợp



### Using the rdtsc Instruction

- Phương pháp kiểm tra thời gian phổ biến nhất sử dụng lệnh rdtsc (opcode 0x0F31), trả về số lượng tích tắc kể từ hệ thống cuối cùng khởi động lại dưới dạng giá trị 64 bit được đặt vào EDX:EAX. Phần mềm độc hại sẽ thực thi đơn giản hướng dẫn này hai lần và so sánh sự khác biệt giữa hai bài đọc. Liệt kê 16-7 hiển thị một mẫu phần mềm độc hại thực sự sử dụng kỹ thuật rdtsc.



- Phần mềm độc hại sẽ kiểm tra xem liệu sự khác biệt giữa hai lệnh gọi đến rdtsc có lớn hơn 0xFFF tại `1` hay không và nếu quá nhiều thời gian đã trôi qua, lệnh điều kiện bước nhảy sẽ không được thực hiện. Nếu bước nhảy không được thực hiện, rdtsc được gọi lại và kết quả được đẩy lên ngăn xếp tại `2`, điều này sẽ khiến kết quả trả về chiếm thực hiện đến một vị trí ngẫu nhiên.



### Using QueryPerformanceCounter and GetTickCount

- Hai chức năng Windows API được sử dụng như rdtsc để thực hiện kiểm tra thời gian chống gỡ lỗi. Phương pháp này dựa trên thực tế là bộ vi xử lý có bộ đếm hiệu suất có độ phân giải cao các thanh ghi lưu trữ số lượng các hoạt động được thực hiện trong bộ xử lý. QueryPerformanceCounter có thể được gọi để truy vấn bộ đếm này hai lần để có chênh lệch thời gian sử dụng trong so sánh. Nếu quá nhiều thời gian đã trôi qua giữa hai cuộc gọi, giả định là một trình gỡ lỗi đang được sử dụng. 

- Chống gỡ lỗi Hàm GetTickCount trả về số mili giây có đã trôi qua kể từ lần khởi động lại hệ thống cuối cùng. (Do kích thước được phân bổ cho bộ đếm này, nó sẽ hoàn thành sau 49,7 ngày.) Một ví dụ về GetTickCount trong thực tế là được hiển thị trong Liệt kê 16-8.
  
  - Tất cả các cuộc tấn công tính thời gian mà chúng ta đã thảo luận có thể được tìm thấy trong quá trình gỡ lỗi hoặc phân tích tĩnh bằng cách xác định hai lệnh gọi liên tiếp tới các chức năng này theo sau bằng một phép so sánh.

-  Những kiểm tra này sẽ chỉ bắt được trình gỡ lỗi nếu bạn thực hiện một bước hoặc đặt điểm dừng giữa hai lệnh gọi được sử dụng để nắm bắt đồng bằng thời gian. Vì vậy, cách dễ nhất để tránh bị phát hiện theo thời gian là chạy thông qua các bước kiểm tra này và đặt điểm dừng ngay sau chúng, sau đó bắt đầu bước đơn của bạn một lần nữa. Nếu đó không phải là một lựa chọn, chỉ cần sửa đổi kết quả của sự so sánh để buộc bước nhảy mà bạn muốn thực hiện.



## Interfering with Debugger Functionality

- Malware có thể sử dụng một số kỹ thuật để can thiệp vào hoạt động của trình gỡ lỗi thông thường: lệnh gọi lại lưu trữ cục bộ (TLS) luồng, ngoại lệ và chèn ngắt. Những kỹ thuật này cố gắng làm gián đoạn quá trình thực thi của chương trình chỉ khi nó dưới sự kiểm soát của một trình gỡ lỗi.



### Using TLS Callbacks

- Bạn có thể nghĩ rằng khi bạn tải một chương trình vào trình gỡ lỗi, nó sẽ tạm dừng ở lệnh đầu tiên mà chương trình thực thi, nhưng điều này không phải lúc nào cũng đúng trường hợp. Hầu hết các trình gỡ lỗi đều bắt đầu tại điểm vào của chương trình như được xác định bởi PE tiêu đề. Một cuộc gọi lại TLS có thể được sử dụng để thực thi mã trước điểm vào và do đó thực thi bí mật trong trình gỡ lỗi. Nếu bạn chỉ dựa vào việc sử dụng một trình gỡ lỗi, bạn có thể bỏ lỡ chức năng nhất định của phần mềm độc hại, vì lệnh gọi lại TLS có thể chạy ngay khi được tải vào trình gỡ lỗi. 

- TLS là lớp lưu trữ Windows trong đó đối tượng dữ liệu không phải là đối tượng tự động biến ngăn xếp, nhưng là biến cục bộ của từng luồng chạy mã. Về cơ bản, TLS cho phép mỗi luồng duy trì một giá trị khác nhau cho một biến được khai báo bằng TLS. Khi TLS được triển khai bởi một tệp thực thi, mã thường sẽ chứa phần .tls trong tiêu đề PE, như trong Hình 16-1. Hỗ trợ TLS các hàm gọi lại để khởi tạo và kết thúc các đối tượng dữ liệu TLS. Windows thực thi các chức năng này trước khi chạy mã khi khởi động bình thường của một chương trình.
  
  - Có thể phát hiện các cuộc gọi lại TLS bằng cách xem phần .tls bằng PEview. Bạn nên nghi ngờ ngay lập tức chống gỡ lỗi nếu bạn thấy phần .tls, như các chương trình bình thường thường không sử dụng phần này. 

- Việc phân tích lệnh gọi lại TLS thật dễ dàng với IDA Pro. Khi IDA Pro đã hoàn tất phân tích của nó, bạn có thể xem các điểm vào cho nhị phân bằng cách nhấn CTRL-E để hiển thị tất cả các điểm vào chương trình, bao gồm các cuộc gọi lại TLS, như được hiển thị trong Hình 16-2. Tất cả các hàm gọi lại TLS đều có nhãn được thêm vào trước Tlscallback. Bạn có thể duyệt đến chức năng gọi lại trong IDA Pro bằng cách nhấp đúp vào tên chức năng.
  
  - Lệnh gọi lại TLS có thể được xử lý trong trình gỡ lỗi, mặc dù đôi khi trình gỡ lỗi sẽ chạy lệnh gọi lại TLS trước khi ngắt ở mục nhập ban đầu điểm. Để tránh sự cố này, hãy thay đổi cài đặt của trình gỡ lỗi. Ví dụ, nếu bạn đang sử dụng OllyDbg, bạn có thể tạm dừng nó trước khi gọi lại TLS bằng cách chọn Options=> Debugging => Options =>Events và cài đặt System break-point làm nơi tạm dừng đầu tiên, như trong Hình 16-3. 

- NOTE: OllyDbg 2.0 có nhiều khả năng phá vỡ hơn phiên bản 1.1; ví dụ, nó có thể tạm dừng khi bắt đầu cuộc gọi lại TLS. Ngoài ra, WinDbg luôn bị hỏng ở điểm dừng hệ thống trước lệnh gọi lại TLS.



- Vì lệnh gọi lại TLS được biết đến rộng rãi nên phần mềm độc hại ít sử dụng chúng hơn trong quá khứ. Không có nhiều ứng dụng hợp pháp sử dụng lệnh gọi lại TLS, vì vậyPhần .tls trong tệp thực thi có thể nổi bật. 



### Using Exceptions

- Sử dụng ngoại lệ Như đã thảo luận trước đó, các ngắt tạo ra các ngoại lệ được trình gỡ lỗi sử dụng để thực hiện các hoạt động như điểm dừng. Trong Chương 15, bạn đã học cách thiết lập SEH để đạt được bước nhảy độc đáo. Việc sửa đổi của Chuỗi SEH áp dụng cho cả chức năng chống tháo gỡ và chống gỡ lỗi. Trong phần này, chúng ta sẽ bỏ qua các chi tiết cụ thể về SEH (vì chúng đã được đề cập ở Chương 15) và tập trung vào những cách khác mà các ngoại lệ có thể được sử dụng để cản trở phần mềm độc hại nhà phân tích. 
- Exceptions có thể được sử dụng để làm gián đoạn hoặc phát hiện trình gỡ lỗi. Hầu hết việc phát hiện dựa trên ngoại lệ đều dựa vào thực tế là trình gỡ lỗi sẽ bẫy ngoại lệ và không ngay lập tức chuyển nó tới quá trình đang được gỡ lỗi để xử lý. Các cài đặt mặc định trên hầu hết các trình gỡ lỗi là bẫy các ngoại lệ và không vượt qua chúng đến chương trình. Nếu trình gỡ lỗi không chuyển ngoại lệ cho quy trình đúng cách, lỗi đó có thể được phát hiện trong quá trình xử lý ngoại lệ cơ chế.



### 

## Inserting Interrupts

- Một hình thức chống gỡ lỗi cổ điển là sử dụng các ngoại lệ để làm phiền nhà phân tích và làm gián đoạn việc thực thi chương trình thông thường bằng cách chèn các ngắt vào giữa chương trình trình tự lệnh hợp lệ. Tùy thuộc vào cài đặt trình gỡ lỗi, các phần chèn này có thể khiến trình gỡ lỗi dừng lại vì nó có cùng cơ chế chính trình gỡ lỗi sử dụng để đặt điểm dừng phần mềm.



### Inserting INT 3

- Vì INT 3 được trình gỡ lỗi sử dụng để đặt điểm ngắt phần mềm, nên một kỹ thuật chống gỡ lỗi bao gồm chèn mã lệnh 0xCC vào các phần hợp lệ của mã để đánh lừa trình gỡ lỗi nghĩ rằng các opcode là của nó điểm dừng. Một số trình sửa lỗi theo dõi nơi họ đặt điểm dừng phần mềm trong để tránh rơi vào mánh khóe này. 

- Chuỗi opcode 2 byte 0xCD03 cũng có thể được sử dụng để tạo INT 3, và đây thường là cách hợp lệ để phần mềm độc hại can thiệp vào WinDbg. Bên ngoài một trình gỡ lỗi, 0xCD03 tạo ngoại lệ STATUS_BREAKPOINT. 

- Tuy nhiên, bên trong WinDbg, nó bắt điểm dừng và sau đó âm thầm tăng EIP chính xác 1 byte, vì điểm ngắt thường là mã lệnh 0xCC. Điều này có thể gây ra chương trình để thực hiện một tập lệnh khác khi được gỡ lỗi bởi WinDbg so với chạy bình thường. (OllyDbg không dễ bị can thiệp bằng cách sử dụng cuộc tấn công INT 3 2 byte này.) 

-  Liệt kê 16-9 hiển thị mã hợp ngữ thực hiện kỹ thuật này. Cái này ví dụ đặt SEH mới và sau đó gọi INT 3 để buộc mã tiếp tục.

### Inserting INT 2D

- Kỹ thuật chống gỡ lỗi INT 2D hoạt động giống như INT 3—lệnh INT 0x2D được sử dụng để truy cập trình gỡ lỗi kernel. Bởi vì INT 0x2D là cách mà các trình gỡ lỗi hạt nhân thiết lập các điểm dừng nên phương pháp hiển thị trong Liệt kê 16-10 sẽ được áp dụng. 

### Inserting ICE

- Một trong những hướng dẫn không có giấy tờ của Intel là Trình mô phỏng trong mạch (ICE) điểm dừng, icebp (opcode 0xF1). Hướng dẫn này được thiết kế để giúp việc gỡ lỗi bằng ICE dễ dàng hơn vì rất khó đặt điểm dừng tùy ý với một ICE. 

- Việc thực hiện lệnh này sẽ tạo ra một ngoại lệ một bước. Nếu chương trình đang được theo dõi thông qua một bước, trình gỡ lỗi sẽ nghĩ rằng đó là ngoại lệ bình thường được tạo bởi một bước và không thực thi một thiết lập trước đó trình xử lý ngoại lệ. 

- Phần mềm độc hại có thể lợi dụng điều này bằng cách sử dụng ngoại lệ xử lý luồng thực thi thông thường của nó, điều này sẽ bị gián đoạn trong trường hợp này. Để bỏ qua kỹ thuật này, không được thực hiện một bước nào qua hướng dẫn Icebp.



## Debugger Vulnerabilities

- Giống như tất cả các phần mềm, trình gỡ lỗi chứa lỗ hổng và đôi khi phần mềm độc hại tác giả tấn công chúng để ngăn chặn việc gỡ lỗi. Ở đây, chúng tôi trình bày một số các lỗ hổng phổ biến trong cách OllyDbg xử lý định dạng PE.

## PE Header Vulnerabilities

- Kỹ thuật đầu tiên sửa đổi tiêu đề Microsoft PE của tệp thực thi nhị phân, khiến OllyDbg gặp sự cố khi tải tệp thực thi. Kết quả là một lỗi của “Tệp thực thi 32-bit xấu hoặc không xác định”, nhưng chương trình vẫn thường chạy tốt bên ngoài trình gỡ lỗi. Vấn đề này là do OllyDbg tuân thủ quá nghiêm ngặt các thông số kỹ thuật của Microsoft về tiêu đề PE. Trong tiêu đề PE, thường có một cấu trúc được gọi là IMAGE_OPTIONAL_HEADER. Hình 16-5 cho thấy một tập hợp con của cấu trúc này.

- Một số yếu tố cuối cùng trong cấu trúc này được đặc biệt quan tâm. Các Trường NumberOfRvaAndSizes xác định số lượng mục nhập trong mảng DataDirectory theo sau. Mảng DataDirectory cho biết nơi tìm các dữ liệu khác các thành phần thực thi quan trọng trong tệp; nó không chỉ là một mảng Cấu trúc IMAGE_DATA_DIRECTORY ở cuối cấu trúc tiêu đề tùy chọn. Mỗi cấu trúc thư mục dữ liệu chỉ định kích thước và địa chỉ ảo tương đối của các thư mục. 

- Kích thước của mảng được đặt thành IMAGE_NUMBEROF_DIRECTORY_ENTRIES, nghĩa là bằng 0x10. Trình tải Windows bỏ qua mọi NumberOfRvaAndSizes lớn hơn 0x10, vì mọi thứ lớn hơn sẽ không vừa với mảng DataDirectory. OllyDbg tuân theo tiêu chuẩn và sử dụng NumberOfRvaAndSizes bất kể điều gì. 

- Do đó, việc đặt kích thước của mảng thành giá trị lớn hơn 0x10 (như 0x99) sẽ khiến OllyDbg tạo một cửa sổ bật lên cho người dùng trước khi thoát khỏi chương trình. Cách dễ nhất để khắc phục kỹ thuật này là sửa đổi thủ công Tiêu đề PE và đặt NumberOfRvaAndSizes thành 0x10 bằng trình chỉnh sửa hex hoặc PE Nhà thám hiểm. 

- Hoặc, tất nhiên, bạn có thể sử dụng một trình gỡ lỗi không dễ bị tấn công. kỹ thuật này, chẳng hạn như WinDbg hoặc OllyDbg 2.0. Một thủ thuật tiêu đề PE khác liên quan đến tiêu đề phần, khiến OllyDbg gặp sự cố trong khi tải với lỗi “Tệp chứa quá nhiều dữ liệu”. (WinDbg và OllyDbg 2.0 không dễ bị tổn thương bởi kỹ thuật này.) Các phần chứa nội dung của tệp, bao gồm mã, dữ liệu, tài nguyên và thông tin khác. Mỗi phần có tiêu đề ở dạng cấu trúc IMAGE_SECTION_HEADER.

- Hình 16-6 cho thấy một tập hợp con của cấu trúc này.

- Các yếu tố quan tâm là VirtualSize và SizeOfRawData. Theo đặc tả Windows PE, VirtualSize phải chứa tổng kích thước của phần khi được tải vào bộ nhớ và SizeOfRawData sẽ chứa kích thước của dữ liệu trên đĩa. Trình tải Windows sử dụng VirtualSize nhỏ hơn và SizeOfRawData để ánh xạ dữ liệu phần vào bộ nhớ. Nếu SizeOfRawData là lớn hơn VirtualSize, chỉ dữ liệu VirtualSize được sao chép vào bộ nhớ; Phần còn lại là làm ngơ. Vì OllyDbg chỉ sử dụng SizeOfRawData nên việc đặt SizeofRawData thành giá trị lớn như 0x77777777 sẽ khiến OllyDbg gặp sự cố.

- Cách dễ nhất để khắc phục kỹ thuật chống gỡ lỗi này là sửa đổi tiêu đề PE một cách thủ công và đặt SizeOfRawData bằng trình soạn thảo hex thành thay đổi giá trị gần với VirtualSize. (Lưu ý rằng, theo đặc điểm kỹ thuật, giá trị này phải là bội số của giá trị FileAlignment từ IMAGE_OPTIONAL_HEADER). PE Explorer là một chương trình tuyệt vời để sử dụng cho mục đích này vì nó không bị đánh lừa bởi giá trị lớn của SizeofRawData.



### The OutputDebugString Vulnerability

- Phần mềm độc hại thường cố gắng khai thác lỗ hổng chuỗi định dạng trong phiên bản 1.1 của OllyDbg, bằng cách cung cấp một chuỗi %s làm tham số cho OutputDebugString để khiến OllyDbg gặp sự cố. Cảnh giác với các cuộc gọi đáng ngờ như OutputDebugString ('%s%s%s%s%s%s%s%s%s%s%s%s%s%s'). Nếu cuộc gọi này được thực thi, trình gỡ lỗi của bạn sẽ crash.



## Conclusion

- Chương này đã giới thiệu cho bạn một số kỹ thuật chống gỡ lỗi phổ biến. Cần phải có sự kiên nhẫn và kiên trì để học cách nhận biết và vượt qua các kỹ thuật chống gỡ lỗi. Hãy chắc chắn ghi chú trong quá trình phân tích của bạn và nhớ vị trí của bất kỳ kỹ thuật chống gỡ lỗi nào và cách bạn bỏ qua chúng; làm như vậy sẽ giúp ích cho bạn nếu bạn cần khởi động lại quá trình gỡ lỗi quá trình. 

- Hầu hết các kỹ thuật chống gỡ lỗi có thể được phát hiện bằng cách sử dụng thông thường, trong khi gỡ lỗi một quá trình một cách chậm rãi . Kỹ thuật chống gỡ lỗi phổ biến nhất liên quan đến việc truy cập fs:[30h], gọi lệnh gọi Windows API hoặc thực hiện kiểm tra thời gian. 

- Tất nhiên, giống như tất cả các phân tích phần mềm độc hại, cách tốt nhất để học cách ngăn chặn kỹ thuật chống gỡ lỗi là tiếp tục đảo ngược và nghiên cứu phần mềm độc hại. Tác giả phần mềm độc hại luôn tìm kiếm những cách mới để ngăn chặn trình gỡ lỗi và để luôn cảnh giác với các nhà phân tích phần mềm độc hại như bạn.
