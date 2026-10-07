---
title: "Lesson 16.4: Rewriting the algorithm in Python, and letting Z3 solve it"
date: 2023-07-14 11:28:00 +0700
categories: ["Technique Reverse", "Part 16 · Crypto and Algorithms"]
tags: [reverse-engineering, crypto]
render_with_liquid: false
---
By now you can read the check algorithm in a binary. The next question: how do you find a valid input? There are two levels. Level one, if the algorithm is simple, rewrite it in Python and then invert it or brute-force it. Level two, the logic is a tangle of constraints between bytes that would drive you mad to solve by hand, so we hand it to Z3, an SMT solver, which finds an input satisfying every condition on its own. This lesson covers both, and the final lab is a crackme solved entirely with Z3 that actually ran.

## Level one: rewrite it in Python

For most crackmes, once you've read the check function you immediately see a transform that can be inverted. A common example: the program takes each input character, transforms it, then compares to a constant array.

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

Rewriting in Python is a foundation skill. But some checks need more than a rewrite.

## When hand-written Python gives up

Consider a check function that doesn't transform each character independently but ties them to each other:

```c
if (f[0] ^ f[1] != 0x41) return 0;
if ((3*f[2] + f[3]) & 0xff != 0x5E) return 0;
if (f[0] + f[1] + ... + f[11] != 988) return 0;
// ... a dozen more interleaved constraints
```

Each condition involves several bytes, and the bytes appear in several conditions. Inverting by hand turns into solving a system of equations, and brute-forcing a 95^12 space is far too large. This is exactly a problem for an SMT solver.

## What Z3 is and why it fits

Z3 (Microsoft Research) is an SMT solver: you describe the problem with variables and constraints, and it finds an assignment of values satisfying all of them, or reports there's no solution. For RE, we model each input byte as a variable, translate each cmp/xor/add/comparison in the binary into a constraint, then call the solver. It returns the flag.

What fits RE is that Z3 has the `BitVec` type that models n-bit integers exactly, with overflow (wrap-around) and bit operations, just like the CPU. `xor`, `+`, `&`, `*` on a BitVec behave exactly as in the binary, even when 8-bit overflow happens.

The skeleton of a Z3 solution always has four parts:

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

A few tips matter here. Use the right width: a byte is `BitVec(name, 8)`, and when accumulating into a large sum, widen with `ZeroExt(24, c)` up to 32-bit to avoid unintended overflow. Match wrap-around too: if the binary computes `(unsigned char)(3*f[i] + f[i+1])`, then in Z3 it's `(3*f[i] + f[i+1]) & 0xff` on an 8-bit BitVec (which already wraps by itself). Finally, check for a unique solution. After you have `m`, add `s.add(Or([c != m[c] for c in f]))` and `check()` again, and if it's `unsat` the solution is unique, so you can be confident it's the real flag.

## Lab: a crackme solved entirely with Z3

The lab at `labs/16.4/` is a crackme that deliberately ties 12 input bytes together: a chain of equations `A[i]*f[i] + f[i+1] == C[i]`, two cross xor constraints, and a sum constraint. No operation compares the input to the flag directly, so you can't pull the flag out of memory or strings. You read the constraint system in the binary, copy it into Z3, and hit solve.

The reference solution `solve_z3.py` builds exactly that system and spits out the flag in a blink. Results actually checked in this environment (gcc 11.4, Python 3.11, z3 5.1.0):

```text
$ python3 solve_z3.py
FLAG: Z3_Rul3s_RE!

$ python3 solve_z3.py | sed -n 's/FLAG: //p' | ./crackme
Enter flag: Correct! Valid flag.
```

Z3 found `Z3_Rul3s_RE!` purely from the constraint constants, and the crackme itself confirms it's valid. I also checked that it's the unique solution, so there's no second flag.

Step-by-step details are in `labs/16.4/solution.md`, including how to match each C line to a Z3 constraint.

## When Z3 is not the answer

Z3 is powerful but not magic. It struggles when the constraints pass through a truly one-way function (a hash like SHA-256), because there's no algebraic structure for the solver to exploit and it will run forever. It also struggles when the state space is too big, with long data-dependent loops, where you should consider combining with symbolic execution (angr, Lesson 18.3) to generate constraints automatically from running the code. Complex float constraints are supported but slow.

The rule: if the check is a system of equations/inequalities on bytes (add, xor, multiply, compare), Z3 wins hands down. If the check is "hash and compare the hash", Z3 is useless and you have to attack another way.

## Key takeaways
For a reversible transform, rewrite in Python and invert; for a small space, brute-force. For a system of constraints tangled across many bytes, hand it to Z3 instead of solving by hand. The Z3 skeleton is BitVec variables, domain constraints, constraints from the binary, then check and model.

Use BitVec with the right width and ZeroExt when accumulating, to match the CPU's wrap-around, and check uniqueness by blocking the old solution and calling check again. Z3 gives up against one-way hashes, so change the attack direction then.
