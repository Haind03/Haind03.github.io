// Rust crackme for Lesson 9.3
// Build:
//   rustc -O main.rs -o crackme            (optimized, like the real world)
//   rustc    main.rs -o crackme_debug      (easier to read while learning)
// Run:
//   ./crackme <password>
//
// The password is NOT stored directly in the binary. Each character is transformed:
//   enc[i] = ((pw[i] as u8).wrapping_add(i as u8)) ^ 0x3C
// then compared with the EXPECTED array. To find the password you must reverse this.

use std::process::exit;

// The target array. In the binary it lives in .rodata, and the iterator chain is usually inlined.
const EXPECTED: [u8; 12] = [
    0x6e, 0x4a, 0x49, 0x4b, 0x5f, 0x0a, 0x45, 0x5a, 0x72, 0x42, 0x44, 0x10,
];

fn check(input: &str) -> bool {
    let bytes = input.as_bytes();
    if bytes.len() != EXPECTED.len() {
        return false;
    }
    for (i, &c) in bytes.iter().enumerate() {
        let enc = c.wrapping_add(i as u8) ^ 0x3C;
        if enc != EXPECTED[i] {
            return false;
        }
    }
    true
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 2 {
        println!("Usage: {} <password>", args[0]);
        exit(1);
    }
    if check(&args[1]) {
        println!("Correct! Flag: RE{{{}}}", args[1]);
    } else {
        println!("Nope.");
        exit(1);
    }
}
