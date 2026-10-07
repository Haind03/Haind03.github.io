// Lab 4.1: name mangling and the this pointer
//
// Build (Linux, GCC):
//   g++ -O0 -g counter.cpp -o counter
// Build (Windows, MinGW):
//   g++ -O0 counter.cpp -o counter.exe
// Build (Windows, MSVC Developer Prompt):
//   cl /EHsc /Od counter.cpp
//
// View the mangled symbols (Linux):
//   nm counter | grep -i counter
//   nm counter | grep -i counter | c++filt
// View the disassembly of main (Linux):
//   objdump -d -M intel counter | less   (look for <main>)

#include <cstdio>

class Counter {
    int value;
public:
    Counter(int start) : value(start) {}
    void add(int n)        { value += n; }          // overload 1
    void add(int n, int m) { value += n + m; }      // overload 2
    int  get() const       { return value; }
};

int main() {
    Counter c(10);
    c.add(5);        // this + 1 argument
    c.add(1, 2);     // this + 2 arguments
    printf("%d\n", c.get());
    return 0;
}
