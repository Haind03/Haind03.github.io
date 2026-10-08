---
title: "Lesson 1.2: Primes, Euler's Totient, and the Fermat and Euler Theorems"
image:
  path: /assets/img/covers/crypto-1-2-primes-euler-totient-fermat-euler.webp
  alt: "Primes, Euler's Totient, and the Fermat and Euler Theorems"
date: 2023-02-05 14:25:00 +0700
categories: ["Cryptography", "Crypto · Math Foundations"]
tags: [cryptography, rsa, euler, fermat, number-theory]
render_with_liquid: false
---

This lesson covers the set of theorems that make RSA work. After it you understand why knowing phi(n) is almost the same as breaking RSA, you can reduce a huge exponent to a few digits, and you can build a toy RSA that shows Euler's theorem is what makes decryption correct.

![Primes, Euler's Totient, and the Fermat and Euler Theorems](/assets/img/crypto/crypto-1-2-primes-euler-totient-fermat-euler.svg)
_RSA decryption works because e*d = 1 + k*phi(n), so Euler's theorem collapses m^phi(n) to 1._

Part: 1 (Math Foundations) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 1.1 (modular arithmetic).

**Tools:** Python 3, optionally SymPy or SageMath.

## Goals

After this lesson you understand the role of primes and factorization, and why large primes are central to RSA. You can compute Euler's phi function and know the formulas for phi(p) and phi(p*q). You can state and use Fermat's little theorem and Euler's theorem to reduce exponents. You also see, in a runnable numeric example, that Euler's theorem is what makes RSA decryption correct.

## 1. Theory

### Primes as the base of arithmetic

A prime is an integer greater than 1 that is divisible only by 1 and itself, such as 2, 3, 5, 7, 11, 13, and so on. They are the basic parts of arithmetic in the sense of the fundamental theorem of arithmetic: every integer greater than 1 factors into a product of primes in exactly one way (ignoring order).

For example, `360 = 2^3 * 3^2 * 5`. There is no other way to write 360 as a product of primes.

Why does this matter for RSA? RSA picks two large primes p and q (each around 1024 bits) and uses `n = p * q` as the public modulus. All the security rests on an asymmetry. Multiplying p by q is easy, but given n, finding p and q again (the integer factorization problem) is extremely hard when n is large enough. Nobody knows how to factor a 2048-bit number quickly on ordinary computers. Solving that problem would break RSA.

Testing whether a number is prime (primality testing) is surprisingly easy, much easier than factoring. Tests such as the Fermat test and the Miller-Rabin test run fast and tell you with near certainty whether a number is prime, without factoring it. That is how large primes are generated for keys. The details of these tests come later. For now it is enough to know that generating primes is easy and factoring a product of two primes is hard.

### Euler's phi function

Euler's phi function (the totient), written `phi(n)`, counts how many numbers from 1 to n are coprime to n (gcd equal to 1).

For `phi(10)`, the numbers from 1 to 10 that are coprime to 10 are 1, 3, 7, 9 (all others are divisible by 2 or 5). That is 4 numbers, so `phi(10) = 4`.

A few formulas you must know:

- If p is prime then `phi(p) = p - 1`, because every number from 1 to p-1 is coprime to p. For example `phi(7) = 6`.
- If p and q are two DIFFERENT primes then `phi(p*q) = (p-1)(q-1)`. For example `phi(15) = phi(3)*phi(5) = 2*4 = 8`. Check by listing the numbers coprime to 15: 1, 2, 4, 7, 8, 11, 13, 14, exactly 8 numbers.
- In general, if `n = p1^a1 * ... * pk^ak` then `phi(n) = n * product(1 - 1/pi)` over the primes pi dividing n.

An important property: phi is multiplicative when the two parts are coprime, that is `phi(a*b) = phi(a)*phi(b)` if gcd(a,b) = 1. This is what gives `phi(p*q) = phi(p)*phi(q) = (p-1)(q-1)`. Note the coprime condition: `phi(4) = 2`, not `phi(2)*phi(2) = 1`, because 2 and 2 are not coprime.

Remember one key point for RSA. If you know `n = p*q` but not p and q, then computing `phi(n)` is as hard as factoring n. Conversely, anyone who knows p and q computes phi(n) in one line, and knowing phi(n) is enough to compute the private key. In other words, knowing phi(n) is equivalent to breaking RSA.

### Fermat's little theorem

Fermat's little theorem says that if p is prime and gcd(a, p) = 1 then

```
a^(p-1) ≡ 1 (mod p)
```

For p = 7 and a = 3, `3^6 = 729 = 104*7 + 1`, so `3^6 ≡ 1 (mod 7)`. This is what the theorem says.

An equivalent form, which needs no coprime condition, is `a^p ≡ a (mod p)` for every a.

Two applications you will use constantly:

Reducing a huge exponent. Since `a^(p-1) ≡ 1`, the powers of a repeat with period p-1, so when gcd(a, p) = 1 we have `a^k mod p = a^(k mod (p-1)) mod p`. For example, to compute `3^100 mod 7`, reduce the exponent first: `100 mod 6 = 4`, then `3^4 = 81 = 11*7 + 4 ≡ 4 (mod 7)`. So `3^100 mod 7 = 4`. Note that the exponent reduces modulo p-1, not p. This is exactly the point I promised in Lesson 1.1.

Fast inverse. From `a^(p-1) ≡ 1` it follows that `a * a^(p-2) ≡ 1`, so `a^{-1} ≡ a^(p-2) (mod p)`. For example `3^{-1} mod 7 = 3^5 mod 7 = 243 = 34*7 + 5 ≡ 5 (mod 7)`, which matches the result of Lesson 1.1. This is how to compute an inverse when the modulus is prime, with a single exponentiation.

### Euler's theorem

Euler's theorem generalizes Fermat to any modulus. If gcd(a, n) = 1 then

```
a^phi(n) ≡ 1 (mod n)
```

When n is a prime p, phi(p) = p-1 and we get Fermat back. For n = 10, phi(10) = 4 and a = 3, `3^4 = 81 = 8*10 + 1 ≡ 1 (mod 10)`. Correct.

Like Fermat, Euler lets you reduce the exponent modulo phi(n): `a^k mod n = a^(k mod phi(n)) mod n` when gcd(a, n) = 1.

And this is why RSA works. RSA chooses e and d such that `e * d ≡ 1 (mod phi(n))`, meaning `e*d = 1 + k*phi(n)` for some k. Then decrypting a ciphertext `c = m^e` gives:

```
c^d = (m^e)^d = m^(e*d) = m^(1 + k*phi(n)) = m * (m^phi(n))^k ≡ m * 1^k = m (mod n)
```

So raising to the power e and then d returns exactly the original m. Everything depends on `m^phi(n) ≡ 1`, which is Euler's theorem. (This assumes gcd(m, n) = 1. The other case also holds, thanks to the Chinese remainder theorem in Lesson 1.3. In practice m is almost always coprime to n.)

One point that will save you from a classic mistake: when you reduce exponents in RSA, you reduce modulo `phi(n)`, NOT modulo n. Beginners often mix this up and get completely wrong results.

## 2. Hands-on (demo)

The plain Python below checks everything above, including a toy RSA.

```python
# fermat_euler.py: verify Fermat, Euler and a toy RSA
from math import gcd

def phi(n):
    # Compute phi(n) by factoring (trial division) and then applying the product formula.
    result = n
    m = n
    p = 2
    while p * p <= m:
        if m % p == 0:
            while m % p == 0:
                m //= p
            result -= result // p     # multiply by (1 - 1/p)
        p += 1
    if m > 1:                          # one large prime factor remains
        result -= result // m
    return result

def main():
    # phi for a few numbers
    print("phi(10) =", phi(10), "| phi(7) =", phi(7), "| phi(15) =", phi(15))

    # Fermat's little theorem: a^(p-1) mod p == 1 when gcd(a,p)=1
    for a, p in [(3, 7), (2, 11), (5, 13)]:
        assert pow(a, p - 1, p) == 1
    print("Fermat little: 3^6 mod 7 =", pow(3, 6, 7))

    # Reduce the exponent modulo p-1
    print("3^100 mod 7 =", pow(3, 100, 7), "= 3^(100 mod 6) mod 7 =", pow(3, 100 % 6, 7))

    # Inverse via Fermat: a^(p-2) mod p
    print("3^-1 mod 7 = 3^5 mod 7 =", pow(3, 5, 7))

    # Euler's theorem: a^phi(n) mod n == 1
    assert pow(3, phi(10), 10) == 1
    print("Euler: 3^phi(10) mod 10 =", pow(3, phi(10), 10))

    # Toy RSA
    p, q = 61, 53
    n = p * q                 # 3233
    e = 17
    ph = (p - 1) * (q - 1)    # 3120
    d = pow(e, -1, ph)        # 2753
    m = 65                    # 'A'
    c = pow(m, e, n)          # 2790
    dec = pow(c, d, n)        # must give back 65
    print(f"Toy RSA: n={n} phi={ph} d={d} | c={c} -> decrypts to m={dec}")
    assert dec == m

if __name__ == "__main__":
    main()
```

Output:

```
phi(10) = 4 | phi(7) = 6 | phi(15) = 8
Fermat little: 3^6 mod 7 = 1
3^100 mod 7 = 4 = 3^(100 mod 6) mod 7 = 4
3^-1 mod 7 = 3^5 mod 7 = 5
Euler: 3^phi(10) mod 10 = 1
Toy RSA: n=3233 phi=3120 d=2753 | c=2790 -> decrypts to m=65
```

Reading the output, the phi values match (`phi(15) = 8`). Fermat gives `3^6 ≡ 1 (mod 7)`. The exponent reduction works: `3^100 mod 7` equals `3^4 mod 7 = 4`. The inverse through Fermat gives 5, matching Lesson 1.1. Euler gives `3^phi(10) ≡ 1 (mod 10)`. And the most important line: the toy RSA with `d = 2753` decrypts `c = 2790` back to `m = 65`, the character 'A'. The full encrypt then decrypt round trip being correct is Euler's theorem doing its work.

## 3. Lab

- Task: given `n = 3233`, `e = 17`, and the ciphertext `c = 2790`. Pretend you are only an attacker who knows the public key (n, e) and c. Factor n into two primes p, q, compute phi, derive d, and then recover m. (Because n is small, it can be factored by trial division. That is the lesson, since with a small n RSA is broken.)
- Files: none, the parameters are given right here.
- Hints, step by step:
  - Hint 1: try dividing n by 2, 3, 5, 7, ... until a factor appears. `3233 = 61 * 53`.
  - Hint 2: `phi = (61-1)*(53-1) = 3120`; `d = inverse(17, 3120)`.
  - Hint 3: `m = pow(c, d, n)`, then read `m` as a character if you like.
- Done when: you recover m from (n, e, c) by factoring, and you can say why a large n stops this. (Part 6 digs into many kinds of RSA attacks.)

## 4. Key takeaways

- [ ] `phi(p) = p - 1`; `phi(p*q) = (p-1)(q-1)` for distinct primes p, q.
- [ ] Fermat's little theorem: `a^(p-1) ≡ 1 (mod p)` when gcd(a, p) = 1; as a consequence `a^(p-2)` is the inverse mod p.
- [ ] Euler: `a^phi(n) ≡ 1 (mod n)` when gcd(a, n) = 1; this is why RSA decryption is correct.
- [ ] Reduce exponents modulo phi(n) (or p-1 when the modulus is prime), NOT modulo n.
- [ ] Knowing phi(n) is equivalent to being able to factor n, which means breaking RSA.

## 5. Common pitfalls

- Reducing the exponent mod n instead of mod phi(n). This is completely wrong. The exponent lives in the "phi(n) world", not in n.
- Using Fermat when gcd(a, p) is not 1. The theorem does not apply. For example if `a` is a multiple of p then `a^(p-1) ≡ 0`, not 1.
- Thinking `phi(p*q) = p*q - 1`. Wrong, that is the formula for the phi of a prime, not of a product of two primes.
- Forgetting the gcd(a, n) = 1 condition in Euler's theorem. Without coprimality the formula does not apply.
- Using the multiplicativity of phi when the two parts are not coprime. `phi(a*b) = phi(a)*phi(b)` holds only when gcd(a, b) = 1.

## 6. Further reading

- "An Introduction to Mathematical Cryptography" (Hoffstein, Pipher, Silverman), chapters 1 to 3, on Fermat, Euler and RSA.
- "Handbook of Applied Cryptography", chapter 2 and chapter 8 (public key).
- CryptoHack (cryptohack.org), the Modular Arithmetic and RSA Starter paths.
- SymPy documentation, `totient`, `isprime`, `factorint`, to quickly check the examples.
