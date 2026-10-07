// crackme.go - Go crackme for Lesson 8.4
//
// Build:
//   go build -o crackme crackme.go                  (full binary, keeps pclntab)
//   go build -ldflags "-s -w" -o crackme_strip crackme.go   (stripped try)
//   GOOS=windows go build -o crackme.exe crackme.go (Windows build)
//
// Run:  ./crackme <password>
package main

import (
	"fmt"
	"os"
)

// checkKey transforms each character and then compares with a constant array.
// The password is not stored as plaintext in the binary.
func checkKey(input string) bool {
	want := []byte{0x50, 0x79, 0x56, 0x68, 0x7a, 0x79, 0x82, 0x61, 0x7a, 0x2e, 0x2d}
	if len(input) != len(want) {
		return false
	}
	for i := 0; i < len(input); i++ {
		// each character: XOR 0x17 then add the index
		if (input[i]^0x17)+byte(i) != want[i] {
			return false
		}
	}
	return true
}

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Usage: crackme <password>")
		return
	}
	if checkKey(os.Args[1]) {
		fmt.Println("Correct! Flag: GO{" + os.Args[1] + "}")
	} else {
		fmt.Println("Wrong password.")
	}
}
