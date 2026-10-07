#include <stdio.h>
#include <string.h>

/* Lab 1.8: sample ELF binary to dissect with readelf/objdump/nm.
 * It calls a few library functions (printf, strlen) so you can see the PLT/GOT,
 * and has one internal function to compare stripped vs non-stripped.
 */

static int secret_len(const char *s) {
    return (int)strlen(s);
}

int main(void) {
    const char *msg = "Hello, ELF!";
    printf("%s\n", msg);
    printf("string length is %d\n", secret_len(msg));
    return 0;
}
