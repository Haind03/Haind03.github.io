---
title: "Lesson 18.3: Symbolic execution, making the computer solve the crackme for you"
date: 2023-09-04 11:00:00 +0700
categories: ["Technique Reverse", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
In [lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/) you wrote constraints by hand and let Z3 solve them. But writing constraints by hand means reading and understanding every comparison in the binary and copying it down without a single wrong sign. With a check function that has a few dozen branches, that's tiring and error-prone. Symbolic execution does the copying for you: it runs the binary with the input as symbolic variables, collects constraints along the way, then calls a solver. You only need to say "find the path to the spot that prints Correct".

## The core idea

In a normal run, the input is a concrete value, for example `s[0] = 0x41`. Symbolic execution replaces it with a symbolic variable (a symbol), call it `c0`. When it meets the instruction `s[0] ^ 0x41`, the machine doesn't compute a number but records the expression `c0 ^ 0x41`. When it meets a branch `if (... == 0)`, it splits into two paths: one path adds the constraint `c0 ^ 0x41 == 0`, the other adds `c0 ^ 0x41 != 0`, and it continues down both.

Like this, each execution path accumulates a set of constraints. When it reaches the goal (the spot that prints "Correct"), we have enough constraints describing "which input leads here", and handing that to an SMT solver gives a concrete input. You don't read the logic, you don't copy constraints, you only point at the goal and at the spots to avoid.

A few terms are worth knowing. Symbolic execution means running with symbolic variables and exploring paths by splitting branches. Concolic (concrete + symbolic) runs with real values while tracking symbols, balancing accuracy and speed, and Triton goes this way. Path explosion is the number of paths growing exponentially with the number of branches, and it's the method's weak spot.

## angr, the main knife

angr is an open Python framework, the most popular for symbolic execution on binaries. The workflow always involves four things. A Project loads the binary, and a State holds the initial state (registers, memory, symbolic input). The simulation manager (`simgr`) is the machinery that pushes states forward, sorting them into found/active/deadended. Finally `explore(find=..., avoid=...)` says the goal to reach and the spots to avoid.

An example solving a crackme that takes a serial through `argv[1]`:

```python
import angr, claripy

proj = angr.Project("./crackme", auto_load_libs=False)

# 8-byte serial, each byte an 8-bit BitVec
chars  = [claripy.BVS(f"c{i}", 8) for i in range(8)]
serial = claripy.Concat(*chars)

state = proj.factory.full_init_state(args=["./crackme", serial])
for c in chars:                       # force printable characters to keep it tidy
    state.solver.add(c >= 0x20, c <= 0x7e)

simgr = proj.factory.simulation_manager(state)
simgr.explore(
    find =lambda s: b"Correct" in s.posix.dumps(1),   # reach the spot that prints Correct
    avoid=lambda s: b"Nope"    in s.posix.dumps(1),    # avoid the spot that prints Nope
)

found = simgr.found[0]
print(found.solver.eval(serial, cast_to=bytes))
```

`find` and `avoid` take the stdout of the simulated process (`posix.dumps(1)` is file descriptor 1). Instead of just hand-picked addresses, we let angr run until stdout contains "Correct". When it finishes, `found.solver.eval` asks the solver "which serial satisfies every constraint on this path" and returns bytes.

Run on this lab's crackme, angr prints the exact serial in a few seconds without us ever reading the `check` function.

## Triton and other options

Triton (Quarkslab) leans toward concolic and integrates DBI (tying to [lesson 17.7](/posts/re-17-7-dynamic-binary-instrumentation-letting-binary-tell/)). It's strong when you want to trace one real execution path and then derive symbols along it, avoiding path explosion. Miasm, maat and manticore are other frameworks, each with its own strength. At the bottom of all of them is still an SMT solver (usually Z3).

## When to use angr, when to go back to hand-written Z3

angr wins when the check logic has many branches but each branch is simple, you're too lazy to read it, and the input space is moderate. It handles the translation from binary to constraints for you.

angr loses (and hand-written Z3 or another approach wins) in a few cases. Path explosion is one: big loops and many nested branches blow up the number of paths, and then you limit the exploration area, or symbolize only the check function (use `call_state` to call the function directly instead of running from main). Heavy crypto or one-way hashes are another: hashing MD5/SHA or multi-round AES produces huge constraints the solver can't handle, and a one-way hash can't in theory be solved by a solver, so you have to brute force or find another route (tying back to [lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/)). The last is syscalls or a complex environment: angr has to be able to simulate whatever the program calls, and without hooks it gets lost.

Pragmatic rule: try angr first because it's cheap, if it hangs or explodes narrow the scope, if that doesn't work read by hand and write Z3.

## Lab

The folder `labs/18.3/`. `src/crackme.c` checks an 8-character serial through a chain of constraints on the bytes. The task is to build it, then let `solve_angr.py` find the serial by itself, without reading the `check` function. Compare the result with the hand-read approach. The solution and the correct serial are in `solution.md` (this serial was actually found by angr, see the writeup).

## Key takeaways
Symbolic execution replaces the input with symbolic variables, splits branches to explore, then uses an SMT solver to find the input that reaches the goal. With angr you set up a Project, a State (symbolic input via `claripy.BVS`), a simulation manager, and `explore(find=, avoid=)`, and `find`/`avoid` can match on stdout so you don't need hand-picked addresses. The weak spots are path explosion and heavy crypto/hashes, and then you narrow the scope or go back to hand-written Z3. Try angr first because it's cheap, and if it fails read by hand.
