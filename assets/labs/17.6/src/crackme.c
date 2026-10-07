// crackme.c - a small crackme that uses strcmp, for practicing the LD_PRELOAD hook
// Build: gcc -O0 -no-pie -o crackme crackme.c
#include <stdio.h>
#include <string.h>

int main(void) {
    char input[64];
    // The correct password is built in memory, so strcmp is not called with an obvious literal
    char secret[] = {'R','3','v','_','P','r','3','l','0','4','d','\0'};

    printf("Enter password: ");
    if (!fgets(input, sizeof(input), stdin)) return 1;
    input[strcspn(input, "\n")] = '\0';

    if (strcmp(input, secret) == 0)
        printf("Correct! Flag: CTF{%s}\n", secret);
    else
        printf("Nope.\n");
    return 0;
}
