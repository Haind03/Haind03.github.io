// hook.js, sample Frida script for iOS
// Run: frida -U -f com.example.myapp -l hook.js
// Change the class/method names to match YOUR app (or an app you are allowed to test).

if (ObjC.available) {
    console.log('[*] ObjC runtime available');

    // 1) Hook an instance method, log the argument, change the return value
    try {
        var TargetClass = ObjC.classes.LoginViewController;   // rename
        var method = TargetClass['- checkPassword:'];          // change selector
        Interceptor.attach(method.implementation, {
            onEnter: function (args) {
                // args[0] = self, args[1] = selector (SEL), args[2] = first argument
                var arg = new ObjC.Object(args[2]);
                console.log('[+] checkPassword: called with "' + arg.toString() + '"');
            },
            onLeave: function (retval) {
                console.log('[+] original return value: ' + retval);
                retval.replace(ptr(1));   // force a return of true (BOOL YES)
            }
        });
    } catch (e) {
        console.log('[-] could not hook the target method: ' + e);
    }

    // 2) Quickly list the methods of a class to find a target
    // ObjC.classes.LoginViewController.$ownMethods.forEach(function (m) {
    //     console.log('   ' + m);
    // });

    // 3) Example jailbreak detection bypass: force the check to return false
    try {
        var SecurityClass = ObjC.classes.SecurityManager;      // rename
        Interceptor.attach(SecurityClass['- isJailbroken'].implementation, {
            onLeave: function (retval) {
                retval.replace(ptr(0));   // false
                console.log('[+] isJailbroken forced to false');
            }
        });
    } catch (e) {
        // class/method does not exist in this app, ignore
    }
} else {
    console.log('[-] ObjC runtime not available (could be a pure Swift app, or not loaded yet)');
}
