// Small .NET crackme for Lesson 5.4 (patching IL / C#).
// Build:
//   dotnet new console -o crackme54, drop this Program.cs in, then:
//   dotnet build -c Release
//   (output: bin/Release/net8.0/crackme54.dll, run it with: dotnet crackme54.dll)
// Or compile quickly if you have .NET Framework:
//   csc Program.cs   ->  Program.exe
//
// Lab goal: do NOT find the password, PATCH the program so it always prints "Correct!".
// The real password is in the code only so the program has some checking logic, it is not the point of the exercise.

using System;

class Program
{
    // The check function returns a bool. This is the patch target.
    static bool CheckPassword(string input)
    {
        // Deliberately trivial logic: compare with a lightly transformed string.
        // The learner doesn't need to break this logic, only to force the function to return true.
        string expected = "dotnet_" + (2 * 21).ToString(); // "dotnet_42"
        return input == expected;
    }

    static void Main()
    {
        Console.Write("Enter password: ");
        string? input = Console.ReadLine();

        if (CheckPassword(input ?? ""))
            Console.WriteLine("Correct!");
        else
            Console.WriteLine("Wrong. Try again.");
    }
}
