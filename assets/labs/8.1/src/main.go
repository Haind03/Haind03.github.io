package main

import "fmt"

//go:noinline
func add(a, b int) int {
	return a + b
}

func main() {
	name := "Reverser"
	fmt.Printf("Hello, %s! 2+3=%d\n", name, add(2, 3))
}

// Build:
//   go build -o hello main.go
// Build stripped (drops the regular symbol table, but pclntab stays):
//   go build -ldflags="-s -w" -o hello_s main.go
// Build with main.add kept un-inlined to see the register ABI:
//   go build -gcflags="-N -l" -o hello2 main.go
