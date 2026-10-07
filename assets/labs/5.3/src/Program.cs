using System;

// Small .NET crackme for Lesson 5.3: practice debugging with dnSpy.
// Learning goals: set a breakpoint at the comparison, read variables in Locals,
// and try editing the condition variable at run time to pass the check without knowing the password.
//
// Build (needs the dotnet SDK):
//   dotnet new console -o crackme53 && replace Program.cs with this file
//   cd crackme53 && dotnet build -c Debug
//   run: dotnet run    or    bin/Debug/netX/crackme53(.exe)
// Tip: build in Debug configuration so dnSpy maps lines more easily.

class Program
{
    // The correct serial is computed from the username, not stored as a plain string in the code.
    static string MakeSerial(string user)
    {
        int acc = 0x1337;
        foreach (char c in user)
            acc = (acc * 31 + c) & 0xFFFFF;
        return acc.ToString("X5"); // 5 uppercase hex digits
    }

    static bool CheckSerial(string user, string serial)
    {
        string expected = MakeSerial(user);
        bool isValid = string.Equals(serial, expected, StringComparison.Ordinal);
        return isValid;
    }

    static void Main()
    {
        Console.Write("Username: ");
        string user = Console.ReadLine() ?? "";
        Console.Write("Serial:   ");
        string serial = Console.ReadLine() ?? "";

        if (CheckSerial(user, serial))
            Console.WriteLine("Correct! Welcome, " + user);
        else
            Console.WriteLine("Wrong serial.");
    }
}
