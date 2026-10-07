---
title: "Bài 18.8: AI hỗ trợ reverse engineering, dùng đúng chỗ thì nhanh gấp đôi"
date: 2026-10-06 09:54:00 +0700
categories: ["Technique Reverse", "Phần 18 · Nâng cao"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
Reverse là nghề đọc nhiều: đọc pseudocode, đoán hàm này làm gì, đặt lại tên cho đống `sub_401000` và `v7`. Phần lớn việc đó lặp đi lặp lại và tốn thời gian. Đây chính là chỗ LLM chen vào được: nó đọc một hàm, đoán mục đích, đề xuất tên biến, giải thích một đoạn khó hiểu. Nó không reverse thay bạn, nhưng dọn đường để bạn đi nhanh hơn. Bài này nói về hai cách dùng AI trong RE, và quan trọng hơn là lúc nào đừng tin nó.

## Hai kiểu tích hợp AI

Có hai cách AI chui vào quy trình của bạn, khác nhau về độ sâu.

**Kiểu 1: plugin gọi LLM từ trong decompiler.** Bạn đang ở trong IDA hay Ghidra, chọn một hàm, bấm một phím, plugin gửi pseudocode lên một LLM rồi dán câu trả lời vào. Một chiều: tool hỏi, AI đáp. Đơn giản, đủ dùng cho việc "hàm này làm gì".

**Kiểu 2: MCP server để AI tự điều khiển decompiler.** Đây là bước nhảy. Thay vì bạn copy từng hàm cho AI, một LLM agent (Claude, Cursor) nói chuyện trực tiếp với decompiler qua một MCP server: nó tự lấy danh sách hàm, tự đọc pseudocode, tự đổi tên, tự đặt comment, tự đi theo xref. Bạn ra lệnh bằng tiếng người ("tìm hàm kiểm tra license và giải thích thuật toán"), agent tự mò.

## Kiểu 1: plugin LLM trong decompiler

Các plugin phổ biến, chia theo decompiler:

| Decompiler | Plugin | Làm gì |
|---|---|---|
| IDA | **Gepetto** | Chọn hàm, nhờ LLM giải thích và đề xuất đổi tên biến hàng loạt ngay trong pseudocode |
| Binary Ninja | **aiDAPal / Sidekick** | Trợ lý AI tích hợp, giải thích và gợi ý tên |
| Ghidra | **GhidrAssist / G-3PO** | Gọi LLM giải thích hàm trong decompiler Ghidra |

Cách dùng điển hình với Gepetto: mở một hàm `sub_14000C0A0` rối rắm, bấm phím tắt, Gepetto trả về "hàm này đọc một file config, giải mã bằng RC4 với khoá cứng, rồi parse thành cặp key-value", kèm đề xuất đổi `v3` thành `decrypted_config`, `v7` thành `rc4_key`. Bạn nhìn lướt, thấy hợp lý thì chấp nhận, thấy sai thì bỏ.

Điểm mạnh là nhanh. Một hàm mà bạn phải đọc năm phút, LLM tóm trong năm giây. Điểm yếu nằm ở chữ "đề xuất": nó đoán, và đoán thì có lúc sai.

## Kiểu 2: MCP server cho RE

MCP (Model Context Protocol) là một giao thức chuẩn để LLM agent gọi công cụ bên ngoài. Với RE, người ta viết các MCP server bắc cầu giữa agent và decompiler/debugger:

| MCP server | Nối tới | Agent làm được gì |
|---|---|---|
| **ida-pro-mcp** (mrexodia) | IDA Pro | Lấy decompile, xref, rename, comment, đọc/ghi qua Hex-Rays |
| **GhidraMCP** (LaurieWired) | Ghidra | Liệt kê hàm, decompile, rename, đặt data type |
| **Binary Ninja MCP** | Binary Ninja | Khai thác HLIL/MLIL qua hội thoại |
| **r2mcp** | radare2/rizin | Chạy lệnh r2, phân tích theo hội thoại |
| **frida-mcp** | Frida | Agent tự viết và nạp script Frida, đọc kết quả hook |

Danh sách đầy đủ hơn nằm ở [kho công cụ, mục 23b](/posts/tr-tai-nguyen-cong-cu/#23-ai-hỗ-trợ-re).

### Cấu hình cơ bản

MCP server khai báo trong file cấu hình của client (Claude Desktop, Cline, Cursor). Mẫu chung kiểu:

```json
{
  "mcpServers": {
    "ida": {
      "command": "python",
      "args": ["-m", "ida_pro_mcp.server"]
    }
  }
}
```

Chi tiết từng server khác nhau (có cái chạy như plugin trong IDA mở sẵn port, client nối vào; có cái là một process riêng). Đọc README của đúng server bạn cài. Sau khi nối xong, bạn hỏi agent bằng tiếng tự nhiên và nó tự gọi các hàm MCP (list functions, decompile, rename...) để trả lời.

Trải nghiệm thực tế: mở một binary lạ, bảo agent "khảo sát và đổi tên các hàm chính cho dễ đọc", vài phút sau cả cây hàm `sub_*` đã có tên gợi ý. Bạn rà lại, sửa chỗ sai, và tiết kiệm được cả buổi đặt tên tay.

## Giới hạn: AI đoán, và đoán thì sai được

Đây là phần quan trọng nhất của bài, đọc kỹ.

LLM không chạy code, không chứng minh gì cả. Nó đoán dựa trên pattern đã thấy. Hệ quả:

- **Ảo giác (hallucination).** Nó có thể tự tin nói "đây là AES" trong khi thực ra là một XOR loop. Nó có thể bịa ra một tên hàm nghe hợp lý nhưng sai hoàn toàn.
- **Tên sai lan truyền.** Nếu bạn nhận một cái tên sai mà không kiểm, các hàm gọi nó sẽ được AI đọc theo cái tên sai đó, và sai chồng sai.
- **Không thay được người phân tích.** AI giỏi tóm tắt và đặt tên, dở ở suy luận nhiều bước, logic tinh vi, và những thứ phụ thuộc giá trị runtime mà nó không thấy.

Quy tắc sống còn: **coi output của AI là một giả thuyết, không phải sự thật.** Nó nói "hàm này giải mã RC4"? Tốt, giờ bạn xác nhận bằng cách tìm KSA/PRGA trong code (bài [16.2](/posts/tr-16-2-xor-rc4-base64-custom/)), hoặc chạy động xem đầu vào đầu ra. Giả thuyết đúng thì giữ, sai thì bỏ, nhưng luôn kiểm.

## An toàn khi phân tích malware

MCP cho agent quyền chạy công cụ trên máy bạn. Khi mục tiêu là malware, điều này nguy hiểm:

- **Chạy client và MCP server trong VM cô lập** (xem bài [0.3](/posts/tr-0-3-dung-lab-an-toan/)), đúng cái lab bạn vẫn dùng cho malware.
- **Đừng để agent tự thực thi mẫu.** Một agent "chủ động" có thể quyết định chạy thử binary để xem nó làm gì. Với malware, đó là lây nhiễm. Giới hạn quyền của agent ở đọc và phân tích tĩnh, hoặc giám sát chặt khi cho chạy động trong sandbox.
- **Cẩn thận dữ liệu gửi lên cloud.** Mẫu malware, hay binary nội bộ của công ty, gửi pseudocode lên một LLM cloud là đưa dữ liệu ra ngoài. Với mẫu nhạy cảm, cân nhắc LLM chạy local.

## Khi nào AI đáng dùng, khi nào không

Đáng dùng: đặt tên hàng loạt, tóm tắt nhanh một hàm lạ, giải thích một API không quen, sinh script boilerplate (IDAPython, Frida), gợi ý hướng khi bí. Nó là bàn đạp tốc độ.

Đừng dựa vào nó cho: kết luận cuối về thuật toán crypto, logic bảo mật phải chính xác tuyệt đối, hay bất cứ claim nào bạn sẽ đưa vào báo cáo mà chưa tự kiểm. Những thứ đó vẫn là việc của bạn.

AI làm reverse nhanh hơn, không làm reverse dễ hơn. Bạn vẫn phải hiểu mọi thứ trong các phần trước của series thì mới biết lúc nào AI đang nói nhảm.

## Checklist ghi nhớ
- Hai kiểu: plugin LLM một chiều (Gepetto, GhidrAssist) và MCP server để agent tự điều khiển decompiler (ida-pro-mcp, GhidraMCP, r2mcp, frida-mcp).
- MCP khai báo trong cấu hình client, rồi ra lệnh bằng tiếng tự nhiên.
- Output AI là giả thuyết, luôn kiểm lại bằng tay hoặc chạy động trước khi tin.
- Ảo giác và tên sai lan truyền là rủi ro lớn nhất.
- Phân tích malware: client + MCP trong VM cô lập, không để agent tự chạy mẫu, cẩn thận dữ liệu gửi cloud.
- AI tăng tốc, không thay thế hiểu biết nền tảng.
