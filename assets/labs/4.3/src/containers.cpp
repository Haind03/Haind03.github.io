// containers.cpp
// Lab 4.3: observe the layout of std::string, std::vector and std::map in a binary.
//
// Build (Linux, libstdc++):
//   g++ -O0 -g -std=c++17 containers.cpp -o containers
// Build (Windows, MSVC STL):
//   cl /EHsc /Zi /std:c++17 containers.cpp
// Build (Windows, MinGW):
//   g++ -O0 -g -std=c++17 containers.cpp -o containers.exe
//
// Analysis hints:
//   - Run the program to print sizeof and the field offsets (this is the
//     fastest way to learn the real layout on your toolchain).
//   - Open it in Ghidra/IDA, set a breakpoint after the short and the long
//     string are created, and look at the memory of the std::string object
//     to see SSO.

#include <cstdio>
#include <cstddef>
#include <string>
#include <vector>
#include <map>

// (Wrapping std::string in a struct to get illustrative field offsets would
// only be for observation, not the real internal layout of std::string.)
int main() {
    std::string shortStr = "hi";                 // short: SSO, lives inside the object itself
    std::string longStr  = "this is a long string beyond sso buffer"; // long: heap allocated

    std::vector<int> v = {10, 20, 30, 40};
    std::map<int, const char*> m;
    m[1] = "one";
    m[2] = "two";

    std::printf("sizeof(std::string)      = %zu\n", sizeof(std::string));
    std::printf("sizeof(std::vector<int>) = %zu\n", sizeof(std::vector<int>));
    std::printf("sizeof(std::map<...>)    = %zu\n", sizeof(m));

    std::printf("\n--- std::string short (SSO) ---\n");
    std::printf("addr object  = %p\n", (void*)&shortStr);
    std::printf("data()       = %p  (points INTO the object if SSO)\n", (void*)shortStr.data());
    std::printf("size         = %zu\n", shortStr.size());
    std::printf("capacity     = %zu\n", shortStr.capacity());

    std::printf("\n--- std::string long (heap) ---\n");
    std::printf("addr object  = %p\n", (void*)&longStr);
    std::printf("data()       = %p  (points OUT to the heap, far from the object)\n", (void*)longStr.data());
    std::printf("size         = %zu\n", longStr.size());
    std::printf("capacity     = %zu\n", longStr.capacity());

    std::printf("\n--- std::vector<int> ---\n");
    std::printf("addr object  = %p\n", (void*)&v);
    std::printf("begin (data) = %p\n", (void*)v.data());
    std::printf("size         = %zu\n", v.size());
    std::printf("capacity     = %zu\n", v.capacity());
    // Trong libstdc++, vector = { T* _M_start; T* _M_finish; T* _M_end_of_storage; }
    // size     = _M_finish - _M_start
    // capacity = _M_end_of_storage - _M_start

    return 0;
}
