#!/usr/bin/env python3
# Solve the lesson 18.3 crackme with angr (symbolic execution).
#
# Idea: let angr explore the execution paths, find the path that reaches the
# "Correct" string and avoid the path that prints "Nope". angr uses an SMT
# solver on its own to derive a serial satisfying all the constraints, so we
# do not solve it by hand.
#
# Run:  python3 solve_angr.py ./crackme
import sys
import angr
import claripy

LEN = 8

def main(path):
    proj = angr.Project(path, auto_load_libs=False)

    # 8 symbolic bytes for the serial, each byte is an 8-bit BitVec.
    chars = [claripy.BVS(f"c{i}", 8) for i in range(LEN)]
    serial = claripy.Concat(*chars)

    # Pass the serial through argv[1]. angr simulates from main.
    state = proj.factory.full_init_state(args=[path, serial])

    # Soft constraint: each byte is a printable character (not required, but it
    # keeps the result tidy and narrows the search space).
    for c in chars:
        state.solver.add(c >= 0x20, c <= 0x7e)

    simgr = proj.factory.simulation_manager(state)
    simgr.explore(
        find=lambda s: b"Correct" in s.posix.dumps(1),
        avoid=lambda s: b"Nope" in s.posix.dumps(1),
    )

    if not simgr.found:
        print("No path to Correct found")
        return 1

    found = simgr.found[0]
    sol = found.solver.eval(serial, cast_to=bytes)
    print("Serial:", sol.decode("latin1"))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "./crackme"))
