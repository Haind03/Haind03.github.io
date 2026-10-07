---
title: "Anti Disassembly"
date: 2023-08-22 07:19:00 +0700
categories: ["Technique Reverse", "Ghi chép 2023"]
tags: [reverse-engineering, anti-disassembly, malware]
render_with_liquid: false
---
- Anti Disassembly sử dụng mã hoặc dữ liệu được chế tạo đặc biệt trong một chương trình để tạo ra các công cụ phân tích tháo gỡ một danh sách chương trình không chính xác. Kỹ thuật này được chế tạo bởi các tác giả phần mềm độc hại theo cách thủ công, với một công cụ riêng biệt trong quá trình xây dựng và triển khai hoặc đan xen vào mã nguồn phần mềm độc hại của họ.

- Tất cả phần mềm độc hại được thiết kế với một mục tiêu cụ thể: ghi nhật ký gõ phím, truy cập cửa sau, sử dụng một hệ thống mục tiêu để gửi quá nhiều email đến các máy chủ bị tê liệt, v.v. Tác giả phần mềm độc hại thường vượt ra ngoài chức năng cơ bản này để triển khai các kỹ thuật cụ thể để ẩn người dùng hoặc quản trị viên hệ thống, sử dụng rootkit hoặc xử lý tiêm chích hoặc để ngăn cản phân tích và
  phát hiện.

- Tác giả phần mềm độc hại sử dụng các kỹ thuật Anti Disassembly để trì hoãn hoặc ngăn chặn phân tích mã độc. Bất kỳ mã nào thực thi thành công đều có thể được thiết kế ngược, nhưng bằng cách bọc thép cho mã của họ bằng các kỹ thuật Anti Disassembly và chống gỡ lỗi, tác giả phần mềm độc hại nâng cao trình độ kỹ năng cần thiết của nhà phân tích phần mềm độc hại. Quá trình điều tra nhạy cảm với thời gian bị cản trở bởi nhà phân tích phần mềm độc hại không có khả năng hiểu được khả năng của phần mềm độc hại, lấy các chữ ký mạng và máy chủ có giá trị, đồng thời phát triển các thuật toán giải mã. Các lớp bảo vệ bổ sung này có thể làm cạn kiệt kỹ năng nội bộ ở nhiều tổ chức và yêu cầu chuyên gia tư vấn hoặc nghiên cứu lớn mức độ nỗ lực của dự án để thiết kế ngược.

- Ngoài việc trì hoãn hoặc ngăn cản quá trình phân tích của con người, tính năng Anti Disassembly còn cũng có hiệu quả trong việc ngăn chặn một số kỹ thuật phân tích tự động. Nhiều thuật toán phát hiện tương tự phần mềm độc hại và các công cụ heuristic chống vi-rút sử dụng phân tích tháo gỡ để xác định hoặc phân loại phần mềm độc hại. Bất kỳ thủ công hoặc tự động quy trình sử dụng các hướng dẫn chương trình riêng lẻ sẽ dễ bị ảnh hưởng bởi kỹ thuật chống phân tích được mô tả trong chương này.

## Understanding Anti-Disassembly

- Tháo gỡ không phải là một vấn đề đơn giản. Chuỗi mã thực thi có thể có nhiều biểu diễn tháo gỡ, một số có thể không hợp lệ và che khuất chức năng thực sự của chương trình. Khi triển khai chống tháo gỡ, tác giả phần mềm độc hại tạo ra một chuỗi đánh lừa trình giải mã tháo gỡ để hiển thị một danh sách các hướng dẫn khác với các hướng dẫn sẽ được thực thi.

- Các kỹ thuật chống tháo gỡ hoạt động bằng cách tận dụng các giả định và hạn chế của các bộ tháo rời. Ví dụ, bộ dịch ngược chỉ có thể đại diện cho từng byte của chương trình như một phần của một lệnh tại một thời điểm. Nếu trình dịch ngược bị lừa để tháo rời ở phần bù sai, một lệnh hợp lệ có thể bị ẩn khỏi chế độ xem. Ví dụ: kiểm tra đoạn mã sau đây:

                - Đoạn mã này đã được phân tách bằng cách sử dụng phân tách tuyến tính kỹ thuật, và kết quả là không chính xác. Đọc mã này, chúng tôi bỏ lỡ phần thông tin mà tác giả của nó đang cố che giấu. Chúng tôi thấy những gì dường như là một hướng dẫn cuộc gọi, nhưng mục tiêu của cuộc gọi là vô nghĩa `1` . Lệnh đầu tiên là lệnh jmp có mục tiêu không hợp lệ vì nó rơi vào giữa hướng dẫn tiếp theo. Anti-Disassembly 

- Bây giờ hãy kiểm tra cùng một chuỗi byte được phân tách bằng một chiến lược:

    - Đoạn này tiết lộ một trình tự ghi nhớ lắp ráp khác, và nó dường như được nhiều thông tin hơn. Ở đây, chúng ta thấy một cuộc gọi đến chức năng API Sleep ở `1`. Mục tiêu của lệnh jmp đầu tiên hiện được thể hiện chính xác, và chúng ta có thể thấy rằng nó nhảy tới một lệnh đẩy, sau đó là lệnh gọi tới chế độ Sleep.

- Byte trên dòng thứ ba của ví dụ này là 0xE8, nhưng byte này không bị chương trình cắt exe vì lệnh jmp bỏ qua nó. Đoạn này đã được phân tách bằng trình phân tách hướng dòng chảy, thay vì bộ phân tách tuyến tính được sử dụng trước đây. Trong trường hợp này, trình dịch ngược định hướng dòng chảy chính xác hơn vì logic của nó phản chiếu chặt chẽ hơn chương trình thực và không cố gắng dịch mã bất kỳ byte nào không phải là một phần của luồng thực thi. 

- Chúng ta sẽ thảo luận chi tiết hơn về lắp ráp dis định hướng và tuyến tính trong phần tiếp theo. Vì vậy, việc tháo gỡ không đơn giản như bạn có thể nghĩ. Các ví dụ tháo rời cho thấy hai bộ hướng dẫn hoàn toàn khác nhau cho cùng một tập hợp các byte. 

- Điều này chứng tỏ cách chống tháo gỡ có thể khiến trình tháo gỡ tạo ra một bộ hướng dẫn không chính xác cho một phạm vi byte nhất định. Một số kỹ thuật chống tháo gỡ là đủ chung để hoạt động trên hầu hết tháo rời, trong khi một số nhắm mục tiêu các sản phẩm cụ thể.

## Defeating Disassembly Algorithms

- Các kỹ thuật chống tháo gỡ được sinh ra từ những điểm yếu cố hữu trong các thuật toán tháo gỡ. Bất kỳ trình dịch ngược nào cũng phải đưa ra các giả định nhất định trong để trình bày mã nó đang phân tách rõ ràng. Khi những giả định này thất bại, tác giả phần mềm độc hại có cơ hội đánh lừa nhà phân tích phần mềm độc hại.

- Có hai loại thuật toán dịch ngược: tuyến tính và hướng luồng. Tháo gỡ tuyến tính dễ thực hiện hơn, nhưng nó cũng dễ bị lỗi hơn.

### Linear Disassembly

- Chiến lược phân tách tuyến tính lặp lại trên một khối mã, phân tách một hướng dẫn tại một thời điểm tuyến tính, không sai lệch. Chiến lược cơ bản này là được sử dụng bởi các hướng dẫn viết trình dịch ngược và được sử dụng rộng rãi bởi các trình gỡ lỗi.  Tháo gỡ tuyến tính sử dụng kích thước của lệnh tháo rời để xác định byte nào cần phân tách tiếp theo, bất kể hướng dẫn điều khiển luồng.

- Đoạn mã sau đây cho thấy việc sử dụng thư viện tháo gỡ libdisasm (http://sf.net/projects/bastard/files/libdisasm/) để triển khai thô trình dịch ngược trong một số dòng của C bằng cách sử dụng mã tháo tuyến tính

    - Trong ví dụ này, một bộ đệm dữ liệu có tên là bộ đệm chứa các lệnh để được tháo rời. Hàm x86_disasm sẽ tạo cấu trúc dữ liệu với các chi tiết cụ thể của hướng dẫn nó vừa tháo rời và trả về kích thước của chỉ dẫn. Vòng lặp tăng biến vị trí theo giá trị kích thước `1` nếu một hướng dẫn hợp lệ đã được tháo rời; ngược lại, nó tăng thêm một `2` . 

- Thuật toán này sẽ phân tách hầu hết mã mà không gặp vấn đề gì, nhưng nó sẽ giới thiệu các lỗi không thường xuyên ngay cả trong các tệp nhị phân không độc hại. Hạn chế chính của phương pháp này là nó sẽ phân tách quá nhiều mã. thuật toán sẽ tiếp tục phân tách một cách mù quáng cho đến khi kết thúc bộ đệm, ngay cả khi điều khiển luồng hướng dẫn sẽ chỉ khiến một phần nhỏ của bộ đệm thực thi.

- Trong tệp thực thi có định dạng PE, mã thực thi thường được chứa trong một phần duy nhất. Thật hợp lý khi cho rằng bạn có thể thoát khỏi chỉ với việc áp dụng thuật toán tháo gỡ tuyến tính này cho phần .text chứa mã, nhưng vấn đề là phần mã của gần như tất cả các tệp nhị phân cũng sẽ chứa dữ liệu không phải là hướng dẫn.

- Một trong những loại mục dữ liệu phổ biến nhất được tìm thấy trong phần mã là một giá trị con trỏ, được sử dụng trong thành ngữ chuyển đổi theo hướng bảng. 

- Sau đây đoạn tháo gỡ (từ bộ dịch ngược phi tuyến tính) hiển thị một hàm chứa các con trỏ chuyển đổi ngay sau mã chức năng.

    - Lệnh cuối cùng trong chức năng này là retn. Trong bộ nhớ, các byte ngay sau lệnh retn là các giá trị con trỏ bắt đầu bằng 401020 tại `1`, trong bộ nhớ sẽ xuất hiện dưới dạng chuỗi byte `20 10 40 00` trong hex. Bốn giá trị con trỏ này được hiển thị trong đoạn mã tạo thành 16 byte dữ liệu bên trong phần .text của tệp nhị phân này. Họ cũng xảy ra với tháo rời để hướng dẫn hợp lệ. 

- Đoạn tháo gỡ sau đây sẽ được tạo ra bởi một thuật toán tháo gỡ tuyến tính khi nó tiếp tục tháo gỡ các hướng dẫn bling ngoài phần cuối của hàm

    - Nhiều hướng dẫn trong đoạn này bao gồm nhiều byte. Chìa khóa cách mà các tác giả phần mềm độc hại khai thác các thuật toán tháo gỡ tuyến tính nằm trong việc cài đặt các byte dữ liệu tạo thành mã lệnh của các lệnh nhiều byte. 

- Ví dụ, hướng dẫn cuộc gọi cục bộ tiêu chuẩn là 5 byte, bắt đầu bằng opcode 0xE8. Nếu 16 byte dữ liệu cấu thành bảng chuyển đổi kết thúc bằng giá trị 0xE8, trình dịch ngược sẽ gặp opcode hướng dẫn cuộc gọi và xử lý 4 byte tiếp theo làm toán hạng cho lệnh đó, thay vì bắt đầu chức năng tiếp theo.

- Các thuật toán tháo gỡ tuyến tính là dễ bị đánh bại nhất vì chúng không thể phân biệt giữa mã và dữ liệu.

### Flow-Oriented Disassembly

- Một loại thuật toán tháo gỡ nâng cao hơn là trình biên dịch mã dis hướng dòng chảy. Đây là phương pháp được sử dụng bởi hầu hết các trình dịch ngược thương mại như IDA Pro.

- Sự khác biệt chính giữa tháo gỡ theo hướng dòng chảy và tuyến tính là trình dịch ngược không lặp lại một cách mù quáng trên bộ đệm, giả sử dữ liệu không là gì ngoài các hướng dẫn được đóng gói gọn gàng với nhau. 

- Thay vào đó, nó kiểm tra từng hướng dẫn và xây dựng một danh sách các vị trí để tháo rời. Đoạn sau hiển thị mã có thể được phân tách chính xác chỉ với bộ phân tách hướng dòng chảy.

- Ví dụ này bắt đầu bằng một bài kiểm tra và một bước nhảy có điều kiện. Khi trình dịch ngược dòng hướng đến lệnh rẽ nhánh có điều kiện jz tại `1`, nó lưu ý rằng tại một thời điểm nào đó trong tương lai, nó cần phải tháo rời vị trí loc_1A tại `5`. Bởi vì đây chỉ là một nhánh có điều kiện, lệnh tại `2`cũng là một khả năng trong quá trình thực thi, do đó trình dịch ngược sẽ tháo rời lệnh này.

- Các dòng tại `2`và `3` chịu trách nhiệm in chuỗi Không thành công màn hình. Theo sau đây là một lệnh jmp tại `4`. Trình phân tách định hướng dòng chảy sẽ thêm đích của loc_1D này vào danh sách các vị trí cần phân tách trong tương lai. Vì jmp là vô điều kiện nên trình dịch ngược sẽ không tự động tháo rời hướng dẫn ngay sau đó trong bộ nhớ. Thay vào đó, nó sẽ lùi lại và kiểm tra danh sách các địa điểm mà nó đã ghi chú trước đó, chẳng hạn như loc_1A và tháo rời bắt đầu từ thời điểm đó.

- Ngược lại, khi trình dịch ngược tuyến tính gặp lệnh jmp, nó sẽ tiếp tục phân tách một cách mù quáng các hướng dẫn một cách tuần tự trong bộ nhớ, bất kể luồng logic của mã. Trong trường hợp này, chuỗi Failed sẽ được phân tách dưới dạng mã, vô tình ẩn chuỗi ASCII và hai hướng dẫn cuối cùng trong đoạn ví dụ. Ví dụ: đoạn sau đây hiển thị cùng một mã được phân tách bằng phân tách tuyến tínhthuật toán

- Trong tháo gỡ tuyến tính, bộ tháo rời không có lựa chọn nào để thực hiện hướng dẫn để tháo rời tại một thời điểm nhất định. Bộ tháo rời định hướng dòng chảy làm cho lựa chọn và giả định. Mặc dù các giả định và lựa chọn có vẻ như không cần thiết, hướng dẫn mã máy đơn giản là phức tạp bởi bổ sung các khía cạnh mã có vấn đề như con trỏ, ngoại lệ và phân nhánh có điều kiện. 

- Các nhánh có điều kiện cung cấp cho trình dịch ngược dòng chảy một sự lựa chọn hai nơi để tháo rời: nhánh đúng hoặc nhánh sai. Trong mã được tạo bởi trình biên dịch điển hình, sẽ không có sự khác biệt về đầu ra nếu trình dịch ngược mã xử lý nhánh đúng hoặc sai trước. 

- Trong mã lắp ráp viết tay và mã chống tháo gỡ, tuy nhiên, hai nhánh thường có thể tạo ra sự tháo gỡ khác nhau cho cùng một khối mã. Khi có xung đột, hầu hết những người phân tách tin tưởng vào cách giải thích ban đầu của họ về một vị trí nhất định trước tiên. Hầu hết trình phân tách hướng dòng chảy sẽ xử lý (và do đó tin tưởng) nhánh sai của bất kỳ bước nhảy có điều kiện nào trước. 

- Hình 15-1 cho thấy một chuỗi các byte và máy tương ứng của chúng hướng dẫn. Lưu ý chuỗi xin chào ở giữa hướng dẫn. Khi chương trình thực thi, chuỗi này bị bỏ qua bởi lệnh gọi, và 6 byte và bộ kết thúc NULL không bao giờ được thực hiện như hướng dẫn.

- Lệnh gọi là một nơi khác mà bộ dịch ngược phải thực hiện một quyết định. Vị trí đang được gọi sẽ được thêm vào danh sách tháo gỡ trong tương lai, cùng với vị trí ngay sau cuộc gọi. 

- Cũng giống như câu điều kiện lệnh nhảy, hầu hết các trình dịch ngược sẽ tháo rời các byte sau lệnh gọi trước và vị trí được gọi sau. Trong lắp ráp viết tay, các nhà ngữ pháp chuyên nghiệp sẽ thường sử dụng lệnh gọi để đưa con trỏ đến một mảnh cố định dữ liệu thay vì thực sự gọi một chương trình con. 

- Trong ví dụ này, lệnh gọi được sử dụng để tạo một con trỏ cho chuỗi hello trên ngăn xếp. Các pop sau lệnh gọi sau đó lấy giá trị này ra khỏi đầu ngăn xếp và đặt nó vào một thanh ghi (EAX trong trường hợp này). Khi chúng tôi phân tách tệp nhị phân này bằng IDA Pro, chúng tôi thấy rằng nó đã tạo ra quá trình phân tách không như chúng tôi mong đợi:

- Hóa ra, chữ cái đầu tiên của chuỗi xin chào là chữ h, đó là 0x68 ở dạng thập lục phân. Đây cũng là mã lệnh của lệnh 5 byte `1` đẩy DWORD. Trình kết thúc null cho chuỗi xin chào hóa ra cũng là dấu đầu tiên byte của một lệnh hợp pháp khác. Trình dịch ngược định hướng dòng chảy trong IDA Pro đã quyết định xử lý luồng tháo gỡ tại `1` (ngay sau lệnh gọi) trước khi xử lý mục tiêu của lệnh gọi, và do đó tạo ra hai hướng dẫn sai lầm này. Nếu nó đã xử lý mục tiêu đầu tiên, nó vẫn sẽ tạo ra lệnh đẩy đầu tiên, nhưng hướng dẫn sau khi đẩy sẽ mâu thuẫn với hướng dẫn thực nó bị tháo rời do mục tiêu cuộc gọi. 

- Nếu IDA Pro tạo ra kết quả không chính xác, bạn có thể chuyển đổi byte theo cách thủ công từ dữ liệu sang hướng dẫn hoặc hướng dẫn đến dữ liệu bằng cách sử dụng phím C hoặc D trên bàn phím, như sau:  
  
  - Nhấn phím C sẽ chuyển vị trí con trỏ thành mã.  
  
  - Nhấn phím D chuyển vị trí con trỏ thành dữ liệu.
  
  - Đây là chức năng tương tự sau khi dọn dẹp thủ công:

## Anti-Disassembly Techniques

- Cách chính mà phần mềm độc hại có thể buộc trình dịch ngược tạo ra tốc độ phân tách không chính xác là tận dụng các lựa chọn của trình dịch ngược và giả thiết. Các kỹ thuật chúng ta sẽ xem xét trong chương này khai thác hầu hết các giả định cơ bản của trình dịch ngược và thường dễ dàng được sửa bởi một nhà phân tích phần mềm độc hại. 

- Các kỹ thuật tiên tiến hơn liên quan đến việc tận dụng thông tin mà trình dịch ngược thường không có quyền truy cập, cũng như tạo mã không thể tách rời hoàn toàn với danh sách lắp ráp thông thường. 
  
  ### Jump Instructions with the Same Target

- Kỹ thuật chống tháo gỡ phổ biến nhất được thấy trong thực tế là hai hướng dẫn nhảy có điều kiện quay lưng lại với nhau mà cả hai đều trỏ đến cùng một mục tiêu. 

- Vì ví dụ: nếu jz loc_512 được theo sau bởi jnz loc_512, thì vị trí loc_512 sẽ luôn được nhảy tới. Sự kết hợp của jz với jnz trên thực tế là một jmp không có điều kiện, nhưng trình dịch ngược không nhận ra nó như vậy bởi vì nó chỉ tháo rời một hướng dẫn tại một thời điểm. Khi trình dịch ngược gặp phải jnz, nó tiếp tục phân tách nhánh sai của hướng dẫn này, mặc dù thực tế là nó sẽ không bao giờ được thực hiện trong thực tế.

- Đoạn mã sau đây cho thấy diễn giải đầu tiên của IDA Pro về một phần của mã được bảo vệ bằng kỹ thuật này:

- Trong ví dụ này, lệnh ngay sau hai lệnh nhảy có điều kiện dường như là lệnh gọi tại `1`, bắt đầu với byte 0xE8. Tuy nhiên, đây không phải là trường hợp vì cả hai bước nhảy có điều kiện hướng dẫn thực sự trỏ 1 byte ngoài byte 0xE8. Khi đoạn này được xem bằng IDA Pro, mã tham chiếu chéo hiển thị tại `2` loc_4011C4 sẽ xuất hiện bằng màu đỏ, thay vì màu xanh tiêu chuẩn, vì các tham chiếu thực tế điểm bên trong hướng dẫn tại vị trí này, thay vì phần đầu của chỉ dẫn. 

- Với tư cách là nhà phân tích phần mềm độc hại, đây là dấu hiệu đầu tiên cho thấy tính năng chống tháo gỡ có thể được sử dụng trong mẫu bạn đang phân tích. 

- Sau đây là phần tháo gỡ của cùng một mã, nhưng lần này đã được sửa với phím D, để biến byte ngay sau lệnh jnz thành dữ liệu và phím C để biến các byte tại loc_4011C5 thành hướng dẫn.

- Cột bên trái trong các ví dụ này hiển thị các byte cấu thành lệnh. Hiển thị trường này là tùy chọn, nhưng điều quan trọng là khi học chống tháo gỡ. Để hiển thị các byte này (hoặc tắt chúng), chọn Options  =>General.

- Tùy chọn Number of Opcode Byte cho phép bạn nhập một số cho biết bạn muốn hiển thị bao nhiêu byte. Hình 15-2 hiển thị chuỗi byte trong ví dụ này bằng đồ họa.

### A Jump Instruction with a Constant Condition

- Một kỹ thuật chống tháo rời khác thường được tìm thấy trong tự nhiên bao gồm một lệnh nhảy có điều kiện duy nhất được đặt ở nơi điều kiện sẽ luôn giống nhau. 

- Đoạn mã sau sử dụng kỹ thuật này

- Lưu ý rằng đoạn mã này bắt đầu bằng lệnh xor eax, eax. Hướng dẫn này sẽ đặt thanh ghi EAX thành 0 và, như một sản phẩm phụ, đặt cờ 0. Các hướng dẫn tiếp theo là một bước nhảy có điều kiện sẽ nhảy nếu cờ 0 được đặt. 

- TRONG thực tế, điều này hoàn toàn không có điều kiện, vì chúng tôi có thể đảm bảo rằng cờ 0 sẽ luôn được đặt tại thời điểm này trong chương trình. 

- Như đã thảo luận trước đây, trình dịch ngược sẽ xử lý nhánh sai đầu tiên, mã này sẽ tạo ra mã xung đột với nhánh thực và vì nó xử lý nhánh sai trước, nó tin tưởng nhánh đó hơn. 

- Như bạn đã học, bạn có thể sử dụng phím D trên bàn phím khi con trỏ của bạn đang ở trên một dòng mã để biến mã thành dữ liệu và nhấn phím C sẽ biến dữ liệu thành mã số. Sử dụng hai phím tắt này, một nhà phân tích phần mềm độc hại có thể sửa lỗi này mảnh và để nó hiển thị đường dẫn thực thi, như sau:

- Trong ví dụ này, byte 0xE9 được sử dụng chính xác như byte 0xE8 trong ví dụ trước. E9 là mã lệnh cho lệnh jmp 5 byte và E8 là opcode cho lệnh gọi 5 byte.

- Trong mỗi trường hợp, bằng cách đánh lừa trình phân tách để phân tách vị trí này, 4 byte theo sau mã lệnh này là ẩn khỏi tầm nhìn một cách hiệu quả. Hình 15-3 cho thấy ví dụ này bằng đồ thị.

### Impossible Disassembly

- Trong các phần trước, chúng ta đã kiểm tra mã bị tháo rời không đúng cách trong lần thử đầu tiên do trình dịch ngược thực hiện, nhưng với một lỗi tương tác. trình dịch ngược như IDA Pro, chúng tôi có thể làm việc với trình dịch ngược và có nó tạo ra kết quả chính xác. 

- Tuy nhiên, trong một số điều kiện, không có danh sách lắp ráp truyền thống nào thể hiện chính xác các hướng dẫn được thực thi. Chúng tôi sử dụng thuật ngữ tháo gỡ không thể cho các điều kiện như vậy, nhưng thuật ngữ không hoàn toàn chính xác. 

- Bạn có thể tháo rời những kỹ thuật này, nhưng bạn sẽ cần một cách trình bày mã rất khác so với những gì hiện được cung cấp bởi những người tháo rời. Các kỹ thuật chống tháo gỡ đơn giản mà chúng ta đã thảo luận sử dụng một byte dữ liệu được đặt một cách chiến lược sau lệnh nhảy có điều kiện, với ý tưởng rằng việc tháo gỡ bắt đầu từ byte này sẽ ngăn chặn hướng dẫn thực sự theo sau không bị tháo rời vì byte được chèn vào là mã lệnh cho một hướng dẫn đa byte. 

- Chúng tôi sẽ gọi đây là byte lừa đảo vì nó không phải là một phần của chương trình và chỉ có trong mã để loại bỏ trình dịch ngược. Trong tất cả những điều này ví dụ, byte giả mạo có thể được bỏ qua. 

- Nhưng nếu không thể bỏ qua byte lừa đảo thì sao? Điều gì sẽ xảy ra nếu nó là một phần của lệnh hợp pháp thực sự được thực thi trong thời gian chạy? Ở đây, chúng ta bắt gặp một kịch bản phức tạp trong đó bất kỳ byte đã cho nào cũng có thể là một phần của nhiều hướng dẫn được thực thi. 

- Không có bộ phân tách nào hiện có trên thị trường sẽ đại diện cho một một byte như là một phần của hai hướng dẫn, nhưng bộ xử lý không có như vậy giới hạn. 

- Hình 15-4 cho thấy một ví dụ. 
  
  - Lệnh đầu tiên trong chuỗi 4 byte này là một lệnh jmp 2 byte. 
  
  - Mục tiêu của bước nhảy là byte thứ hai của chính nó.
  
  - Điều này không gây ra lỗi, vì byte FF là byte đầu tiên của byte tiếp theo Lệnh 2 byte, inc eax.

                                - Tình trạng khó khăn khi cố gắng biểu diễn chuỗi này dưới dạng tháo rời là nếu chúng ta chọn biểu diễn byte FF như một phần của lệnh jmp, thì nó sẽ không có sẵn để hiển thị ở phần đầu của hướng dẫn inc eax. Byte FF là một phần của cả hai lệnh thực sự thực thi và trình dịch ngược hiện đại không có cách nào biểu diễn điều này. 

- Chuỗi 4 byte này tăng EAX, rồi giảm nó, đây thực sự là một công việc phức tạp trình tự NOP. Nó có thể được chèn vào hầu hết mọi vị trí trong chương trình để phá vỡ chuỗi tháo gỡ hợp lệ. 

- Để giải quyết vấn đề này, một nhà phân tích phần mềm độc hại có thể chọn thay thế toàn bộ chuỗi này bằng các lệnh NOP bằng cách sử dụng tập lệnh IDC hoặc IDAPython gọi hàm PatchByte. 

- Một cách khác là đơn giản biến tất cả thành dữ liệu bằng phím D, do đó quá trình tháo gỡ sẽ tiếp tục như mong đợi ở cuối 4 byte. Để có một cái nhìn thoáng qua về sự phức tạp có thể đạt được với những loại này trình tự hướng dẫn, hãy kiểm tra một mẫu vật nâng cao hơn. 

- Hình 15-5 hiển thị một ví dụ hoạt động theo nguyên tắc giống như ví dụ trước, trong đó một số byte là một phần của nhiều hướng dẫn

        - Lệnh đầu tiên trong chuỗi này là lệnh mov 4 byte. Cuối cùng 2 byte đã được tô sáng vì cả hai đều là một phần của hướng dẫn này và cũng là hướng dẫn riêng của họ để được thực hiện sau này. 
  
  - Hướng dẫn đầu tiên điền dữ liệu vào thanh ghi AX. 
  
  - Hướng dẫn thứ hai, một xor, sẽ bằng không ra khỏi thanh ghi này và đặt cờ bằng không. 
  
  - Lệnh thứ ba là lệnh có điều kiện nhảy sẽ nhảy nếu cờ 0 được đặt, nhưng nó thực sự vô điều kiện, vì hướng dẫn trước đó sẽ luôn đặt cờ bằng không. bộ tháo rời sẽ quyết định tách lệnh ngay sau lệnh jz, lệnh này sẽ bắt đầu bằng byte 0xE8, opcode cho 5 byte gọi hướng dẫn. 
  
  - Lệnh bắt đầu bằng byte E8 sẽ không bao giờ thực hiện trên thực tế. 
  
  - Trình dịch mã trong trường hợp này không thể mã hóa mục tiêu của lệnh jz vì các byte này đã được biểu diễn chính xác dưới dạng một phần của hướng dẫn mov. Mã mà jz trỏ tới sẽ luôn bị cắt exe, vì cờ 0 sẽ luôn được đặt tại thời điểm này. 
  
  - Hướng dẫn jz trỏ đến giữa lệnh mov 4 byte đầu tiên. 2 byte cuối cùng của cái này lệnh là toán hạng sẽ được chuyển vào thanh ghi. Khi được tháo rời hoặc tự thực thi, chúng tạo thành một lệnh jmp sẽ nhảy tới 5 byte từ cuối lệnh. 

- Khi xem lần đầu trong IDA Pro, trình tự này sẽ giống như sau

        - Vì không có cách nào để làm sạch mã để tất cả các lệnh thực thi được thể hiện, nên chúng ta phải chọn các lệnh để bỏ vào. Mạng tác dụng phụ của trình tự chống tháo gỡ này là thanh ghi EAX được đặt thành số không. 

- Nếu bạn thao tác mã bằng phím D và C trong IDA Pro để chỉ hướng dẫn hiển thị là hướng dẫn xor và hướng dẫn ẩn, kết quả của bạn sẽ giống như sau

- Đây là một giải pháp có thể chấp nhận được vì nó chỉ hiển thị các hướng dẫn có liên quan để hiểu chương trình. Tuy nhiên, giải pháp này có thể can thiệp vào các quá trình phân tích như vẽ đồ thị, vì rất khó để cho biết chính xác cách lệnh xor hoặc chuỗi pop và retn được thực thi. 

- Một giải pháp hoàn chỉnh hơn là sử dụng chức năng PatchByte từ Ngôn ngữ kịch bản IDC để sửa đổi các byte còn lại để chúng xuất hiện dưới dạng NOP hướng dẫn. 

- Ví dụ này có hai vùng byte chưa phân tách mà chúng ta cần chuyển đổi thành lệnh NOP: 4 byte bắt đầu từ địa chỉ bộ nhớ 0x004011C0 và 3 byte bắt đầu từ địa chỉ bộ nhớ 0x004011C6. 

- IDAPython sau đây tập lệnh sẽ chuyển đổi các byte này thành byte NOP (0x90)

- Mã này có cách tiếp cận lâu dài bằng cách tạo một hàm tiện ích được gọi là NopBytes thành NOP-ra một phạm vi byte. 

- Sau đó, nó sử dụng chức năng tiện ích đó để chống lại hai phạm vi mà chúng ta cần phải sửa chữa. Khi tập lệnh này được thực thi, kết quả phần tháo rời rõ ràng, dễ đọc và tương đương về mặt logic với bản gốc

- Tập lệnh IDAPython mà chúng tôi vừa tạo hoạt động tuyệt vời cho kịch bản này, nhưng tính hữu dụng của nó bị hạn chế khi áp dụng cho các thử thách mới. 

- ĐẾN sử dụng lại tập lệnh trước đó, nhà phân tích phần mềm độc hại phải quyết định phần bù và độ dài byte cần thay đổi thành lệnh NOP và chỉnh sửa thủ công script với các giá trị mới.

### NOP-ing Out Instructions with IDA Pro

- Với một chút kiến ​​thức về IDA Python, chúng ta có thể phát triển một tập lệnh cho phép các nhà phân tích phần mềm độc hại để dễ dàng hướng dẫn NOP-out khi họ thấy phù hợp. Sau đây tập lệnh thiết lập phím nóng ALT-N. 

- Khi tập lệnh này được thực thi, bất cứ khi nào người dùng nhấn ALT-N, IDA Pro sẽ NOP-ra lệnh hiện tại tại vị trí con trỏ. Nó cũng sẽ thuận tiện chuyển con trỏ sang trang tiếp theo hướng dẫn để tạo điều kiện dễ dàng NOP-out các khối mã lớn.

## Obscuring Flow Control

- Các trình dịch ngược hiện đại như IDA Pro thực hiện rất tốt công việc tương quan gọi hàm và suy luận thông tin cấp cao dựa trên kiến ​​thức về cách các chức năng có liên quan với nhau. 

- Loại phân tích này hoạt động tốt chống lại mã được viết theo phong cách lập trình tiêu chuẩn với trình soạn thảo com tiêu chuẩn, nhưng dễ dàng bị tác giả phần mềm độc hại đánh bại.

### The Function Pointer Problem

- Con trỏ hàm là một thành ngữ lập trình phổ biến trong lập trình C ngôn ngữ và được sử dụng rộng rãi đằng sau hậu trường trong C++. Mặc dù vậy, họ vẫn chứng tỏ là có vấn đề đối với một trình dịch ngược. 

- Sử dụng con trỏ hàm theo cách dự định trong chương trình C có thể làm giảm đáng kể thông tin có thể được suy luận tự động về dòng chương trình. 

- Nếu con trỏ hàm được sử dụng trong lắp ráp viết tay hoặc thủ công theo cách không chuẩn trong mã nguồn, kết quả có thể khó đảo ngược kỹ sư nếu không có phân tích động. 

- Danh sách lắp ráp sau đây cho thấy hai chức năng. Chức năng thứ hai sử dụng cái đầu tiên thông qua một con trỏ hàm

- Mặc dù ví dụ này không đặc biệt khó để thiết kế ngược, nhưng nó tiết lộ một vấn đề quan trọng. Hàm sub_4011C0 thực sự được gọi từ hai vị trí khác nhau ( `2` và `3`) trong hàm sub_4011D0, nhưng nó chỉ hiển thị một tham chiếu chéo tại `1`. Điều này là do IDA Pro có thể phát hiện tham chiếu đến hàm khi phần bù của nó được tải vào một biến ngăn xếp trên dòng 004011D5. 

- Tuy nhiên, điều mà IDA Pro không phát hiện ra là thực tế là chức năng sau đó được gọi hai lần từ các vị trí `2` và `3`. Bất kỳ thông tin pro totype chức năng nào thường được tự động chuyển sang cuộc gọi chức năng cũng bị mất. Khi được sử dụng rộng rãi và kết hợp với các thiết bị chống tháo rời khác kỹ thuật, con trỏ hàm có thể kết hợp rất nhiều sự phức tạp và khó khăn của kỹ thuật đảo ngược

### Adding Missing Code Cross-References in IDA Pro

- Tất cả thông tin không được tự động lan truyền lên trên, chẳng hạn như tên đối số hàm, có thể được thêm theo cách thủ công dưới dạng nhận xét của nhà phân tích phần mềm độc hại. 

- Để thêm các tham chiếu chéo thực tế, chúng ta phải sử dụng ngôn ngữ IDC (hoặc IDAPython) để nói với IDA Pro rằng hàm sub_4011C0 thực sự được gọi từ hai vị trí trong chức năng khác. 

- Chức năng IDC chúng tôi sử dụng được gọi là AddCodeXref. Phải mất ba đối số: vị trí xuất phát của tham chiếu, vị trí mà tham chiếu đến và luồng kiểu. Hàm có thể hỗ trợ một số loại luồng khác nhau, nhưng đối với các vị trí thuần túy của chúng tôi, hữu ích nhất là fl_CF cho lệnh gọi thông thường hoặc fl_JF cho lệnh nhảy. Để sửa danh sách mã lắp ráp ví dụ trước trong IDA Pro, tập lệnh sau đã được thực thi

### Return Pointer Abuse

- Lệnh gọi và lệnh jmp không phải là lệnh duy nhất để chuyển điều khiển bên trong một chương trình. Bản sao của lệnh gọi là retn (cũng được gửi lại dưới dạng ret). Lệnh gọi hoạt động giống như lệnh jmp, ngoại trừ nó đẩy một con trỏ trở lại trên ngăn xếp. Điểm trở về sẽ là ký ức địa chỉ ngay sau khi kết thúc lệnh gọi.

- Vì cuộc gọi là sự kết hợp giữa jmp và push, retn là sự kết hợp giữa pop và jmp. Lệnh retn bật giá trị từ đỉnh ngăn xếp và nhảy với nó. Nó thường được sử dụng để trả về từ một lệnh gọi hàm, nhưng không có lý do kiến ​​trúc nào khiến nó không thể được sử dụng để kiểm soát luồng chung. 

- Khi lệnh retn được sử dụng theo những cách khác ngoài việc quay lại từ một cuộc gọi chức năng, ngay cả những bộ phân tách thông minh nhất cũng có thể bị bỏ lại trong bóng tối. 

- Kết quả rõ ràng nhất của kỹ thuật này là trình dịch ngược không hiển thị bất kỳ tham chiếu chéo mã nào đến mục tiêu được nhảy tới. chìa khóa khác lợi ích của kỹ thuật này là trình dịch ngược sẽ kết thúc sớm chức năng.

- Hãy kiểm tra đoạn lắp ráp sau:

- Đây là một hàm đơn giản lấy một số và trả về tích của số đó nhân với 42. Thật không may, IDA Pro không thể suy ra bất kỳ thông tin có ý nghĩa về chức năng này bởi vì nó đã bị đánh bại bởi một hướng dẫn giả mạo retn. 

- Lưu ý rằng nó đã không phát hiện ra sự hiện diện của một đối số cho chức năng này. Ba hướng dẫn đầu tiên hoàn thành nhiệm vụ chuyển đến điểm bắt đầu thực sự của chức năng. 

- Hãy xem xét từng những hướng dẫn này. Lệnh đầu tiên trong chức năng này là lệnh gọi $+5. Hướng dẫn này đơn giản gọi vị trí ngay sau chính nó, dẫn đến một con trỏ tới vị trí bộ nhớ này được đặt trên ngăn xếp. 

- Trong ví dụ cụ thể này, các giá trị 0x004011C5 sẽ được đặt ở đầu ngăn xếp sau hướng dẫn này thực thi. Đây là một hướng dẫn phổ biến được tìm thấy trong mã cần tự tham chiếu hoặc độc lập với vị trí và sẽ được đề cập chi tiết hơn trong Chương 19.

- Hướng dẫn tiếp theo là thêm [esp+4+var_4], 5. Nếu bạn đã quen đọc IDA Pro, bạn có thể nghĩ rằng hướng dẫn này đang tham chiếu đến một biến ngăn xếp var_4. Trong trường hợp này, phân tích khung ngăn xếp của IDA Pro không chính xác, và hướng dẫn này không đề cập đến biến ngăn xếp bình thường có thể được đặt tên tự động là var_4 trong một hàm thông thường. Điều này có vẻ khó hiểu lúc đầu, nhưng lưu ý rằng ở đầu hàm, var_4 được định nghĩa là hằng số -4. Điều này có nghĩa là nội dung bên trong dấu ngoặc là [esp+4+(-4)], có thể cũng được biểu diễn dưới dạng [esp+0] hoặc đơn giản là [esp]. 

- Hướng dẫn này đang thêm năm thành giá trị ở đầu ngăn xếp, là 0x004011C5. kết quả của hướng dẫn bổ sung là giá trị ở đầu ngăn xếp sẽ là 0x004011CA. Lệnh cuối cùng trong chuỗi này là lệnh retn, lệnh này có mục đích duy nhất của việc lấy giá trị này ra khỏi ngăn xếp và nhảy tới nó. Nếu bạn kiểm tra mã tại vị trí 0x004011CA, nó có vẻ hợp pháp bắt đầu của một chức năng trông khá bình thường. 

- Chức năng “thực” này là được IDA Pro xác định là không phải là một phần của bất kỳ chức năng nào do sự hiện diện của của hướng dẫn retn lừa đảo. Để sửa chữa ví dụ này, chúng ta có thể vá qua ba hướng dẫn đầu tiên với các hướng dẫn NOP và điều chỉnh các ranh giới chức năng để bao trùm thực tế chức năng.

- Để điều chỉnh ranh giới chức năng, đặt con trỏ vào IDA Pro bên trong chức năng bạn muốn điều chỉnh và nhấn ALT-P. Điều chỉnh kết thúc chức năng địa chỉ đến địa chỉ bộ nhớ ngay sau lệnh cuối cùng trong hàm. Để thay thế một số hướng dẫn đầu tiên bằng nop, hãy tham khảo kỹ thuật tập lệnh được mô tả trong “Hướng dẫn NOP-ing Out với IDA Pro” trên trang 340

### 

### Misusing Structured Exception Handlers

- Cơ chế Xử lý ngoại lệ có cấu trúc (SEH) cung cấp một phương thức điều khiển luồng không thể bị theo dõi bởi trình dịch ngược và sẽ đánh lừa người sửa lỗi. SEH là một tính năng của kiến ​​trúc x86 và nhằm mục đích cung cấp một cách để chương trình xử lý các điều kiện lỗi một cách thông minh. 

- Các ngôn ngữ kết hợp chương trình như C++ và Ada chủ yếu dựa vào xử lý ngoại lệ và dịch tự nhiên sang SEH khi được biên dịch trên các hệ thống x86. Trước khi khám phá cách khai thác SEH để che khuất điều khiển luồng, hãy xem xét một vài khái niệm cơ bản về cách nó hoạt động. 

- Các ngoại lệ có thể được kích hoạt vì một số lý do, chẳng hạn như quyền truy cập vào vùng bộ nhớ không hợp lệ hoặc chia cho số không. Các ngoại lệ phần mềm bổ sung có thể được nêu ra bằng cách gọi chức năng RaiseException. Chuỗi SEH là một danh sách các chức năng được thiết kế để xử lý các trường hợp ngoại lệ bên trong luồng. Mỗi chức năng trong danh sách có thể xử lý ngoại lệ hoặc chuyển nó cho trình xử lý tiếp theo trong danh sách. 

- Nếu ngoại lệ làm cho nó tất cả các đến trình xử lý cuối cùng, thì nó được coi là một ngoại lệ chưa được xử lý. Trình xử lý ngoại lệ cuối cùng là đoạn mã chịu trách nhiệm kích hoạt hộp thông báo quen thuộc thông báo cho người dùng rằng “đã xảy ra một ngoại lệ chưa được xử lý”. 

- Ngoại lệ xảy ra thường xuyên trong hầu hết các quy trình, nhưng được xử lý âm thầm trước khi chúng chuyển sang trạng thái cuối cùng là làm hỏng quy trình và thông báo cho người dùng. Để tìm chuỗi SEH, HĐH kiểm tra thanh ghi phân đoạn FS. 

- Cái này thanh ghi chứa bộ chọn phân đoạn được sử dụng để truy cập vào Chủ đề Khối môi trường (TEB). 

- Cấu trúc đầu tiên trong TEB là Thread Khối thông tin (TIB). Yếu tố đầu tiên của TIB (và do đó byte đầu tiên của TEB) là một con trỏ tới chuỗi SEH. Chuỗi SEH là một danh sách liên kết đơn giản gồm các cấu trúc dữ liệu 8 byte được gọi là bản ghi EXCEPTION_REGISTRATION

- Phần tử đầu tiên trong bản ghi EXCEPTION_REGISTRATION trỏ tới bản ghi trước đó. Trường thứ hai là một con trỏ tới hàm xử lý. Danh sách được liên kết này hoạt động theo khái niệm như một ngăn xếp. Kỷ lục đầu tiên được được gọi là bản ghi cuối cùng được thêm vào danh sách. 

- Chuỗi SEH phát triển và co lại khi các lớp xử lý ngoại lệ trong một chương trình thay đổi do các lời gọi chương trình con và các khối xử lý ngoại lệ lồng nhau. Vì lý do này, SEH ghi lại luôn được xây dựng trên ngăn xếp. 

- Để sử dụng SEH đạt được điều khiển dòng bí mật, chúng ta không cần quan tâm chính chúng ta với bao nhiêu bản ghi ngoại lệ hiện có trong chuỗi. Chúng tôi chỉ cần hiểu cách thêm trình xử lý của riêng chúng tôi vào đầu danh sách này, như thể hiện trong Hình 15-6

- Để thêm một bản ghi vào danh sách này, chúng ta cần xây dựng một bản ghi mới trên cây rơm. Vì cấu trúc bản ghi chỉ đơn giản là hai DWORD, nên chúng tôi có thể thực hiện việc này với hai hướng dẫn đẩy. 

- Ngăn xếp tăng dần lên, vì vậy lần đẩy đầu tiên sẽ là con trỏ đến chức năng xử lý và lần đẩy thứ hai sẽ là con trỏ tới lần tiếp theo ghi. Chúng tôi đang cố gắng thêm một bản ghi vào đầu chuỗi, vì vậy bước tiếp theo bản ghi trong chuỗi khi chúng tôi hoàn thành sẽ là bản ghi hiện đang đứng đầu, bản ghi nào được trỏ đến bởi fs:[0]. 

- Đoạn mã sau thực hiện trình tự này

- Hàm ExceptionHandler sẽ được gọi đầu tiên bất cứ khi nào có ngoại lệ xảy ra. Hành động này sẽ tuân theo các ràng buộc do Microsoft áp đặt Ngăn chặn Thực thi Dữ liệu Phần mềm (Software DEP, còn được gọi là SafeSEH). Software DEP là một tính năng bảo mật ngăn chặn việc bổ sung các trình xử lý ngoại lệ của bên thứ ba khi chạy. 

- Đối với mục đích lắp ráp viết tay mã, có một số cách để giải quyết công nghệ này, chẳng hạn như sử dụng một trình biên dịch chương trình hợp ngữ có hỗ trợ cho các chỉ thị SafeSEH. 

- Sử dụng trình biên dịch C của Microsoft, tác giả có thể thêm /SAFESEH:NO vào dòng lệnh của trình liên kết để tắt tính năng này. Khi mã ExceptionHandler được gọi, ngăn xếp sẽ tăng mạnh bị thay đổi. May mắn thay, mục đích của chúng ta là không cần thiết phải kiểm tra đầy đủ tất cả các dữ liệu được thêm vào ngăn xếp tại thời điểm này. 

- Chúng ta phải hiểu đơn giản như thế nào để trả ngăn xếp về vị trí ban đầu trước ngoại lệ. Nhớ rằng mục tiêu của chúng tôi là che khuất điều khiển luồng và không xử lý đúng chương trình ngoại lệ. 

- Hệ điều hành thêm một trình xử lý SEH khác khi trình xử lý của chúng tôi được gọi. Trở về để chương trình hoạt động bình thường, chúng ta cần hủy liên kết không chỉ trình xử lý của mình, nhưng người xử lý này là tốt. 

- Do đó, chúng ta cần kéo con trỏ ngăn xếp ban đầu của mình từ đặc biệt + 8 thay vì đặc biệt.

- Hãy mang tất cả những kiến ​​thức này trở lại mục tiêu ban đầu của chúng ta là che khuất dòng chảy điều khiển. Đoạn sau chứa một đoạn mã từ Visual C++ nhị phân bí mật chuyển luồng sang một chương trình con. 

- Vì không có con trỏ đối với chức năng này và trình dịch ngược không hiểu SEH, nó xuất hiện dưới dạng mặc dù chương trình con không có tham chiếu nào và trình dịch ngược cho rằng mã ngay sau khi kích hoạt ngoại lệ sẽ được thực thi

- Trong ví dụ này, IDA Pro không chỉ bỏ sót một thực tế là chương trình con tại vị trí 401080 `1` không được gọi, nhưng nó thậm chí không thể tháo rời cái này chức năng. Mã này thiết lập một trình xử lý ngoại lệ một cách bí mật bằng cài đặt đầu tiên đăng ký EAX thành giá trị 40106C `2`, sau đó thêm 14h vào đó để tạo con trỏ tới hàm 401080. Một ngoại lệ chia cho 0 được kích hoạt bởi đặt ECX về 0 với xor ecx, ecx theo sau bởi div ecx tại `3`, chia thanh ghi EAX của ECX. 

- Hãy sử dụng phím C trong IDA Pro để biến dữ liệu tại vị trí 401080 thành mã và xem những gì đã được ẩn bằng cách sử dụng thủ thuật này.

## Thwarting Stack-Frame Analysis

- Trình dịch ngược nâng cao có thể phân tích các hướng dẫn trong hàm để suy ra việc xây dựng khung ngăn xếp của nó, cho phép chúng hiển thị các biến cục bộ và tham số liên quan đến hàm. Thông tin này cực kỳ có giá trị đối với nhà phân tích phần mềm độc hại, vì nó cho phép phân tích một chức năng duy nhất tại một thời điểm và cho phép nhà phân tích hiểu rõ hơn về đầu vào, đầu ra, và xây dựng. 

- Tuy nhiên, việc phân tích một hàm để xác định cấu trúc ngăn xếp của nó khung không phải là một khoa học chính xác. Cũng như nhiều khía cạnh khác của việc tháo gỡ, các thuật toán được sử dụng để xác định cấu trúc của khung ngăn xếp phải thực hiện một số giả định và dự đoán hợp lý nhưng thường có thể được khai thác bởi một tác giả phần mềm độc hại có kiến ​​thức. 

- Đánh bại phân tích khung ngăn xếp cũng sẽ ngăn hoạt động của một số các kỹ thuật phân tích, đáng chú ý nhất là plug-in Hex-Rays Decompiler cho IDA Pro, tạo mã giả giống như C cho một hàm. 

- Hãy bắt đầu bằng cách kiểm tra một chức năng đã được bọc thép để đánh bại phân tích khung ngăn xếp

- Các kỹ thuật chống phân tích khung ngăn xếp phụ thuộc nhiều vào trình biên dịch đã sử dụng. Tất nhiên, nếu phần mềm độc hại được viết hoàn toàn bằng hợp ngữ, thì tác giả được tự do sử dụng các kỹ thuật không chính thống hơn. Tuy nhiên, nếu phần mềm độc hại được tạo bằng ngôn ngữ cấp cao hơn như C hoặc C++, cần phải đặc biệt cẩn thận được đưa đến mã đầu ra có thể được thao tác.

- Trong Liệt kê 15-1, cột ở ngoài cùng bên trái là dòng IDA Pro tiêu chuẩn tiền tố, chứa tên phân đoạn và địa chỉ bộ nhớ cho mỗi chức năng. Cột tiếp theo bên phải hiển thị con trỏ ngăn xếp. Đối với mỗi lệnh, cột con trỏ ngăn xếp hiển thị giá trị của thanh ghi ESP tương ứng với vị trí của nó khi bắt đầu chức năng. 

- Quan điểm này cho thấy rằng chức năng này là một khung ngăn xếp dựa trên ESP chứ không phải là một khung dựa trên EBP, giống như hầu hết các chức năng. (Cột con trỏ ngăn xếp này có thể được kích hoạt trong IDA Pro thông qua menu Tùy chọn.) 

- Tại `1`, con trỏ ngăn xếp bắt đầu hiển thị dưới dạng số âm. Cái này sẽ không bao giờ xảy ra đối với một chức năng thông thường bởi vì điều đó có nghĩa là điều này chức năng có thể làm hỏng khung ngăn xếp của chức năng gọi. Trong danh sách này, IDA Pro cũng nói với chúng tôi rằng nó nghĩ hàm này có 62 đối số, trong đó nó nghĩ rằng 2 đang thực sự được sử dụng.

- NOTE Nhấn CTRL-K trong IDA Pro để kiểm tra chi tiết khung ngăn xếp khổng lồ này. nếu bạn cố gắng nhấn Y để cung cấp cho chức năng này một nguyên mẫu, bạn sẽ thấy một trong sự ghê tởm ghê tởm nhất của một nguyên mẫu chức năng mà bạn từng thấy. Như bạn có thể đoán, chức năng này không thực sự nhận 62 đối số. 

- Trong thực tế, nó không có đối số và có hai biến cục bộ. 

- Mật mã chịu trách nhiệm phá vỡ phân tích của IDA Pro nằm gần đầu chức năng, giữa các vị trí 00401546 và 0040155C. Đó là một con trai so sánh đơn giản với hai nhánh. Thanh ghi ESP đang được so sánh với giá trị 0x1000.

- Nếu nó ít hơn hơn 0x1000, thì nó sẽ thực thi mã ở 00401556; mặt khác, nó thực hiện mã tại 00401551. Mỗi nhánh thêm một số giá trị vào ESP—0x104 trên nhánh “nhỏ hơn” và 4 trên nhánh “lớn hơn hoặc bằng”. 

- Từ quan điểm của một nhà dịch thuật disas, có hai giá trị có thể có của phần bù con trỏ ngăn xếp tại thời điểm này, tùy thuộc vào nhánh nào đã được thực hiện. bộ tháo rời buộc phải đưa ra lựa chọn và may mắn cho tác giả phần mềm độc hại, nó đã bị lừa vào việc đưa ra lựa chọn sai lầm. 

- Trước đó, chúng ta đã thảo luận về các lệnh rẽ nhánh có điều kiện, vốn không có điều kiện bởi vì chúng tồn tại khi điều kiện không đổi, chẳng hạn như lệnh jz ngay sau lệnh xor eax, eax. 

- Đổi mới các tác giả của trình dịch ngược có thể mã hóa các ngữ nghĩa đặc biệt trong thuật toán của họ để theo dõi trạng thái cờ được đảm bảo như vậy và phát hiện sự hiện diện của điều kiện giả mạo như vậy cành cây. Mã này sẽ hữu ích trong nhiều tình huống và sẽ rất đơn giản, mặc dù rườm rà, để thực hiện. 

- Trong Liệt kê 15-1, lệnh cmp esp, 1000h sẽ luôn tạo ra một giá trị cố định kết quả. Một nhà phân tích phần mềm độc hại có kinh nghiệm có thể nhận ra rằng mức thấp nhất trang bộ nhớ trong quy trình Windows sẽ không được sử dụng làm ngăn xếp và do đó sự so sánh này hầu như được đảm bảo để luôn dẫn đến nhánh “lớn hơn Chống tháo gỡ 349 hoặc bằng với” được thực thi. 

- Chương trình tháo gỡ không có mức độ trực giác này. Công việc của nó là chỉ cho bạn các hướng dẫn. Nó không được thiết kế để đánh giá mọi quyết định trong mã dựa trên một tập hợp các tình huống trong thế giới thực. 

- Mấu chốt của vấn đề là trình dịch ngược giả định rằng phần bổ sung đặc biệt, hướng dẫn 104h là hợp lệ và có liên quan, đồng thời điều chỉnh cách giải thích của nó về ngăn xếp cho phù hợp. Lệnh add esp, 4 trong nhánh lớn hơn hoặc bằng chỉ ở đó để điều chỉnh lại ngăn xếp sau lệnh sub esp, 4 mà đến trước khi so sánh. 

- Kết quả cuối cùng trong thời gian thực là ESP giá trị sẽ giống hệt với giá trị trước khi bắt đầu chuỗi tại địa chỉ 00401546. 

- Để khắc phục những điều chỉnh nhỏ đối với khung ngăn xếp (đôi khi xảy ra do bản chất vốn có thể sai sót của phân tích khung ngăn xếp), trong IDA Pro, bạn có thể đặt con trỏ trên một dòng tháo cụ thể và nhấn ALT-K để nhập điều chỉnh cho con trỏ ngăn xếp. 

- Trong nhiều trường hợp, chẳng hạn như trong Liệt kê 15-1, nó có thể tỏ ra hiệu quả hơn khi vá các hướng dẫn thao tác khung ngăn xếp, như trong các ví dụ trước.

## Conclusion

- Chống tháo gỡ không bị giới hạn trong các kỹ thuật được thảo luận trong chương này. Đó là một lớp kỹ thuật tận dụng những khó khăn vốn có trong Phân tích. Các chương trình nâng cao như trình dịch ngược hiện đại thực hiện xuất sắc công việc xác định hướng dẫn nào cấu thành một chương trình, nhưng chúng vẫn yêu cầu các giả định và lựa chọn được thực hiện trong quá trình. Đối với mỗi lựa chọn hoặc giả định có thể được thực hiện bởi một bộ tách rời, có thể có một kỹ thuật chống tháo gỡ được bảo trợ tương ứng.

- Chương này cho thấy cách hoạt động của bộ dịch ngược và chiến lược tháo theo hướng tuyến tính và dòng chảy khác nhau như thế nào. Chống tháo gỡ khó khăn hơn với một trình phân tách theo hướng dòng chảy nhưng vẫn hoàn toàn khả thi, một khi bạn hiểu rằng trình dịch ngược mã đang đưa ra các giả định nhất định về vị trí mã sẽ thực thi. 

- Nhiều kỹ thuật chống tháo gỡ được sử dụng chống lại định hướng dòng chảy bộ tách rời hoạt động bằng cách tạo các hướng dẫn điều khiển luồng có điều kiện cho mà điều kiện luôn giống nhau trong thời gian chạy nhưng trình tìm kiếm disas không xác định được. 

- Che khuất kiểm soát luồng là cách mà phần mềm độc hại có thể khiến phân tích phần mềm độc hại bỏ qua các phần mã hoặc ẩn mục đích của chức năng bằng cách che khuất mối quan hệ của nó với các chức năng khác và các cuộc gọi hệ thống. 

- Chúng tôi đã xem xét một số cách để thực hiện điều này, từ việc sử dụng lệnh ret đến việc sử dụng bộ xử lý SEH như một bước nhảy có mục đích chung. Mục tiêu của chương này là giúp bạn hiểu mã từ một chiến thuật luật xa gần. 

- Bạn đã học cách thức hoạt động của các loại kỹ thuật này, tại sao chúng hữu ích và cách đánh bại chúng khi bạn gặp chúng trên thực địa. 

- Hơn các kỹ thuật đang chờ được khám phá và phát minh. Với nền tảng vững chắc này, bạn sẽ sẵn sàng hơn để gây chiến trong cuộc chiến chống tháo gỡ chiến trường của tương lai.
