// loader.c (lab 4.1): nap shellcode tho tu stdin vao mot trang nho RWX
// (read + write + execute) roi nhay vao de thuc thi. Day la bo khung de
// kiem tra shellcode doc lap, khong can lo hong nao.
//
// Build: xem build.sh. Khong can flag dac biet vi ta xin RWX thang tu mmap.
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(void) {
    unsigned char buf[4096];

    // Doc shellcode tho tu stdin (byte nguyen, khong dien giai).
    ssize_t n = read(0, buf, sizeof(buf));
    if (n <= 0) { perror("read"); return 1; }

    // Xin mot trang nho RWX: doc duoc, ghi duoc, THUC THI duoc.
    // Day la diem mau chot, trang stack/heap binh thuong khong co quyen x (NX).
    void *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mem == MAP_FAILED) { perror("mmap"); return 1; }

    memcpy(mem, buf, n);        // chep shellcode vao vung RWX
    fprintf(stderr, "[loader] %zd byte shellcode @ %p, nhay vao...\n", n, mem);
    fflush(stderr);

    // Ep con tro vung nho thanh con tro ham roi goi: CPU bat dau thuc thi
    // tung byte shellcode nhu lenh may that su.
    ((void (*)(void))mem)();
    return 0;
}
