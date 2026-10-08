// Demo 9.1: quan sat chunk, PREV_INUSE, safe-linking cua tcache tren glibc 2.39.
// Khong can pwndbg: tu doc byte header va fd de in ra so that.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static void dump(const char *name, void *p){
    uint64_t prev = *(uint64_t*)((char*)p - 16);
    uint64_t size = *(uint64_t*)((char*)p - 8);
    printf("%-4s mem=%p  prev_size=%#llx  size_field=%#llx  (chunk_size=%#llx PREV_INUSE=%lld)\n",
           name, p, (unsigned long long)prev, (unsigned long long)size,
           (unsigned long long)(size & ~0x7ULL), (long long)(size & 1));
}

int main(void){
    setvbuf(stdout,0,2,0);
    void *a = malloc(0x30), *b = malloc(0x30), *c = malloc(0x30);
    puts("== chunk vua cap phat =="); dump("a",a); dump("b",b); dump("c",c);

    puts("\n== free(a) -> vao tcache[0x40] (bin rong) ==");
    free(a);
    uint64_t fd_a  = *(uint64_t*)a;
    uint64_t key_a = *(uint64_t*)((char*)a+8);
    printf("a.fd (obfuscated) = %#llx\n", (unsigned long long)fd_a);
    printf("a>>12             = %#llx   (== fd vi next=NULL: PROTECT(a,0)=a>>12)\n",
           (unsigned long long)((uint64_t)a>>12));
    printf("a.key             = %#llx   (tcache_key, de phat hien double free)\n",
           (unsigned long long)key_a);

    puts("\n== free(b) -> b thanh dau bin, b.fd tro toi a (bi obfuscate) ==");
    free(b);
    uint64_t fd_b = *(uint64_t*)b;
    uint64_t protect_ba = ((uint64_t)b>>12) ^ (uint64_t)a;
    uint64_t reveal_b   = ((uint64_t)b>>12) ^ fd_b;
    printf("b.fd (stored)     = %#llx\n", (unsigned long long)fd_b);
    printf("PROTECT(b,a)      = %#llx   (= (b>>12) XOR a)\n", (unsigned long long)protect_ba);
    printf("REVEAL(b.fd)      = %#llx   (= (b>>12) XOR b.fd -> dia chi a that)\n",
           (unsigned long long)reveal_b);
    printf("a that            = %p\n", a);
    return 0;
}
