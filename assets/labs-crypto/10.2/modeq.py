# modeq.py: giai he phuong trinh modular bang Z3 (vi du nho)
# He: 7x + 3y = 346631 (mod p), 2x + 5y = 274794 (mod p), p = 1000003
from z3 import Int, Solver, sat
p = 1000003
s = Solver()
x, y = Int("x"), Int("y")
s.add(x >= 0, x < p, y >= 0, y < p)
s.add((7*x + 3*y) % p == 346631)
s.add((2*x + 5*y) % p == 274794)
print(s.check())
if s.check() == sat:
    m = s.model()
    print("x =", m[x], " y =", m[y])
