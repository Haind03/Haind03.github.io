---
title: "Lesson 1.4: Groups, Rings and Finite Fields"
image:
  path: /assets/img/covers/crypto-1-4-groups-rings-finite-fields.webp
  alt: "Groups, Rings and Finite Fields"
date: 2023-02-22 17:08:00 +0700
categories: ["Cryptography", "Crypto · Math Foundations"]
tags: [cryptography, finite-fields, groups, aes]
render_with_liquid: false
---

This lesson gives you the algebra needed to talk about Diffie-Hellman, ECC and AES without treating them as black boxes. After it you know what "element", "order" and "generator" mean, you can tell GF(p) from GF(2^n), and you know why AES lives in GF(2^8).

![Group, ring and field, and the two finite field families](/assets/img/crypto/crypto-1-4-groups-rings-finite-fields.svg)
_A field adds multiplicative inverses on top of a ring, and the finite fields come as GF(p) and GF(2^n)._

Part: 1 (Math Foundations) | Time: about 40 minutes | Difficulty: hard

**Prerequisites:** Lesson 1.1 (modular arithmetic), Lesson 1.2 (primes, Euler).

**Tools:** Python 3, SageMath recommended (`GF`).

## Goals

By the end of this lesson you can tell a group, a ring and a field apart and know when Z_n is a field. You understand the order of an element and generators, and how they relate to Fermat and Euler. You can distinguish GF(p) from GF(2^n) and do arithmetic in each. You can multiply in GF(2^8), which is enough to understand AES.

## 1. Theory

Crypto uses the words "element", "order", "generator" and "field" constantly. If they stay unclear, DH, ECC and AES stay opaque. This lesson covers just those concepts, enough to use, without going deep into abstract algebra. As usual, concrete examples come before definitions.

### Group

Take the set `Z_7* = {1, 2, 3, 4, 5, 6}` with multiplication modulo 7. Try a few products: 3*5 = 15 ≡ 1, 2*4 = 8 ≡ 1, 6*6 = 36 ≡ 1. Multiplying two elements gives an element of the set (closure), the element 1 acts as the identity (multiplying by 1 changes nothing), and each element has a partner that multiplies it to 1 (its inverse). A structure like this is called a group.

A group is a set with one operation that satisfies four rules: closure (the operation on two elements of the set stays in the set), associativity, an identity element, and an inverse for every element. If the operation is also commutative, the group is abelian. `(Z_5, +)` is an abelian group with identity 0, and `(Z_7*, *)` is an abelian group with identity 1.

The order of a group is its number of elements. `|Z_7*| = 6`.

### Order of an element

The order of an element a is the smallest positive exponent k such that `a^k = identity`. In Z_7* the powers of 3 are

```
3^1=3, 3^2=2, 3^3=6, 3^4=4, 3^5=5, 3^6=1
```

The powers only return to 1 at exponent 6, so the order of 3 is 6. The powers of 2 are:

```
2^1=2, 2^2=4, 2^3=1
```

The order of 2 is 3.

Note that both element orders (6 and 3) divide the group order (6). This is not a coincidence. It is Lagrange's theorem, which says the order of every element divides the order of the group. A direct consequence is that raising any element to the group order gives the identity, so `a^|G| = 1`. For `Z_p*`, `|G| = p-1`, and we recover Fermat's little theorem from Lesson 1.2. Fermat and Euler are Lagrange's theorem applied to the multiplicative group.

### Generator

The element 3 above has a special property. Its powers `3, 2, 6, 4, 5, 1` sweep through all of Z_7*. Such an element is called a generator or primitive root. Its order equals the group order, so its powers fill the whole group. The element 2, by contrast, only generates `{1, 2, 4}`, a subgroup of size 3, so it is not a generator.

An important fact is that the multiplicative group of a finite field is always cyclic, so a generator always exists. For Z_p*, the number of generators is exactly `phi(p-1)`.

Why does crypto care? Diffie-Hellman works inside a group and needs a generator of large order (ideally a large prime order). If an element of small order is used by mistake, or the group has many small subgroups, an attacker splits the discrete log problem into small pieces in each subgroup and solves it much more easily. That is Pohlig-Hellman (named here only, Part 7 covers it). Generator and order are keywords that keep coming back.

### Ring

What if we give the group a second operation? Take `Z_n` with both addition and multiplication. Addition forms an abelian group, and multiplication is associative and distributes over addition, but not every nonzero element is required to have a multiplicative inverse. A structure with two operations like this is called a ring.

`Z_6` is a ring. It has an oddity: `2 * 3 = 6 ≡ 0 (mod 6)`, so two nonzero elements multiply to 0. They are called zero divisors. This is why 2 and 3 in Z_6 have no multiplicative inverse. A ring allows this.

### Field

A field is a commutative ring in which every nonzero element has a multiplicative inverse. In a field you can add, subtract, multiply and divide freely (dividing by nonzero elements).

Z_p with p prime is a field, because when p is prime every nonzero a is coprime to p and so has an inverse (Lesson 1.1). This field is written `GF(p)` or F_p (GF stands for Galois Field). Z_6 is NOT a field, because 2 has no inverse. The rule is that `Z_n` is a field if and only if n is prime.

A basic result says a finite field exists if and only if its number of elements is `q = p^n`, a power of a prime. For each such q the field is unique up to isomorphism. You need two families.

### GF(p)

`GF(p)` is `Z_p`, arithmetic modulo a prime. This is the home of Diffie-Hellman and the arithmetic part of RSA. For example `GF(7)` is `{0,1,2,3,4,5,6}` with addition and multiplication mod 7. Nothing new here.

### GF(2^n)

This family is less familiar, but AES runs on it, so you need to know it. An element of `GF(2^n)` is not a number. It is a polynomial of degree less than n with coefficients in GF(2) (coefficients are bits 0 or 1). An element of GF(2^8) is a polynomial of degree at most 7, written compactly as 8 bits, which is one byte. For example the byte `0x57 = 0b01010111` is the polynomial `x^6 + x^4 + x^2 + x + 1`.

Arithmetic in GF(2^n):

- Addition is XOR. Coefficients in GF(2) add mod 2, and addition mod 2 is bitwise XOR. There is no carry. For example `0x57 + 0x13 = 0x44` (it is just `0x57 XOR 0x13`). Subtraction is also XOR, because in GF(2) addition and subtraction are the same.
- Multiplication is polynomial multiplication followed by the remainder modulo an irreducible polynomial (a polynomial that cannot be factored into two polynomials of lower degree, playing the role of a prime). This irreducible polynomial keeps the result within n bits and makes the structure a field. AES uses the irreducible polynomial `x^8 + x^4 + x^3 + x + 1`, which is `0x11B` in numeric form.

A small example in `GF(2^3)` with irreducible polynomial `x^3 + x + 1`. Elements are 3 bits. Multiply `(x+1) * x`:

```
(x + 1) * x = x^2 + x        (degree 2, still < 3, no reduction needed)
```

Now multiply `x^2 * x = x^3`. Degree 3 is too large, so we reduce modulo `x^3 + x + 1`. From `x^3 + x + 1 = 0` (in GF(2)) we get `x^3 = x + 1` (remember minus equals plus). So `x^2 * x = x^3 = x + 1`.

In AES this "multiply by x" step has its own name, xtime. For a byte, shift left by 1 bit. If the 8th bit overflows (the original byte had its high bit set), XOR in `0x1B` (the tail of the polynomial 0x11B) to reduce back to 8 bits. xtime is the building block of the AES MixColumns step.

To summarize: GF(p) is used for DH and RSA-style arithmetic, and GF(2^n) is used for AES and a few other ciphers. "Order" and "generator" are words you will meet again and again, especially in DH and ECC.

## 2. Demo

This has two parts, plain Python for GF(p) and GF(2^8), then Sage doing the same in a few lines.

```python
# finite_fields.py - element order in GF(p), and multiplication in GF(2^8)

def element_order(a, p):
    # Order of a in the multiplicative group Z_p*: smallest exponent k with a^k = 1.
    k, x = 1, a % p
    while x != 1:
        x = (x * a) % p
        k += 1
    return k

def find_generators(p):
    # A generator is an element whose order equals p-1.
    return [a for a in range(1, p) if element_order(a, p) == p - 1]

def gmul(a, b):
    # Multiply in GF(2^8) with irreducible polynomial 0x11B (Russian peasant algorithm).
    product = 0
    for _ in range(8):
        if b & 1:
            product ^= a            # addition is XOR
        carry = a & 0x80            # high bit about to overflow
        a = (a << 1) & 0xFF
        if carry:
            a ^= 0x1B               # reduce modulo the irreducible polynomial
        b >>= 1
    return product

def main():
    # Order of every element in Z_7*
    orders = {a: element_order(a, 7) for a in range(1, 7)}
    print("Orders in Z_7*:", orders)
    print("Generators of Z_7*:", find_generators(7))

    # Classic example from the AES document: 0x57 * 0x13 = 0xFE
    print("0x57 * 0x13 =", hex(gmul(0x57, 0x13)))
    # 0x53 and 0xCA are inverses of each other in GF(2^8): product = 1
    print("0x53 * 0xCA =", hex(gmul(0x53, 0xCA)))

if __name__ == "__main__":
    main()
```

Output:

```
Orders in Z_7*: {1: 1, 2: 3, 3: 6, 4: 3, 5: 6, 6: 2}
Generators of Z_7*: [3, 5]
0x57 * 0x13 = 0xfe
0x53 * 0xCA = 0x1
```

In the output, in Z_7* the elements 3 and 5 have order 6 (equal to the group order), so they are generators. There are 2 generators, which equals `phi(6) = 2`. In GF(2^8), `0x57 * 0x13 = 0xFE` matches the classic example in the AES standard (FIPS-197), which confirms the field multiplication is correct. And `0x53 * 0xCA = 0x1` means 0x53 and 0xCA are inverses of each other, the relation used when building the AES S-box.

In Sage the same work is much shorter (run inside `sage`):

```python
sage: F = GF(7)
sage: F.multiplicative_generator()          # a generator of GF(7)*
3
sage: K.<a> = GF(2^8)                        # GF(2^8) with variable a playing the role of x
sage: x = K.fetch_int(0x57); y = K.fetch_int(0x13)
sage: (x * y).integer_representation()       # 0x57 * 0x13
254
```

Sage returns a generator and the result 254 = 0xFE, matching the hand-written code. When you work on ECC or advanced RSA, this brevity of Sage saves you a lot of effort.

## 3. Lab

- Task, in two small parts:
  1. For p = 101, find all generators of Z_101* and count them. Check that the count equals phi(100).
  2. In GF(2^8), implement multiplication yourself and confirm that 0x53 has inverse 0xCA, that is `gmul(0x53, 0xCA) == 1`.
- Files: none, write it yourself.
- Hints, in steps:
  - Hint 1: reuse `element_order` and `find_generators`, only change p to 101.
  - Hint 2: the number of generators of Z_p* is always phi(p-1). For p = 101 that is phi(100). Compute phi(100) to compare.
  - Hint 3: for GF(2^8), use `gmul` from the demo. To find the inverse of a byte yourself, scan all 255 nonzero bytes for the one that multiplies to 1, or use `gmul(b, b^254)` (the power 254 in GF(2^8) gives the inverse, because the multiplicative group has 255 elements).
- Done when: you list the correct set of generators of Z_101*, the count matches phi(100) = 40, and you confirm that 0x53 and 0xCA are inverses in GF(2^8).

## 4. Key takeaways

- In a field every nonzero element has an inverse, so addition, subtraction, multiplication and division all work.
- `Z_n` is a field if and only if n is prime. It is then called GF(p).
- The order of an element divides the order of the group (Lagrange), which gives Fermat and Euler.
- A generator has order equal to the group order, its powers sweep the whole group, and Z_p* has phi(p-1) generators.
- GF(2^n): addition is XOR, multiplication is polynomial multiplication modulo an irreducible polynomial.
- AES lives in GF(2^8) with the irreducible polynomial 0x11B.

## 5. Common pitfalls

- Assuming Z_n is always a field. It is not when n is composite. There are then zero divisors and some elements have no inverse.
- Confusing the order of an element with the order of the group. They differ, and an element is a generator only when the two are equal.
- Using a generator of small order in Diffie-Hellman. It exposes a small subgroup and opens the way to Pohlig-Hellman.
- In GF(2^n), forgetting the reduction modulo the irreducible polynomial, or using the wrong polynomial. Each n has its own polynomial, and AES uses 0x11B.
- Mixing up addition in GF(2^n) with integer addition. Here addition is XOR, with no carry.
- Mixing up GF(2^8) with Z_256. Z_256 is not a field (256 is not prime), and its arithmetic is completely different.

## 6. Further reading

- "An Introduction to Mathematical Cryptography" (Hoffstein, Pipher, Silverman), the chapters on groups and finite fields.
- "A Computational Introduction to Number Theory and Algebra" (Victor Shoup), a free PDF, very thorough on groups and fields.
- FIPS-197 (the AES standard), the section on arithmetic in GF(2^8), to see exactly what you just coded.
- SageMath documentation, the `GF` and `FiniteField` sections.
- CryptoHack (cryptohack.org), the Mathematics track and the start of the Symmetric track.
