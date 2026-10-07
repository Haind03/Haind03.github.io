// Lab 5.5: a small .NET assembly to obfuscate and then strip.
// Build:
//   csc /out:LicenseCheck.exe LicenseCheck.cs         (.NET Framework)
// or create a console project and run: dotnet build
//
// Run: LicenseCheck.exe <key>
// Valid key: REVERSE-2024
//
// Purpose: before obfuscation, everything (function names, strings) is plainly
// visible in ILSpy/dnSpy. After running it through ConfuserEx, the names get
// mangled and the strings get encrypted. Use de4dot to bring it back to a
// readable form.

using System;

class LicenseCheck
{
    static bool CheckKey(string key)
    {
        // The logic is deliberately simple, to keep the focus on obfuscation.
        if (key == null || key.Length != 12)
            return false;
        return key == "REVERSE-2024";
    }

    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: LicenseCheck.exe <key>");
            return 1;
        }

        if (CheckKey(args[0]))
        {
            Console.WriteLine("Valid key");
            return 0;
        }

        Console.WriteLine("Wrong key");
        return 2;
    }
}
