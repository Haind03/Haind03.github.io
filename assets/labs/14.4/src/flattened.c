// flattened.c: EXACTLY the same logic as original.c but manually
// control flow flattened. The original flow disappears, replaced by
// a while(1) + switch(state) dispatcher. This is how OLLVM -fla
// transforms code, written by hand so you can see the shape clearly.
// Build: gcc -O0 -o flattened flattened.c
#include <stdio.h>
#include <string.h>

int check(const char *s) {
    int state = 0;      // dispatcher state variable
    int len = 0, sum = 0, i = 0, ret = 0;
    while (1) {
        switch (state) {
            case 0:                       // initialization
                len = (int)strlen(s);
                state = 1;
                break;
            case 1:                       // if (len != 8)
                if (len != 8) { ret = 0; state = 99; }
                else state = 2;
                break;
            case 2:                       // if (s[0] != 'R')
                if (s[0] != 'R') { ret = 0; state = 99; }
                else { sum = 0; i = 0; state = 3; }
                break;
            case 3:                       // loop condition
                if (i < len) state = 4;
                else state = 5;
                break;
            case 4:                       // loop body
                sum += (unsigned char)s[i];
                i++;
                state = 3;
                break;
            case 5:                       // if (sum % 7 != 0)
                if (sum % 7 != 0) { ret = 0; state = 99; }
                else { ret = 1; state = 99; }
                break;
            case 99:                      // return block
                return ret;
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <serial>\n", argv[0]);
        return 1;
    }
    puts(check(argv[1]) ? "Correct!" : "Nope.");
    return 0;
}
