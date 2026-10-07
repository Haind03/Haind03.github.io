// modern.cpp - illustrates exceptions, templates and lambdas from a reverse engineering angle
// Build Linux:   g++ -O0 -g -o modern modern.cpp
//        (add -fno-inline to keep functions separate when reading asm)
// Build MSVC:    cl /EHsc /Zi modern.cpp
// Build MinGW:   g++ -O0 -g -o modern.exe modern.cpp
#include <cstdio>
#include <string>
#include <stdexcept>

// --- Template: each type used generates its own function in the binary ---
template <typename T>
T add_one(T x) {
    return x + static_cast<T>(1);
}

// --- Exception: try/catch is implemented with unwinding + landing pads ---
int safe_div(int a, int b) {
    if (b == 0)
        throw std::runtime_error("divide by zero");
    return a / b;
}

int main(int argc, char** argv) {
    int n = argc;                 // keeps it from being optimized into a constant

    // Template instantiation with two different types
    int    ai = add_one<int>(n);        // generates add_one<int>
    double ad = add_one<double>(n + 0.5); // generates add_one<double>
    printf("add_one int=%d double=%.1f\n", ai, ad);

    // Lambda with a capture: becomes a hidden functor with operator() and a field storing the capture
    int base = n * 10;
    auto make = [base](int k) { return base + k; };  // captures base by value
    printf("lambda=%d\n", make(7));

    // Exception: the first call divides normally, the second throws and is caught
    try {
        printf("div=%d\n", safe_div(100, n));  // n = argc >= 1, normal division
        printf("div=%d\n", safe_div(100, 0));  // divide by 0 -> throw
    } catch (const std::exception& e) {
        printf("caught: %s\n", e.what());
    }
    return 0;
}
