package main

import (
	"fmt"
	"sync"
)

func sumSlice(xs []int) int {
	total := 0
	for _, x := range xs {
		total += x
	}
	return total
}

func main() {
	secret := "GopherReverse"
	nums := []int{3, 8, 15, 16, 23, 42}
	fmt.Println("secret length:", len(secret))
	fmt.Println("sum:", sumSlice(nums))

	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			fmt.Println("goroutine", id)
		}(i)
	}
	wg.Wait()
}
