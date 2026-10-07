// crackme.cpp - a C++ crackme using a virtual function (vtable)
//
// Build Linux/macOS (g++):
//     g++ -O0 -std=c++17 -o crackme crackme.cpp
//   Optimized build to see the difference:
//     g++ -O2 -std=c++17 -o crackme_O2 crackme.cpp
//
// Build Windows (MSVC, in a Developer Command Prompt):
//     cl /EHsc /Od crackme.cpp
//   or MinGW:
//     g++ -O0 -std=c++17 -o crackme.exe crackme.cpp
//
// How to play:
//     ./crackme <password>
//
// Goal: the password is never printed, so the learner has to go through the vtable to find the check function.

#include <cstdio>
#include <cstring>
#include <cstdint>

// Abstract base class. check() is virtual, so calls to it
// go indirectly through the vtable instead of being a direct call.
class Validator {
public:
    virtual bool check(const char* input) const = 0;
    virtual const char* name() const { return "Validator"; }
    virtual ~Validator() {}
};

// The class that does the real checking. Algorithm: for each character,
//   t = ((c XOR 0x5A) + index) & 0xFF
// then compare with the expected array. The password is not stored as plaintext in the binary.
class SerialValidator : public Validator {
    static const int LEN = 12;
    uint8_t expected[LEN] = {
        0x0C, 0x6E, 0x3D, 0x3B, 0x3A, 0x6E, 0x0B, 0x20, 0x30, 0x77, 0x43, 0x3C
    };
public:
    bool check(const char* input) const override {
        if (input == nullptr) return false;
        if ((int)strlen(input) != LEN) return false;
        for (int i = 0; i < LEN; ++i) {
            uint8_t t = (uint8_t)(((input[i] ^ 0x5A) + i) & 0xFF);
            if (t != expected[i]) return false;
        }
        return true;
    }
    const char* name() const override { return "SerialValidator"; }
};

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Usage: %s <password>\n", argv[0]);
        return 1;
    }
    // Base-type pointer, derived-type object: classic polymorphism.
    Validator* v = new SerialValidator();
    bool ok = v->check(argv[1]);   // virtual call, goes through the vtable
    if (ok) {
        printf("Correct! You passed the C++ crackme.\n");
    } else {
        printf("Wrong. Try again.\n");
    }
    delete v;
    return ok ? 0 : 1;
}
