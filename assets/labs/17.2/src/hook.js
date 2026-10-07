// Lab 17.2 - sample Frida hook
//
// Goal: hook the compare function (strcmp/strncmp) of a small program
// to expose the correct string it compares your input against, then force the check to pass.
//
// Run:
//   frida -l hook.js -f ./target            (spawn)
//   frida -l hook.js <process-name>        (attach)
//
// Linux uses libc, Windows uses msvcrt/ucrtbase. Change the module name to match the platform.

function hookStrcmp(moduleName) {
    const p = Module.findExportByName(moduleName, "strcmp");
    if (p === null) {
        console.log("[!] strcmp not found in " + moduleName);
        return;
    }
    Interceptor.attach(p, {
        onEnter(args) {
            // strcmp(const char *a, const char *b)
            this.a = args[0].readCString();
            this.b = args[1].readCString();
            console.log("[strcmp] '" + this.a + "'  vs  '" + this.b + "'");
            // One of the two is usually your input, the other is the answer.
        },
        onLeave(retval) {
            // strcmp returns 0 when the two strings are equal.
            // Uncomment the line below to force every comparison to "match":
            // retval.replace(0);
        }
    });
}

// Pick the module depending on the platform:
//   Linux:   "libc.so.6"
//   Windows: "ucrtbase.dll" or "msvcrt.dll"
hookStrcmp(Process.platform === "windows" ? "ucrtbase.dll" : "libc.so.6");

console.log("[*] hook installed. Type input into the program to see the comparison.");
