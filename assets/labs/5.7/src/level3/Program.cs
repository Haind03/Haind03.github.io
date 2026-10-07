// Level 3: the logic before obfuscation. After packing it with ConfuserEx/Eazfuscator,
// names turn into meaningless characters and strings get encrypted. The task is to run
// de4dot and read it again. The password is NOT stored in plaintext: each byte is
// compared after XOR 0x3C.
// Build: dotnet new console -o level3, replace Program.cs, dotnet run
// Obfuscate (if you have it): ConfuserEx on level3.dll, then de4dot -f level3.dll
using System;

class Program
{
    // Encrypted array of the password "Confuse_Me_42" (each byte = character XOR 0x3C).
    static readonly byte[] Enc = {
        127, 83, 82, 90, 73, 79, 89, 99, 113, 89, 99, 8, 14
    };

    static bool Check(string input)
    {
        if (input.Length != Enc.Length) return false;
        for (int i = 0; i < Enc.Length; i++)
            if ((byte)(input[i] ^ 0x3C) != Enc[i]) return false;
        return true;
    }

    static void Main()
    {
        Console.Write("Enter key: ");
        string s = Console.ReadLine();
        Console.WriteLine(Check(s) ? "Unlocked!" : "Locked.");
    }
}
