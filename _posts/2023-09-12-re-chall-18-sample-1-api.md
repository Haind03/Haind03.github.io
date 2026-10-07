---
title: "Chall 18 - Sample 1: các Windows API gặp trong mẫu"
date: 2023-09-12 18:44:00 +0700
categories: ["Technique Reverse", "Ghi chép 2023"]
tags: [reverse-engineering, malware, windows-api]
render_with_liquid: false
---
```
SHFOLDERAPI SHGetFolderPathW(
  [in]  HWND   hwnd,
  [in]  int    csidl,
  [in]  HANDLE hToken,
  [in]  DWORD  dwFlags,
  [out] LPWSTR pszPath
);

Giá trị trả về
Kiểu: HRESULT

Nếu hàm này thành công, nó trả về S_OK. Nếu không, nó trả về mã lỗi HRESULT.


Ví dụ mã sau đây sử dụng SHGetFolderPath để tìm hoặc tạo một thư mục và sau đó tạo một tệp trong đó.

TCHAR szPath[MAX_PATH];

if(SUCCEEDED(SHGetFolderPath(NULL, 
                            CSIDL_PERSONAL|CSIDL_FLAG_CREATE, 
                             NULL, 
                             0, 
                             szPath))) 
{
    PathAppend(szPath, TEXT("New Doc.txt"));
    HANDLE hFile = CreateFile(szPath, ...);
}
```
# CreateDirectoryW 

```
BOOL CreateDirectoryW(
  [in]           LPCWSTR               lpPathName,
  [in, optional] LPSECURITY_ATTRIBUTES lpSecurityAttributes
);

Tạo một thư mục mới. Nếu hệ thống tệp cơ bản hỗ trợ bảo mật trên tệp và thư mục, hàm áp dụng một mô tả bảo mật được chỉ định cho thư mục mới.

```

# SetFileAttributesW 
```
BOOL SetFileAttributesW(
  [in] LPCWSTR lpFileName,
  [in] DWORD   dwFileAttributes
);
Đặt các thuộc tính cho tệp hoặc thư mục.

```

# GetModuleFileNameW
```
DWORD GetModuleFileNameW(
  [in, optional] HMODULE hModule,
  [out]          LPWSTR  lpFilename,
  [in]           DWORD   nSize
);
Truy xuất đường dẫn đủ điều kiện cho tệp có chứa mô-đun được chỉ định. Mô-đun phải được tải bởi quy trình hiện tại.

```
# CopyFileExW

```
BOOL CopyFileExW(
  [in]           LPCWSTR            lpExistingFileName,
  [in]           LPCWSTR            lpNewFileName,
  [in, optional] LPPROGRESS_ROUTINE lpProgressRoutine,
  [in, optional] LPVOID             lpData,
  [in, optional] LPBOOL             pbCancel,
  [in]           DWORD              dwCopyFlags
);

Sao chép một tệp hiện có sang một tệp mới, thông báo cho ứng dụng về tiến trình của nó thông qua gọi lại chức năng.

```

# WideCharToMultiByte 
```
int WideCharToMultiByte(
  [in]            UINT                               CodePage,
  [in]            DWORD                              dwFlags,
  [in]            _In_NLS_string_(cchWideChar)LPCWCH lpWideCharStr,
  [in]            int                                cchWideChar,
  [out, optional] LPSTR                              lpMultiByteStr,
  [in]            int                                cbMultiByte,
  [in, optional]  LPCCH                              lpDefaultChar,
  [out, optional] LPBOOL                             lpUsedDefaultChar
);

Ánh xạ chuỗi UTF-16 (ký tự rộng) thành chuỗi ký tự mới. Chuỗi ký tự mới không nhất thiết phải từ một bộ ký tự nhiều byte.

```
# FindResourceW 

```
HRSRC FindResourceW(
  [in, optional] HMODULE hModule,
  [in]           LPCWSTR lpName,
  [in]           LPCWSTR lpType
);

Xác định vị trí của tài nguyên với loại và tên được chỉ định trong mô-đun được chỉ định.
```

# LoadResource
```
HGLOBAL LoadResource(
  [in, optional] HMODULE hModule,
  [in]           HRSRC   hResInfo
);
Truy xuất một xử lý có thể được sử dụng để lấy một con trỏ đến byte đầu tiên của tài nguyên được chỉ định trong bộ nhớ.
```

# LockResource 
```
LPVOID LockResource(
  [in] HGLOBAL hResData
);

Truy xuất một con trỏ đến tài nguyên được chỉ định trong bộ nhớ.
```

# SizeofResource 

```
DWORD SizeofResource(
  [in, optional] HMODULE hModule,
  [in]           HRSRC   hResInfo
);

Truy xuất kích thước, tính bằng byte, của tài nguyên được chỉ định.
```

# CreateFileW 
```
HANDLE CreateFileW(
  [in]           LPCWSTR               lpFileName,
  [in]           DWORD                 dwDesiredAccess,
  [in]           DWORD                 dwShareMode,
  [in, optional] LPSECURITY_ATTRIBUTES lpSecurityAttributes,
  [in]           DWORD                 dwCreationDisposition,
  [in]           DWORD                 dwFlagsAndAttributes,
  [in, optional] HANDLE                hTemplateFile
);

Tạo hoặc mở tệp hoặc thiết bị I/O. Các thiết bị I/O được sử dụng phổ biến nhất như sau: file, file luồng, thư mục, đĩa vật lý, âm lượng, bộ đệm bảng điều khiển, ổ băng, tài nguyên truyền thông, khe cắm thư và ống. Hàm trả về một tay cầm có thể được sử dụng để truy cập tệp hoặc thiết bị cho các loại khác nhau I/O tùy thuộc vào tệp hoặc thiết bị cũng như cờ và thuộc tính được chỉ định.

Để thực hiện thao tác này như một hoạt động được giao dịch, dẫn đến một tay cầm có thể được sử dụng để giao dịch I/O, sử dụng hàm CreateFileTransacted.
```

# RegOpenKeyExA 
```
LSTATUS RegOpenKeyExA(
  [in]           HKEY   hKey,
  [in, optional] LPCSTR lpSubKey,
  [in]           DWORD  ulOptions,
  [in]           REGSAM samDesired,
  [out]          PHKEY  phkResult
);

Mở khoá đăng ký được chỉ định. Lưu ý rằng tên khóa không phân biệt chữ hoa chữ thường.

Để thực hiện các thao tác đăng ký đã giao dịch trên một khóa, hãy gọi hàm RegOpenKeyTransacted.
```

# RegQueryValueExA 
```
LSTATUS RegQueryValueExA(
  [in]                HKEY    hKey,
  [in, optional]      LPCSTR  lpValueName,
                      LPDWORD lpReserved,
  [out, optional]     LPDWORD lpType,
  [out, optional]     LPBYTE  lpData,
  [in, out, optional] LPDWORD lpcbData
);

Truy xuất loại và dữ liệu cho tên giá trị được chỉ định liên kết với khoá đăng ký mở.
```
# CreateThread 
```
HANDLE CreateThread(
  [in, optional]  LPSECURITY_ATTRIBUTES   lpThreadAttributes,
  [in]            SIZE_T                  dwStackSize,
  [in]            LPTHREAD_START_ROUTINE  lpStartAddress,
  [in, optional]  __drv_aliasesMem LPVOID lpParameter,
  [in]            DWORD                   dwCreationFlags,
  [out, optional] LPDWORD                 lpThreadId
);

Tạo một luồng để thực thi trong không gian địa chỉ ảo của quá trình gọi.

Để tạo một luồng chạy trong không gian địa chỉ ảo của một quá trình khác, hãy sử dụng hàm CreateRemoteThread.
```

# GdiplusStartup 

```
Status GdiplusStartup(
  ULONG_PTR                 *token,
  const GdiplusStartupInput *input,
  GdiplusStartupOutput      *output
);

Chức năng GdiplusStartup khởi tạo Windows GDI+. Gọi GdiplusStartup trước khi thực hiện bất kỳ cuộc gọi GDI + nào khác và gọi GdiplusShutdown khi bạn đã sử dụng xong GDI +.
```
