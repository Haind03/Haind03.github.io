// shapes.cpp - vtable / inheritance / RTTI lab for Lesson 4.2
//
// Build (Linux, easiest to read):
//   g++ -O0 -g -fno-inline -o shapes shapes.cpp
// Build without RTTI (to see the difference):
//   g++ -O0 -fno-rtti -o shapes_nortti shapes.cpp
// Build MSVC (Developer Command Prompt):
//   cl /EHsc /Od /Zi shapes.cpp
// Build MinGW:
//   g++ -O0 -g -o shapes.exe shapes.cpp
//
// Goal: observe the vtable, the vtable pointer at the start of the object,
// how inheritance shows up in the layout, and RTTI (type_info) in the binary.

#include <cstdio>
#include <cstring>

// Base class with virtual functions -> it gets a vtable.
class Shape {
public:
    int id;                       // plain field, offset right after the vtable pointer
    Shape(int i) : id(i) {}
    virtual double area() = 0;    // pure virtual
    virtual const char* name() { return "Shape"; }
    virtual ~Shape() {}
};

// Derived 1
class Circle : public Shape {
public:
    double radius;
    Circle(int i, double r) : Shape(i), radius(r) {}
    double area() override { return 3.14159265 * radius * radius; }
    const char* name() override { return "Circle"; }
};

// Derived 2
class Rectangle : public Shape {
public:
    double w, h;
    Rectangle(int i, double a, double b) : Shape(i), w(a), h(b) {}
    double area() override { return w * h; }
    const char* name() override { return "Rectangle"; }
};

// Takes a base pointer and calls a virtual -> in asm that is an indirect call through the vtable.
void report(Shape* s) {
    printf("[%d] %s area=%.2f\n", s->id, s->name(), s->area());
}

int main(int argc, char** argv) {
    Circle c(1, 2.0);
    Rectangle r(2, 3.0, 4.0);

    // Array of base pointers, each element a different derived type.
    Shape* shapes[2] = { &c, &r };
    for (int i = 0; i < 2; i++)
        report(shapes[i]);        // same call site, different vtable -> different function

    return 0;
}
