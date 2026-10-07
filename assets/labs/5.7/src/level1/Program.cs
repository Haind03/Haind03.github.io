// Level 1: plain string comparison. The easiest, you only need to read the decompiled C#.
// Build:
//   dotnet new console -o level1, drop this Program.cs in, then dotnet build -c Release
// or compile quickly (with the SDK): dotnet run
using System;

class Program
{
    static bool Check(string input)
    {
        // The password sits right in the IL, decompile it and you see it.
        return input == "dotnet_easy_123";
    }

    static void Main()
    {
        Console.Write("Enter password: ");
        string s = Console.ReadLine();
        Console.WriteLine(Check(s) ? "Correct!" : "Wrong.");
    }
}
