---
title: "Lesson 8.3: Weak Elliptic Curves"
image:
  path: /assets/img/covers/crypto-8-3-weak-elliptic-curves.webp
  alt: "Weak Elliptic Curves"
date: 2023-10-20 07:08:00 +0700
categories: ["Cryptography", "Crypto · Elliptic Curves"]
tags: [cryptography, ecc, invalid-curve, pohlig-hellman]
render_with_liquid: false
---

Lesson 8.1 said ECC is safe when the curve is chosen correctly. This lesson collects the curves that were chosen wrongly, where the ECDLP drops from hopeless to easy. There are four cases. A singular curve (discriminant equal to 0) collapses the ECDLP into a discrete log over an ordinary field. A smooth order (a group order with only small factors) allows Pohlig-Hellman on the curve. An invalid curve attack happens when an implementation does not validate points, so the attacker sends points on a weak curve. And the anomalous curve is introduced. The first two cases and the invalid curve case have pure Python demos that run and recover the secret.

![Four weak elliptic curve cases](/assets/img/crypto/crypto-8-3-weak-elliptic-curves.svg)
_Each case removes a different assumption: a smooth curve, a smooth group order, a validated input point, or an order different from p._

**Prerequisites:** Lesson 8.1 (point addition, scalar multiplication, ECDLP), Lesson 7.2 (Pohlig-Hellman, CRT), Lesson 1.3 (CRT), Lesson 1.4 (finite fields). Remember that the point addition formula does not use `b`.

**Tools:** Python 3 + PyCryptodome + sympy. Install with `pip install pycryptodome sympy`. The solved lab is described in the Lab section below. The anomalous curve case needs SageMath, so this lesson only introduces it.

## Goals

You will understand the singular curve, where a zero discriminant collapses the ECDLP into a discrete log over `Fp*`, which is easy to solve. You will apply Pohlig-Hellman to a curve with smooth group order and recover the scalar. You will understand the invalid curve attack, including why an addition formula that ignores `b` lets foreign points run through, and how the private key is pulled out piece by piece and joined with CRT. And you will know what an anomalous curve is and why it needs specialized tools (Sage).

## Theory

### Singular curve: discriminant equal to 0

The curve `y^2 = x^3 + ax + b` needs `4a^3 + 27b^2 != 0 mod p` to be smooth (non-degenerate). If the discriminant is 0, the right-hand side has a double root, the curve has a singular point (a node or a cusp), and it is no longer a real elliptic curve. What matters is that the group of non-singular points is then isomorphic to an easy group. For a split node it is the multiplicative group `Fp*`. The discrete log in `Fp*` is something we already know how to break (BSGS, Pohlig-Hellman, index calculus, Lesson 7). The ECDLP collapses.

A concrete construction: take a curve with a double root at `x = r`, of the form `y^2 = x^3 - 3r^2 x + 2r^3` (the discriminant is 0 for every `r`). Shifting by `t = x - r` turns it into `y^2 = t^2 (t + 3r)`, the node sits at `t = 0`, and the two tangents have slopes `±alpha` with `alpha^2 = 3r`. When `3r` is a quadratic residue (QR), the node is split, and the map

```
phi(x, y) = (y + alpha*(x - r)) / (y - alpha*(x - r))  mod p
```

is a group isomorphism from the non-singular points to `Fp*`. So `P = k*G` becomes `phi(P) = phi(G)^k`, and the ECDLP turns into an ordinary discrete log.

### Smooth order: Pohlig-Hellman on a curve

Pohlig-Hellman (Lesson 7.2) is not specific to multiplicative groups. It runs on any finite abelian group, including the group of points on an elliptic curve. If the group order `N` factors into small prime powers, project `G` and `P` down to each subgroup of order `q^e`, solve the tiny ECDLP there with baby-step giant-step on points, and join the results with CRT. Standard curves always have a prime or near-prime group order (a small cofactor) precisely to block this attack. A home-made curve, or a curve of unknown origin, may have a smooth order and break at once. This case is the content of the Lab section below.

### Invalid curve attack

This is an implementation flaw, not a flaw in the choice of curve. Recall from Lesson 8.1 that the point addition formula only uses `a`, never `b`. That means if an ECDH service takes your point `P` and computes `d*P` without checking that `P` really lies on the correct curve (the right `b`), you can send a point on a different curve `y^2 = x^3 + ax + b'` (same `a`, different `b'`). The multiplication `d*P` still runs smoothly by the formula, but the result lies on that other curve with `b'`.

The attacker picks `b'` so that the new curve has a point of small order `t`. They send a point `P` of order `t`, and the service returns (or uses) `d*P`, which lies in a subgroup of `t` elements. The attacker tries all `t` possibilities and learns `d mod t`. Repeat with many `b'` for many different `t`, collect enough, then CRT gives the full `d`. This is small subgroup confinement (Lesson 7.2) moved to curves, helped by the addition formula ignoring `b`.

### Anomalous curve (introduction)

A curve over `Fp` is called anomalous when its number of points is exactly `p`, that is `#E(Fp) = p`. For these curves there is Smart's attack. It lifts the problem to the p-adic numbers and uses the formal logarithm map to solve the ECDLP in linear time, which is very fast. The key point is that it does not depend on whether the group order is smooth. It only needs `#E = p`.

This attack needs p-adic arithmetic and tools for curves over rings. SageMath has these built in, while pure Python with pycryptodome and sympy makes them awkward to build. So this lesson only introduces the case and does not include real output for it. When you meet it in a CTF (the sign is that computing `#E` gives exactly `p`), open Sage and use Smart's algorithm, or find an existing `SmartAttack` script. A quick rule is to always compare the group order with `p`. If they are equal, the curve is anomalous and there is nothing more to think about.

## Demo

### Singular curve: the ECDLP collapses to a discrete log in Fp*

```python
# d83_singular.py: singular curve. The ECDLP collapses to a DLP in Fp* (much easier).
p = 10007            # p = 3 mod 4 -> sqrt via exponentiation
assert p % 4 == 3

def legendre(n):
    return pow(n % p, (p - 1) // 2, p)

def sqrt_mod(n):
    return pow(n % p, (p + 1) // 4, p)

# curve singular: y^2 = x^3 - 3r^2 x + 2r^3 (double root at x=r), node at (r,0)
r = 0
for cand in range(1, p):
    if legendre(3 * cand) == 1:    # 3r must be a QR so the node is "split"
        r = cand
        break
a = (-3 * r * r) % p
b = (2 * r ** 3) % p
disc = (4 * a**3 + 27 * b**2) % p
print(f"r={r} a={a} b={b} | discriminant mod p = {disc} (0 -> singular)")

INF = None
def add(P, Q):
    if P is INF: return Q
    if Q is INF: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return INF
    if P == Q:
        m = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def mul(k, P):
    R = INF; Q = P
    while k:
        if k & 1: R = add(R, Q)
        Q = add(Q, Q); k >>= 1
    return R

alpha = sqrt_mod(3 * r)              # slope of the tangent at the node
def phi(P):
    # homomorphism from non-singular points -> Fp* : (y + alpha*(x-r)) / (y - alpha*(x-r))
    x, y = P
    t = (x - r) % p
    num = (y + alpha * t) % p
    den = (y - alpha * t) % p
    return num * pow(den, -1, p) % p

# pick a non-singular point as G
def find_point():
    for x in range(p):
        if x == r:                   # avoid the singular point
            continue
        rhs = (x**3 + a * x + b) % p
        if legendre(rhs) == 1:
            y = sqrt_mod(rhs)
            if (x, y) != (r, 0):
                return (x, y)
    return None

G = find_point()
secret = 1234
P = mul(secret, G)
print("G =", G, "| P = secret*G =", P)

# check the homomorphism: phi(secret*G) == phi(G)^secret mod p
gG, gP = phi(G), phi(P)
print("phi(G) =", gG, "| phi(P) =", gP)
print("phi is a homomorphism?", pow(gG, secret, p) == gP)

# attack: solve the DLP in Fp* (brute force here because p is small) -> get secret
def dlog_fp(g, h):
    cur = 1
    for x in range(p):
        if cur == h:
            return x
        cur = (cur * g) % p
    return None

rec = dlog_fp(gG, gP)
print("ECDLP on singular curve -> DLP in Fp*: secret =", rec, "| correct?", rec == secret)
```

Output:

```
r=1 a=10004 b=2 | discriminant mod p = 0 (0 -> singular)
G = (0, 2641) | P = secret*G = (1069, 6915)
phi(G) = 3941 | phi(P) = 6248
phi is a homomorphism? True
ECDLP on singular curve -> DLP in Fp*: secret = 1234 | correct? True
```

The zero discriminant confirms the curve is singular. The map `phi` turns every point into an element of `Fp*`, and the line `phi is a homomorphism? True` shows that `phi(k*G) = phi(G)^k`. Because of this the ECDLP drops to an ordinary discrete log in `Fp*`, which gives `secret = 1234`. If `p` were such that `p-1` is smooth, replacing the brute-force `dlog_fp` with Pohlig-Hellman would break even a large `p`.

### Invalid curve attack: pulling out the private key piece by piece

```python
# d83_invalid.py: invalid curve attack. EC addition never uses b, so a point on another curve
# still "works", lands in a small subgroup -> leaks d mod small primes -> CRT.
from sympy import factorint
from math import prod

p = 97
a = 3                      # REAL curve: y^2 = x^3 + 3x + 2, order 103 (prime, safe)
b_real = 2
n_real = 103
INF = None

def add(P, Q):             # note: the formula does NOT use b
    if P is INF: return Q
    if Q is INF: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return INF
    if P == Q:
        m = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def mul(k, P):
    R = INF; Q = P
    while k:
        if k & 1: R = add(R, Q)
        Q = add(Q, Q); k >>= 1
    return R

def curve_order(bb):
    cnt = 1
    for x in range(p):
        rhs = (x**3 + a * x + bb) % p
        for y in range(p):
            if (y*y) % p == rhs:
                cnt += 1
    return cnt

def points_on(bb):
    pts = []
    for x in range(p):
        rhs = (x**3 + a * x + bb) % p
        for y in range(p):
            if (y*y) % p == rhs:
                pts.append((x, y))
    return pts

# the victim's secret (scalar d), which the attacker wants to learn
d = 88

# --- attacker looks for weak curves (same p, a; different b) with small subgroups ---
collected = {}   # prime t -> residue d mod t
for bb in range(0, p):
    if bb == b_real:
        continue
    if (4 * a**3 + 27 * bb**2) % p == 0:
        continue
    N = curve_order(bb)
    for t in factorint(N):
        if t in collected or t > 30:
            continue
        # find a point of order t on curve-b': take P, multiply by N/t
        for P in points_on(bb):
            R = mul(N // t, P)
            if R is not INF:
                # the victim computes d*R (formula never checks b) -> lies in the subgroup of order t
                S = mul(d, R)
                # attacker brute d mod t
                cur = INF
                for j in range(t):
                    if cur == S:
                        collected[t] = j
                        break
                    cur = add(cur, R)
                break
    if prod(collected.keys()) > n_real:
        break

print("collected d mod these moduli:", collected)
mods = list(collected.keys())
res = [collected[t] for t in mods]
M = prod(mods)
# CRT
x = 0
for rr, mm in zip(res, mods):
    Mi = M // mm
    x += rr * Mi * pow(Mi, -1, mm)
x %= M
print(f"CRT over {mods} -> d = {x} mod {M}")
print("real d =", d, "| recovered correctly?", x % M == d % M and d < M)
```

Output:

```
collected d mod these moduli: {29: 1, 2: 0, 3: 1, 5: 3}
CRT over [29, 2, 3, 5] -> d = 88 mod 870
real d = 88 | recovered correctly? True
```

The real curve (`b = 2`) has prime order 103 and is safe by itself. But because the service does not check whether the incoming point has the right `b`, the attacker sends points on other curves `b'` that have small subgroups, and collects `d mod 29`, `d mod 2`, `d mod 3` and `d mod 5`. The product `29*2*3*5 = 870 > 88`, so CRT gives back exactly `d = 88`. The defense is simple. Always check that the incoming point lies on the correct curve before multiplying it by the key.

### Smooth order: Pohlig-Hellman on an EC (see the lab)

The Lab section below has the complete smooth order case. The curve is `p = 10007, a = 3, b = 5` with group order `N = 10125 = 3^4 * 5^3` (smooth). Given `G` and `P = secret*G`, find `secret`. `solve.py` is self-contained with pure Python EC math. It projects down to each subgroup of order `q^e`, solves with baby-step giant-step on points, joins with CRT, then decrypts the flag `ECC{...}`. The real transcript is included.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/8.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/8.3/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

- Task: the curve `p = 10007, a = 3, b = 5`, group order `N = 10125`, `G = (1, 3)`, `P = (5324, 8290)`. Find `secret` such that `P = secret*G`, which is used to decrypt the flag.
- Files: `solve.py`, `README.md`, `transcript.txt`.
- Hints in steps: (1) run `factorint(N)` to see if it is smooth; (2) for each `q^e`, set `Gi = (N/q^e)*G` and `Pi = (N/q^e)*P`, then solve the small ECDLP with BSGS on points; (3) join the values `secret mod q^e` with CRT.
- Extension 1: turn the singular demo (section above) into a lab, with a `p` where `p-1` is smooth so that Pohlig-Hellman replaces brute force, and break a singular curve over a large `p`.
- Extension 2: build a fake ECDH service that accepts points without checking `b`, then write your own invalid curve client that collects `d` as in the invalid curve demo, but automates the choice of `b'`.
- Done when you get the flag `ECC{...}` of the smooth order lab and can explain how the singular, smooth and invalid cases differ.

## Key takeaways

- Discriminant `4a^3 + 27b^2 = 0` means a singular curve. The ECDLP collapses to a discrete log in `Fp*` (or an additive group), which is easy to break.
- Smooth group order allows Pohlig-Hellman on the curve, the same as on `Fp*` but with point addition in place of multiplication.
- The point addition formula does not use `b`, which is the basis of the invalid curve attack. Always check that incoming points lie on the correct curve.
- `#E(Fp) = p` is an anomalous curve, broken by Smart's attack (needs Sage, p-adic arithmetic).
- Standard curves (P-256, secp256k1, Curve25519) block all of these. Their order is prime or near-prime, and they are not singular and not anomalous.

## Common pitfalls

- Trusting a curve without checking the discriminant. When a challenge gives odd values of `a, b`, compute `4a^3 + 27b^2 mod p` right away. If it is 0, the curve is singular.
- On a singular curve, confusing a node (split or non-split) with a cusp. A split node is isomorphic to `Fp*`, a non-split node is isomorphic to a subgroup of `Fp(sqrt)*`, and a cusp is isomorphic to the additive group `Fp+` (a trivial discrete log). Choosing the wrong map gives meaningless numbers.
- Skipping confirmation of the group order. Always compute or look up `#E`, then `factorint` it. Both answers (anomalous when it equals `p`, Pohlig-Hellman when it is smooth) are right there.
- Forgetting to validate points in an ECDH implementation. This is a common bug in real code, and it is the reason point validation functions exist. Without the check, the invalid curve attack is wide open.
- Assuming the ECDLP is always equally hard. The difficulty depends on the curve. A wrong curve choice turns a hopeless problem into a few lines of Python.

## Further reading

- "An Elementary Introduction to Elliptic Curves" and notes on singular curves, to understand the isomorphisms to `Fp*` and `Fp+`.
- Smart, "The Discrete Logarithm Problem on Elliptic Curves of Trace One" (1999), the original paper of Smart's attack on anomalous curves.
- Biehl, Meyer, Muller, "Differential Fault Attacks on Elliptic Curve Cryptosystems" (2000), the origin of the invalid curve attack.
- CryptoHack, the "Elliptic Curves" group, with "Smooth Criminal" (smooth order), "Micro Transmissions", and the singular and invalid curve challenges for a full set of practice.
- The `SmartAttack` Sage scripts on GitHub for the anomalous case, to use when you meet `#E = p`.
