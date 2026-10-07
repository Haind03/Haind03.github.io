---
title: "Bài 6.5: Kotlin trong bytecode, hay vì sao JADX trả bạn Java chứ không phải Kotlin"
date: 2026-10-06 08:48:00 +0700
categories: ["Technique Reverse", "Phần 6 · Java / Kotlin / Android (JADX)"]
tags: [reverse-engineering, android, java]
render_with_liquid: false
---
Mở một app Android đời mới trong JADX, bạn gần như chắc chắn thấy Java. Nhưng chờ đã, ngày nay phần lớn app viết bằng Kotlin cơ mà? Đúng vậy. Vấn đề là Kotlin biên dịch ra đúng cái DEX bytecode mà Java biên dịch ra, nên decompiler đọc bytecode rồi dựng lại thành Java, ngôn ngữ nó biết diễn đạt. Kotlin gốc đã bốc hơi.

Tin tốt: trình biên dịch Kotlin để lại rất nhiều dấu vết đặc trưng. Một khi nhận ra chúng, bạn vừa biết code vốn là Kotlin, vừa đọc được ý đồ nhanh hơn nhiều thay vì bơi trong đống Java máy sinh. Bài này là bộ dấu vết đó.

## Dấu hiệu số một: @Metadata

Mọi class do Kotlin sinh ra đều mang một annotation `@Metadata` ở đầu. Trong JADX bạn sẽ thấy đại loại:

```java
@Metadata(mv = {1, 9, 0}, k = 1, d1 = {"..."}, d2 = {"..."})
public final class LoginManager {
```

Cái `d1`/`d2` là chữ ký Kotlin bị mã hoá (tên hàm, kiểu tham số, nullability, tên tham số gốc). Thấy `@Metadata` là kết luận được ngay: class này vốn là Kotlin. Quan trọng hơn, có tool (như jadx với plugin, hoặc công cụ đọc kotlin-metadata) dùng chính `d2` để phục hồi tên tham số thật, thứ mà Java bytecode thường không giữ.

## Dấu hiệu thứ hai: Intrinsics null-check ở khắp nơi

Kotlin phân biệt kiểu nullable (`String?`) và non-null (`String`). Để giữ lời hứa non-null ở ranh giới với Java, trình biên dịch chèn kiểm tra tự động vào đầu gần như mọi hàm:

```java
public final void login(String user, String pass) {
    Intrinsics.checkNotNullParameter(user, "user");
    Intrinsics.checkNotNullParameter(pass, "pass");
    // ... code thật bắt đầu từ đây
}
```

Những dòng `Intrinsics.checkNotNullParameter` (và `checkNotNull`, `checkNotNullExpressionValue`) không phải logic của tác giả, chúng là rác do compiler sinh. Khi đọc, bỏ qua chúng và nhảy xuống code thật. Thấy `Intrinsics.*` dày đặc cũng là một xác nhận nữa rằng đây là Kotlin.

## Dấu hiệu thứ ba: data class phình ra một đống method

Trong Kotlin bạn viết một dòng:

```kotlin
data class User(val id: Int, val name: String)
```

Nhưng compiler sinh ra cả tá method, và JADX hiện đủ:

```java
public final class User {
    private final int id;
    private final String name;
    public final int component1() { return this.id; }
    public final String component2() { return this.name; }
    public final User copy(int id, String name) { ... }
    public boolean equals(Object other) { ... }   // so sánh từng field
    public int hashCode() { ... }
    public String toString() { return "User(id=" + id + ", name=" + name + ")"; }
}
```

Bộ `component1()`, `component2()`, `copy()`, cùng `equals`/`hashCode`/`toString` so sánh và in theo từng field, là chữ ký không thể nhầm của một data class. Thấy nó là biết ngay đây chỉ là một cục dữ liệu, không phải logic đáng đọc, lướt qua.

## Dấu hiệu thứ tư: companion object và extension function

`companion object` (chỗ chứa thành viên tĩnh của class trong Kotlin) biến thành một inner class tên `Companion` kèm một field static:

```java
public static final User.Companion Companion = new User.Companion(null);
```

Còn extension function (`fun String.clean()`) không có chỗ đứng trong JVM, nên nó thành một static method nhận receiver làm tham số đầu:

```java
// Kotlin: fun String.clean(): String
public static final String clean(String $this$clean) { ... }
```

Tham số tên `$this$...` là dấu hiệu rõ ràng của extension function.

## Khó nhằn nhất: coroutine thành state machine

Đây là chỗ Kotlin làm pseudocode rối nhất. Một `suspend fun` nhìn tuyến tính trong source:

```kotlin
suspend fun fetch(): Data {
    val token = getToken()      // suspend
    val data = download(token)  // suspend
    return data
}
```

Sau biên dịch, nó bị compiler xé thành một **state machine**: toàn bộ thân hàm nhồi vào một hàm nhận thêm tham số `Continuation`, với một biến `label` và một `switch` lớn. Mỗi điểm suspend là một `case`. Trong JADX bạn thấy đại loại:

```java
public final Object fetch(Continuation $completion) {
    // ... khôi phục state từ $continuation.label
    switch (this.label) {
        case 0:
            this.label = 1;
            obj = getToken(this);         // nếu trả COROUTINE_SUSPENDED thì return luôn
            if (obj == suspended) return suspended;
            break;
        case 1:
            // tiếp tục sau getToken, giờ gọi download
            ...
    }
}
```

Cách đọc: đừng cố hiểu cơ chế state machine. Hãy coi `label` như số thứ tự bước, và đọc từng `case` theo đúng thứ tự tăng dần, chính là các dòng tuần tự trong source gốc. Mỗi `case` làm một việc rồi set `label` sang bước kế. Nối chúng lại là ra logic tuyến tính ban đầu. Những chỗ `== suspended` thì return chỉ là cơ chế tạm dừng/tiếp tục, bỏ qua được khi đang truy logic.

## Checklist ghi nhớ
- Kotlin biên dịch ra cùng bytecode như Java, nên JADX hiện Java. Kotlin gốc không còn.
- `@Metadata` ở đầu class: chắc chắn là Kotlin, và chứa chữ ký để phục hồi tên.
- `Intrinsics.checkNotNull*` là rác do compiler chèn, bỏ qua khi đọc.
- data class lộ qua `component1/2...`, `copy`, `equals`/`hashCode`/`toString` theo field.
- extension function thành static method có tham số `$this$...`.
- Coroutine thành state machine với `label` + `switch`: đọc từng `case` theo thứ tự như các bước tuần tự của source.

## Lab tự làm
Thực hành ở [labs/6.5/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/6.5/README.md): mở một app Kotlin trong JADX và tự nhận ra từng pattern ở trên.
