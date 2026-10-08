// Lab 7.1: format string leak.
// Loi: printf(buf) truyen input nguoi dung lam format string truc tiep.
// Muc tieu: dung %p do stack, tim offset tham so cua ta (AAAA%N$p),
//           dung %s doc bo nho tuy dia chi, leak canary + libc base + PIE base.
//
// Vong lap doc nhieu luot (nhu mot menu thuc te) de: luot 1 leak PIE base,
// luot 2 dung dia chi vua tinh de %s doc chuoi secret, van trong 1 tien trinh
// (ASLR khong doi giua cac luot).
//
// Bien dich: FORTIFY tat (neu khong glibc doi printf -> __printf_chk va chan %n),
//   nhung GIU stack canary (-fstack-protector-all) de co canary MA LEAK,
//   va GIU PIE (mac dinh Ubuntu 24.04) de co PIE base MA LEAK.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Chuoi bi mat nam trong .data cua binary. Demo doc bo nho tuy dia chi (%s)
// se doc dung chuoi nay khi ta tro toi dia chi cua no (= PIE base + offset).
char secret[] = "FLAG{f0rmat_str1ng_arb1trary_r3ad}";

int main() {
    char buf[128];
    setvbuf(stdout, NULL, 2, 0);   // _IONBF: tat buffer output cho deu
    puts("== fmtstr leak demo (glibc 2.39) ==");
    for (int i = 0; i < 8; i++) {
        printf("echo> ");
        int n = read(0, buf, sizeof(buf) - 1);
        if (n <= 0) break;
        buf[n] = 0;
        printf(buf);     // <--- LOI format string o day
        puts("");
    }
    return 0;
}
