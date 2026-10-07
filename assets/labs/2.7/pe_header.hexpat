// ImHex pattern: parse the start of a PE file
// Open a .exe in ImHex, paste this pattern into the pattern editor, press run.

#pragma endian little

struct DosHeader {
    char magic[2];      // "MZ"
    u8   rest[58];      // skip the middle of the DOS header
    u32  e_lfanew;      // offset to the NT headers
};

struct NtHeaders {
    char signature[4];      // "PE\0\0"
    u16  machine;           // 0x14C = x86, 0x8664 = x64
    u16  numberOfSections;  // number of sections
    u32  timeDateStamp;     // build time (epoch)
};

DosHeader dos @ 0x00;
NtHeaders nt  @ dos.e_lfanew;
