---
title: "Lesson 16.4: Rewriting the algorithm in Python and solving with Z3"
image:
  path: /assets/img/covers/re-16-4-rewriting-algorithm-python-letting-z3-solve.webp
  alt: "Lesson 16.4: Rewriting the algorithm in Python and solving with Z3"
date: 2022-08-12 17:43:00 +0700
categories: ["Reverse Engineering", "Part 16 · Crypto and Algorithms"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
By now you can read the check algorithm in a binary. The next question is how to find a valid input. There are two levels. If the algorithm is simple, rewrite it in Python and then invert it or brute-force it. If the logic is a tangle of constraints between bytes that would take forever to solve by hand, give it to Z3, an SMT solver, which finds an input satisfying every condition. This lesson covers both, and the final lab is a crackme solved entirely with Z3 that actually ran.

![Decision flow from check function to valid input](/assets/img/re/re-16-4-rewriting-algorithm-python-letting-z3-solve.svg)
_Invert in Python when the transform is simple, use Z3 when constraints are tangled_

## Level one: rewrite it in Python

For most crackmes, once you've read the check function you can see a transform that can be inverted. A common example is a program that takes each input character, transforms it, then compares to a constant array.

```c
// read from the binary
for (int i = 0; i < 10; i++)
    if (((input[i] ^ 0x5A) + i) != target[i]) return 0;
```

Rewrite and invert it in Python in three lines:

```python
target = [0x12, 0x34, ...]   # taken from the binary
flag = bytes((target[i] - i) ^ 0x5A for i in range(len(target)))
print(flag)
```

A reversible transform (xor, add, subtract, permutation) can always be inverted this way. When it's partly one-way but the space is small (say 4 characters, each printable), brute-force it:

```python
import itertools, string
for cand in itertools.product(string.printable, repeat=4):
    if check(''.join(cand)): print(cand)
```

Rewriting in Python is a basic skill. But some checks need more than a rewrite.

## When hand-written Python gives up

Consider a check function that doesn't transform each character independently but ties them to each other:

```c
if (f[0] ^ f[1] != 0x41) return 0;
if ((3*f[2] + f[3]) & 0xff != 0x5E) return 0;
if (f[0] + f[1] + ... + f[11] != 988) return 0;
// ... a dozen more interleaved constraints
```

Each condition involves several bytes, and the bytes appear in several conditions. Inverting by hand turns into solving a system of equations, and brute-forcing a 95^12 space is far too large. An SMT solver is made for this.

## What Z3 is

Z3 (Microsoft Research) is an SMT solver, so you describe the problem with variables and constraints, and it finds an assignment of values satisfying all of them, or reports there's no solution. For RE, we model each input byte as a variable, translate each cmp/xor/add/comparison in the binary into a constraint, then call the solver. It returns the flag.

Z3 has the `BitVec` type that models n-bit integers exactly, with overflow (wrap-around) and bit operations, just like the CPU. `xor`, `+`, `&`, `*` on a BitVec behave as in the binary, even when 8-bit overflow happens.

A Z3 solution always has four parts:

```python
from z3 import *
f = [BitVec(f'f{i}', 8) for i in range(12)]   # 1. variables: 12 bytes
s = Solver()
s.add([And(c >= 0x20, c <= 0x7e) for c in f]) # 2. domain constraint (printable)
s.add(f[0] ^ f[1] == 0x41)                    # 3. constraints from the binary
# ... add the other constraints
print(s.check())                              # 4. solve: sat / unsat
m = s.model()
print(bytes(m[c].as_long() for c in f))
```

A few tips. Use the right width. A byte is `BitVec(name, 8)`, and when accumulating into a large sum, widen with `ZeroExt(24, c)` up to 32-bit to avoid unintended overflow. Match wrap-around too. If the binary computes `(unsigned char)(3*f[i] + f[i+1])`, then in Z3 it's `(3*f[i] + f[i+1]) & 0xff` on an 8-bit BitVec (which already wraps by itself). Finally, check for a unique solution. After you have `m`, add `s.add(Or([c != m[c] for c in f]))` and `check()` again, and if it's `unsat` the solution is unique, so you can be confident it's the real flag.

## Lab: a crackme solved entirely with Z3

The lab is a crackme that ties 12 input bytes together, using a chain of equations `A[i]*f[i] + f[i+1] == C[i]`, two cross xor constraints, and a sum constraint. Nothing compares the input to the flag directly, so you can't pull the flag out of memory or strings. You read the constraint system in the binary, copy it into Z3, and solve.

Build it and get started:

```bash
pip install z3-solver
gcc -O0 -o crackme crackme.c
```

Run `./crackme`, try a few 12-character strings, and see it only ever reports Correct or Nope without leaking the flag. Open `crackme.c` (or disassemble the binary in Ghidra or IDA if you want the reading practice) and list out every constraint inside `check`, which are the allowed range for each byte (printable, 0x20 to 0x7e), the chain of equations `A[i]*f[i] + f[i+1] == C[i]` (watch the 8-bit wraparound), the two cross xor constraints, and the 32-bit sum constraint. Rebuild that system in a Z3 script, using `BitVec(..., 8)` for each byte and `ZeroExt(24, c)` when you accumulate the sum so it doesn't wrap unintentionally. Solve it, take the flag, and feed it into `./crackme` to confirm. As one more check, block the solution you just found and run `check()` again, and confirm it comes back `unsat`, proving the flag is unique.

Two questions to think about. Why can't you pull the flag out of this binary with `strings`? And if one constraint were instead `sha256(f) == <a fixed hash>`, could Z3 still solve it, and why or why not?

Do it yourself first. The reference solution is `solve_z3.py`, and the full write-up with real run results is below.

<div class="lab-box">
<div class="lab-head"><b>LAB 16.4</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/16.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/16.4/solve_z3.py" download><i class="fa-solid fa-download"></i>solve_z3.py</a>
<a class="lab-file" href="/assets/labs/16.4/src/crackme.c" download><i class="fa-solid fa-download"></i>src/crackme.c</a>
</div>
</div>
<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Reading the constraint system in `check`. The flag is 12 bytes long. `check` doesn't compare the input to the flag, it checks four groups of constraints. First, the range, where each `f[i]` must sit between `0x20` and `0x7e` (a printable character). Second, a chain of equations, for `i` from 0 to 10:

```
(unsigned char)(A[i]*f[i] + f[i+1]) == C[i]
A = [3,5,7,3,5,7,3,5,7,3,5]
C = [65,94,235,107,181,39,12,158,235,59,122]
```

The cast to `unsigned char` means the arithmetic wraps within 8 bits, so in Z3 you need an 8-bit BitVec (which wraps automatically) or an explicit `& 0xff`. Third, two cross xor constraints:

```
f[0] ^ f[11] == 0x7b
f[2] ^ f[5]  == 0x33
```

Fourth, a 32-bit sum constraint:

```
f[0] + f[1] + ... + f[11] == 988
```

Modeling it in Z3. See `solve_z3.py`. Each `f[i]` is a `BitVec(..., 8)`. The chain of equations translates directly, and the sum uses `ZeroExt(24, c)` to widen each byte to 32 bits before adding, avoiding an unwanted wrap.

Results from an actual run. The environment was gcc 11.4.0, Python 3.11.9, z3-solver 5.1.0.

```text
$ gcc -O0 -o crackme crackme.c
$ python3 solve_z3.py
FLAG: Z3_Rul3s_RE!

$ python3 solve_z3.py | sed -n 's/FLAG: //p' | ./crackme
Enter flag: Correct! Valid flag.

$ printf 'Z3_Rul3s_REX\n' | ./crackme
Enter flag: Nope.
```

Z3 found the flag `Z3_Rul3s_RE!` from the constraint constants alone, and the crackme confirms it's valid.

Checking uniqueness. After getting a solution, adding `s.add(Or([c != m[c] for c in f]))` and calling `s.check()` again returns `unsat`. So the flag is unique, there's no second answer. Worth doing every time, since in a CTF multiple solutions usually mean you're missing a constraint or misread one.

Answering the questions. You can't pull the flag out with `strings` because the binary only contains the constraint constants (A, C, 0x7b, 0x33, 988), the flag doesn't exist in the binary in any form, it only exists as the solution to the system. If one constraint were `sha256(f) == <hash>` instead, Z3 would basically give up, because SHA-256 is a one-way function with no algebraic structure for the solver to work with, so it would just run forever. At that point you'd need a different attack, brute force if the space is small enough, a dictionary, or some other weakness, not Z3.

</details>

## When Z3 is not the answer

Z3 has limits. It struggles when the constraints pass through a truly one-way function (a hash like SHA-256), because there's no algebraic structure for the solver to use and it will run forever. It also struggles when the state space is too big, with long data-dependent loops, where you should consider combining with symbolic execution (angr, Lesson 18.3) to generate constraints automatically from running the code. Complex float constraints are supported but slow.

If the check is a system of equations/inequalities on bytes (add, xor, multiply, compare), Z3 does well. If the check is "hash and compare the hash", Z3 is useless and you have to attack another way.

## Key takeaways
For a reversible transform, rewrite in Python and invert; for a small space, brute-force. For a system of constraints tangled across many bytes, hand it to Z3 instead of solving by hand. The structure of a Z3 script is BitVec variables, domain constraints, constraints from the binary, then check and model.

Use BitVec with the right width and ZeroExt when accumulating, to match the CPU's wrap-around, and check uniqueness by blocking the old solution and calling check again. Z3 gives up against one-way hashes, so change the attack direction then.
