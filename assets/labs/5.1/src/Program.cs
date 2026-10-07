// Lab 5.1: a small C# program for observing IL and metadata.
// Build (if you have the dotnet SDK):
//   dotnet new console -o hello5x && (copy this file over Program.cs)
//   dotnet build -c Debug
// Or more simply:
//   mkdir hello5x && cd hello5x && dotnet new console
//   replace Program.cs with this file, then: dotnet build
//
// No SDK? No problem, just use any ready-made .NET files such as
//   ILSpy.dll or dnSpy.exe as samples to inspect.

using System;

namespace Hello5x
{
    public class Calculator
    {
        // A simple method for comparing the IL with the C#.
        public static int Add(int a, int b)
        {
            return a + b;
        }

        // Has a local variable and a loop to give richer metadata and IL to look at.
        public int SumTo(int n)
        {
            int total = 0;
            for (int i = 1; i <= n; i++)
            {
                total += i;
            }
            return total;
        }
    }

    internal class Program
    {
        static void Main(string[] args)
        {
            var calc = new Calculator();
            Console.WriteLine("Add(2,3)   = " + Calculator.Add(2, 3));
            Console.WriteLine("SumTo(100) = " + calc.SumTo(100));
        }
    }
}
