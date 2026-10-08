---
title: "Lesson 18.3: Symbolic execution"
image:
  path: /assets/img/covers/re-18-3-symbolic-execution-making-computer-solve-crackme.webp
  alt: "Lesson 18.3: Symbolic execution"
date: 2023-09-04 11:00:00 +0700
categories: ["Reverse Engineering", "Part 18 · Advanced Topics"]
tags: [reverse-engineering, advanced]
render_with_liquid: false
---
In [lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/) you wrote constraints by hand and let Z3 solve them. That means reading every comparison in the binary and copying it down without a single wrong sign. With a check function that has a few dozen branches, that's tiring and easy to get wrong. Symbolic execution does the copying for you. It runs the binary with the input as symbolic variables, collects constraints along the way, then calls a solver. You only say "find the path to the spot that prints Correct".

## The core idea

In a normal run, the input is a concrete value, for example `s[0] = 0x41`. Symbolic execution replaces it with a symbolic variable (a symbol), call it `c0`. When it meets the instruction `s[0] ^ 0x41`, the machine doesn't compute a number but records the expression `c0 ^ 0x41`. When it meets a branch `if (... == 0)`, it splits into two paths. One path adds the constraint `c0 ^ 0x41 == 0`, the other adds `c0 ^ 0x41 != 0`, and it continues down both.

So each execution path accumulates a set of constraints. When it reaches the goal (the spot that prints "Correct"), the constraints describe which input leads there, and handing them to an SMT solver gives a concrete input. You don't read the logic or copy constraints, you only point at the goal and at the spots to avoid.

A few terms to know. Symbolic execution means running with symbolic variables and exploring paths by splitting branches. Concolic (concrete + symbolic) runs with real values while tracking symbols, balancing accuracy and speed, and Triton goes this way. Path explosion is the number of paths growing exponentially with the number of branches, and it's the method's weak spot.

## angr

angr is an open Python framework, the most popular for symbolic execution on binaries. The workflow always involves four things. A Project loads the binary, and a State holds the initial state (registers, memory, symbolic input). The simulation manager (`simgr`) pushes states forward, sorting them into found/active/deadended. Finally `explore(find=..., avoid=...)` gives the goal to reach and the spots to avoid.

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

`find` and `avoid` take the stdout of the simulated process (`posix.dumps(1)` is file descriptor 1). Instead of hand-picked addresses, we let angr run until stdout contains "Correct". When it finishes, `found.solver.eval` asks the solver which serial satisfies every constraint on this path and returns bytes.

Run on this lab's crackme, angr prints the exact serial in a few seconds without us ever reading the `check` function.

## Triton and other options

Triton (Quarkslab) leans toward concolic and integrates DBI (tying to [lesson 17.7](/posts/re-17-7-dynamic-binary-instrumentation-letting-binary-tell/)). It's good when you want to trace one real execution path and then derive symbols along it, which avoids path explosion. Miasm, maat and manticore are other frameworks, each with its own strengths. Underneath all of them is an SMT solver (usually Z3).

## When to use angr, when to go back to hand-written Z3

angr works well when the check logic has many branches but each branch is simple, you don't want to read it all, and the input space is moderate. It handles the translation from binary to constraints for you.

It struggles in a few cases, where hand-written Z3 or another approach wins. Path explosion is one. Big loops and many nested branches blow up the number of paths, and then you limit the exploration area, or symbolize only the check function (use `call_state` to call the function directly instead of running from main). Heavy crypto or one-way hashes are another. Hashing MD5/SHA or multi-round AES produces huge constraints the solver can't handle, and a one-way hash can't in theory be solved by a solver, so you have to brute force or find another route (tying back to [lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/)). The last is syscalls or a complex environment. Angr has to be able to simulate whatever the program calls, and without hooks it gets lost.

My rule is to try angr first because it's cheap, and if it hangs or explodes, narrow the scope. If that doesn't work, read by hand and write Z3.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 18.3</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/18.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/18.3/solve_angr.py" download><i class="fa-solid fa-download"></i>solve_angr.py</a>
<a class="lab-file" href="/assets/labs/18.3/src/crackme.c" download><i class="fa-solid fa-download"></i>src/crackme.c</a>
</div>
</div>

The goal is to let symbolic execution find the serial by itself, without reading the `check` function by hand. `crackme.c` checks an 8-character serial through a chain of constraints on the bytes. Install angr and build the crackme:

```bash
pip install angr
gcc -O0 -no-pie -fno-stack-protector -o crackme crackme.c
```

Run `./crackme ABCDEFGH` first to see it print `Nope.`. Do NOT open `crackme.c` or decompile it. All you know is that it takes an 8-character serial through `argv[1]` and prints `Correct!` if it is right. Use `solve_angr.py` to have angr find the serial:

```bash
python3 solve_angr.py ./crackme
```

Feed the serial angr found into `./crackme <serial>` and confirm you get `Correct!`. Only now open `crackme.c`, read the `check` function, solve it by hand and compare with angr's result.

Three questions to think about. Why does angr find the serial without you copying a single constraint? If `check` hashed the serial with SHA-256 and compared it to a constant, could angr still solve it, and why? And `find` and `avoid` here match on stdout, so what other way is there to point angr at a target? Try it yourself first.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The correct serial is `AorrnsqT`. I verified it end to end on Linux. I built with `gcc -O0 -no-pie -fno-stack-protector -o crackme crackme.c`, then `python3 solve_angr.py ./crackme` (angr 9.2.213) printed `Serial: AorrnsqT`. Feeding it back, `./crackme AorrnsqT` prints `Correct! Access granted.` (exit 0), while `./crackme WRONGXXX` prints `Nope.` (exit 1). angr found this serial without us reading the `check` function.

Here's what angr did. It loaded the binary, created 8 symbolic bytes `c0..c7`, joined them into `serial`, and passed it through `argv[1]`. It added a soft constraint that each byte is printable (0x20 to 0x7e) for a tidy result. Then `explore(find=..., avoid=...)` pushed all states forward, keeping the states whose stdout contains `Correct` and dropping those containing `Nope`. On the state it found, `solver.eval(serial)` derives bytes satisfying every constraint accumulated along the way.

To compare with solving by hand, open `crackme.c`, where the `check` function applies 8 constraints.

| Byte | Constraint | Result |
|---|---|---|
| s[0] | `s[0] ^ 0x41 == 0` | `0x41` = 'A' |
| s[1] | `s[1] == 0x6F` | `0x6F` = 'o' |
| s[2] | `s[1] + s[2] == 0xE1` | `0xE1 - 0x6F = 0x72` = 'r' |
| s[3] | `s[3] ^ s[0] == 0x33` | `0x41 ^ 0x33 = 0x72` = 'r' |
| s[4] | `s[4] * 2 == 0xDC` | `0x6E` = 'n' |
| s[5] | `s[5] - s[1] == 0x04` | `0x6F + 4 = 0x73` = 's' |
| s[6] | `s[6] ^ 0x5A == 0x2B` | `0x2B ^ 0x5A = 0x71` = 'q' |
| s[7] | `(s[7] + s[6]) & 0xFF == 0xC5` | `0xC5 - 0x71 = 0x54` = 'T' |

Putting them together, `A o r r n s q T` is `AorrnsqT`, which matches angr's result.

On the questions, you don't need to copy constraints because angr executes the binary with symbolic variables and collects the constraints at each branch itself. We only point at the goal (stdout containing "Correct") and what to avoid, and the job of translating logic into constraints belongs to angr, not to us. If `check` hashed with SHA-256 and compared to a constant, angr would nearly give up. A hash function creates enormous constraints and is essentially one-way, so an SMT solver can't invert it in finite time. Then you would have to brute-force the feasible space, or look for some other weakness (which connects to lesson 16.4). As for other ways to point at the goal, use specific addresses, with `find=0x...` (the address of the instruction that prints Correct, or of the return-1 branch) and `avoid=0x...`, taking the addresses from IDA, Ghidra or objdump. Matching on stdout is more convenient when you don't want to look up addresses.

</details>

## Key takeaways
Symbolic execution replaces the input with symbolic variables, splits branches to explore, then uses an SMT solver to find the input that reaches the goal. With angr you set up a Project, a State (symbolic input via `claripy.BVS`), a simulation manager, and `explore(find=, avoid=)`, and `find`/`avoid` can match on stdout so you don't need hand-picked addresses. The weak spots are path explosion and heavy crypto/hashes, and then you narrow the scope or go back to hand-written Z3. Try angr first because it's cheap, and if it fails read by hand.
