// Lab 9.1: observing the traits of a Rust binary
//
// Build (if you have rustc):
//   Debug:   rustc main.rs -o rust_demo_dbg
//   Release: rustc -O main.rs -o rust_demo_rel
//   v0 mangling: rustc -O -C symbol-mangling-version=v0 main.rs -o rust_demo_v0
//
// With cargo:
//   cargo new rust_demo && (copy this content into src/main.rs) && cargo build --release
//
// After building, try:
//   strings rust_demo_rel | grep -i "\.rs"         # the panic string reveals the file name
//   nm rust_demo_dbg | rustfilt | head             # demangle symbols
//   nm rust_demo_v0 | grep '_R' | rustfilt | head  # mangling v0

fn transform(name: &str) -> u32 {
    // iterator chain: the release build inlines and flattens it into a single loop
    name.bytes()
        .enumerate()
        .map(|(i, b)| (b as u32).wrapping_mul(i as u32 + 1))
        .fold(0x1337u32, |acc, x| acc.wrapping_add(x))
}

fn check(name: &str, serial: u32) -> Result<(), String> {
    let expected = transform(name);
    if serial == expected {
        Ok(())
    } else {
        Err(format!("wrong serial for {}", name))
    }
}

fn main() {
    let name = "rustacean";
    let serial = transform(name);
    // unwrap() here creates the panic machinery with a string containing this file's name
    check(name, serial).unwrap();
    println!("serial ok for {} = {}", name, serial);

    // an Option example to observe niche optimization
    let maybe: Option<&str> = Some(name);
    if let Some(n) = maybe {
        println!("has name: {}", n);
    }
}
