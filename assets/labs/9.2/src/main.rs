// Lab 9.2: observe Rust's String, Vec, iterators and trait objects in a binary.
//
// Build (needs rustc, installed via rustup):
//   rustc -O main.rs -o rust_demo            # optimized build, iterators heavily inlined
//   rustc main.rs -o rust_demo_debug         # unoptimized build, easier to read
// On Windows use the matching MSVC or GNU toolchain.
//
// After building, open it in Ghidra or IDA and look for the patterns described in the lesson.

trait Greeter {
    fn greet(&self) -> String;
}

struct Vietnamese;
struct English;

impl Greeter for Vietnamese {
    fn greet(&self) -> String {
        String::from("Xin chao")
    }
}

impl Greeter for English {
    fn greet(&self) -> String {
        String::from("Hello")
    }
}

fn sum_even_doubled(data: &[u32]) -> u32 {
    // Iterator chain: the optimized build inlines all of it into one flat loop.
    data.iter()
        .filter(|x| *x % 2 == 0)
        .map(|x| x * 2)
        .sum()
}

fn main() {
    // String and Vec
    let name: String = String::from("ReverseEngineer");
    let numbers: Vec<u32> = vec![1, 2, 3, 4, 5, 6, 7, 8];

    println!("Name: {}, length: {}", name, name.len());

    let total = sum_even_doubled(&numbers);
    println!("Sum of doubled evens: {}", total);

    // Trait object: fat pointer (data + vtable), dynamic dispatch
    let greeters: Vec<Box<dyn Greeter>> = vec![Box::new(Vietnamese), Box::new(English)];
    for g in greeters.iter() {
        println!("{}", g.greet());
    }
}
