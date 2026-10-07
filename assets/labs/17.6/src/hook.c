// hook.c - LD_PRELOAD library that overrides strcmp to log its arguments
// Build: gcc -shared -fPIC -o hook.so hook.c -ldl
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>

// pointer to the real strcmp in libc
static int (*real_strcmp)(const char *, const char *) = NULL;

int strcmp(const char *a, const char *b) {
    if (!real_strcmp)
        real_strcmp = (int (*)(const char *, const char *))dlsym(RTLD_NEXT, "strcmp");
    fprintf(stderr, "[hook] strcmp(\"%s\", \"%s\")\n", a, b);
    return real_strcmp(a, b);
}
