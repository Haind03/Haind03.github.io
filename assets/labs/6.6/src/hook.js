/*
 * Lab 6.6: sample Frida script for hooking Java methods.
 * Edit the class/method names to match your target app.
 * Run: frida -U -f <package> -l hook.js
 * Only use on your own app or one you are authorized to test.
 */

Java.perform(function () {
    console.log("[*] Frida attached to the app, starting hooks");

    // ----- Pattern 1: force a root check to return false -----
    try {
        var RootCheck = Java.use("com.example.app.SecurityCheck");
        RootCheck.isRooted.implementation = function () {
            console.log("[*] isRooted() called -> forcing return false");
            return false;
        };
    } catch (e) {
        console.log("[!] SecurityCheck not found, skipping: " + e);
    }

    // ----- Pattern 2: log the arguments and real result of a verification function -----
    try {
        var Checker = Java.use("com.example.app.LicenseChecker");
        Checker.validate.implementation = function (input) {
            console.log("[*] validate() input = " + input);
            var ret = this.validate(input);        // call the original
            console.log("[*] validate() returned = " + ret);
            return ret;                             // keep the behavior, just observe
        };
    } catch (e) {
        console.log("[!] LicenseChecker not found, skipping: " + e);
    }

    // ----- Pattern 3: overloaded method, the signature must be spelled out -----
    // var Util = Java.use("com.example.app.Util");
    // Util.check.overload("java.lang.String", "int").implementation = function (s, n) {
    //     return true;
    // };
});
