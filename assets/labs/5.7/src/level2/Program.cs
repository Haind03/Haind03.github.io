// Level 2: a serial from an algorithm that depends on the username (no plaintext).
// Algorithm: djb2 hash of the username (uint32, seed 0x1505, multiply by 33),
// the correct serial = the hash value as 8 uppercase hex digits (X8).
// Build: dotnet new console -o level2, replace Program.cs, dotnet run
using System;

class Program
{
    static string Expected(string user)
    {
        uint acc = 0x1505;
        foreach (char c in user)
            acc = (acc * 33u) + (byte)c;   // uint32 overflow is intentional
        return acc.ToString("X8");
    }

    static void Main()
    {
        Console.Write("Username: ");
        string u = Console.ReadLine();
        Console.Write("Serial:   ");
        string s = Console.ReadLine();
        Console.WriteLine(s == Expected(u) ? "Valid!" : "Invalid.");
    }
}
