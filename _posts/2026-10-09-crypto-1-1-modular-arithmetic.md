---
title: "Lesson 1.1: Modular Arithmetic"
image:
  path: /assets/img/covers/crypto-1-1-modular-arithmetic.webp
  alt: "Modular Arithmetic"
date: 2023-01-28 01:04:00 +0700
categories: ["Cryptography", "Crypto · Math Foundations"]
tags: [cryptography, modular-arithmetic, extended-euclid, math]
render_with_liquid: false
---

Modular arithmetic is the math underneath almost everything that follows: RSA, Diffie-Hellman and ECC all work in it. After this lesson you can compute a modular power of a huge number almost instantly, find a modular inverse, and use extended Euclid. You will use these three skills constantly through the series.

![Modular Arithmetic](/assets/img/crypto/crypto-1-1-modular-arithmetic.svg)
_Square-and-multiply keeps every value below m, and extended Euclid turns gcd(a, m) = 1 into a modular inverse._

Part: 1 (Math Foundations) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 0.3 (setting up the lab).

**Tools:** Python 3, optionally SageMath.

## Goals

After this lesson you can add, multiply and exponentiate modulo m, and you reduce mod at every step so you never touch huge numbers. You understand and can implement square-and-multiply (fast exponentiation) and know why it is O(log e). You can find a modular inverse and know when it exists. You can use extended Euclid to compute the gcd and the Bezout coefficients, and you see that it is how the inverse is computed.

## 1. Theory

For this whole math part, I give a concrete numeric example first, you see how it runs, and only then I generalize. Modular arithmetic is not hard, only unfamiliar at first.

### The mod operation and congruence

Take a 12-hour clock as an example. It is 10 o'clock now, so what time is it in 5 hours? It is not 15, it is 3, because the count wraps around after 12. That is modular arithmetic: we only care about the remainder after dividing by a number m, called the modulus.

For example, 17 mod 12 = 5, because 17 = 1 * 12 + 5. On the clock, 17:00 is 5 in the afternoon.

Two numbers a and b are congruent modulo m, written `a ≡ b (mod m)`, when m divides the difference a - b. That means they give the same remainder when divided by m. For example `17 ≡ 5 (mod 12)` because 17 - 5 = 12 is divisible by 12. Likewise `29 ≡ 5 (mod 12)` and `5 ≡ 5 (mod 12)`.

The set of possible remainders when dividing by m is `Z_m = {0, 1, 2, ..., m-1}`. For m = 12 that is 0 to 11. Every integer, however large, falls onto exactly one element of this set when you take the mod. All of public key crypto happens inside such a Z_m, except that m has several hundred digits.

### Addition and multiplication modulo m

Addition and multiplication work as usual, you just take the mod at the end:

- `(7 + 8) mod 12 = 15 mod 12 = 3`.
- `(7 * 8) mod 11 = 56 mod 11 = 1`, because 56 = 5 * 11 + 1.

The property that saves you is that you can take the mod at any step and the result does not change. Specifically:

```
(a + b) mod m = ((a mod m) + (b mod m)) mod m
(a * b) mod m = ((a mod m) * (b mod m)) mod m
```

Why is this essential? In RSA you multiply 2048-bit numbers many times. If you multiply directly and only reduce at the end, the intermediate numbers grow enormous, using a lot of memory and running very slowly. With the property above, you reduce right after each multiplication and keep every number smaller than m. An intermediate value is never larger than m^2. This is why every crypto library reduces constantly and never defers it.

### Modular exponentiation and square-and-multiply

Now for the interesting part, computing `a^e mod m` when e is huge. Take `3^13 mod 7` as an example.

The naive way is to multiply 3 by itself 13 times and then reduce. That is fine for exponent 13, but RSA has exponents around 2048 bits, which is about 10^616. Multiplying that many times would take longer than the age of the universe. You need something smarter: square-and-multiply, also called fast exponentiation.

The idea is to write the exponent in binary and use repeated squaring. With 13 = 1101 (binary), we have 13 = 8 + 4 + 1, so `3^13 = 3^8 * 3^4 * 3^1`. The powers 3^1, 3^2, 3^4, 3^8 come from repeated squaring, one multiplication per step:

```
3^1 mod 7 = 3
3^2 mod 7 = 3*3  = 9  mod 7 = 2
3^4 mod 7 = 2*2  = 4  mod 7 = 4
3^8 mod 7 = 4*4  = 16 mod 7 = 2
```

Now multiply the ones that correspond to the 1 bits in 13 = 1101, which are the positions 8, 4 and 1:

```
3^13 mod 7 = 3^8 * 3^4 * 3^1 mod 7 = 2 * 4 * 3 mod 7 = 24 mod 7 = 3
```

So `3^13 mod 7 = 3`. Instead of 12 multiplications, we need about log2(13) squaring steps plus a few multiplications. In general, square-and-multiply costs O(log e) multiplications, not O(e). With e around 2048 bits, that is roughly 2048 steps instead of 10^616. That is the difference between instant and never.

(As a side observation, 3^6 mod 7 = 1, so the powers of 3 repeat with period 6. This is Fermat's little theorem, covered in Lesson 1.2. Here we only need square-and-multiply.)

In Python, `pow(3, 13, 7)` runs exactly this algorithm in C, very fast, and returns 3. Always use the three-argument `pow(base, exp, mod)` and never write `base**exp % mod`.

### Modular inverse

In ordinary arithmetic, dividing by 3 means multiplying by 1/3. But in Z_m there are no fractions, everything is an integer. So what does "divide" mean? It means multiplying by the modular inverse.

The inverse of a modulo m, written `a^{-1} mod m`, is the number x such that `a * x ≡ 1 (mod m)`. For example `3^{-1} mod 7 = 5`, because `3 * 5 = 15 = 2*7 + 1 ≡ 1 (mod 7)`. Multiplying by 5 in Z_7 is "dividing by 3".

The inverse does not always exist. The condition is `gcd(a, m) = 1`, meaning a and m are coprime (no common divisor other than 1). The reasoning is that if a and m share a divisor d > 1, then every multiple of a modulo m is a multiple of d, and so can never reach 1. For example, in Z_6 the number 2 has no inverse, because 2 and 6 are both divisible by 2, and multiplying 2 by anything gives an even number, never 1. This is why we later prefer a prime modulus: when m is prime, EVERY nonzero a is coprime to m, so every one has an inverse.

### The Euclidean algorithm and extended Euclid

How do we find the inverse quickly? With extended Euclid. First, a review of the ordinary Euclidean algorithm for the gcd (greatest common divisor): divide repeatedly with remainder, and substitute the remainder.

Example `gcd(240, 46)`:

```
240 = 5 * 46 + 10
 46 = 4 * 10 + 6
 10 = 1 * 6  + 4
  6 = 1 * 4  + 2
  4 = 2 * 2  + 0   <- remainder 0, stop
```

The last nonzero remainder is 2, so `gcd(240, 46) = 2`.

Extended Euclid does one more thing: besides the gcd, it also finds two integers x, y with `a*x + b*y = gcd(a, b)`. The pair (x, y) is called the Bezout coefficients. You get them by substituting back from the bottom up:

```
2 = 6 - 1*4
  = 6 - 1*(10 - 1*6)      = 2*6 - 1*10
  = 2*(46 - 4*10) - 1*10  = 2*46 - 9*10
  = 2*46 - 9*(240 - 5*46) = 47*46 - 9*240
```

So `2 = 47*46 - 9*240`. Check: 47*46 = 2162, 9*240 = 2160, and the difference is exactly 2. These are the Bezout coefficients of (240, 46).

Now for the nice part, extended Euclid gives the modular inverse almost for free. Find `17^{-1} mod 43`. Running extended Euclid on (17, 43) gives:

```
1 = 2*43 - 5*17
```

(Check: 2*43 = 86, 5*17 = 85, difference = 1.) Take both sides mod 43. The term `2*43` vanishes mod 43, leaving `-5*17 ≡ 1 (mod 43)`. So `17^{-1} ≡ -5 (mod 43)`. Bring it into the range 0 to 42: `-5 ≡ 38 (mod 43)`. Check: `17 * 38 = 646 = 15*43 + 1 ≡ 1 (mod 43)`. Correct.

In general, to find `a^{-1} mod m`, run extended Euclid on (a, m). If the gcd is 1, you have `a*x + m*y = 1`, and then `x mod m` is the inverse of a. If the gcd is not 1, the inverse does not exist.

Why are these three skills the backbone of public key crypto? RSA key generation needs `d = e^{-1} mod phi(n)`, which is a modular inverse. RSA encryption and decryption are modular exponentiation, which is square-and-multiply. Diffie-Hellman and ECC work the same way. Once you have these three firmly, the second half of the series reads easily.

## 2. Hands-on (demo)

The plain Python below implements all three skills and checks every number in section 1. No external library is needed.

```python
# modular_toolkit.py: implement and verify modular arithmetic
# Plain Python only, runs as is.

def fast_pow(base, exp, mod):
    # Square-and-multiply: compute base^exp mod mod with O(log exp) multiplications.
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:            # lowest bit of exp is 1 -> multiply base into the result
            result = (result * base) % mod
        base = (base * base) % mod  # square base for the next bit
        exp >>= 1
    return result

def egcd(a, b):
    # Extended Euclid: return (g, x, y) such that a*x + b*y = g = gcd(a, b).
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    # back-substitute: a*x + b*y = g with x = y1, y = x1 - (a//b)*y1
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, m):
    # Modular inverse via egcd; raise an error if gcd(a, m) != 1.
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f"{a} has no inverse mod {m} because gcd = {g}")
    return x % m

def main():
    # Fast exponentiation matches the built-in pow()
    print("3^13 mod 7   =", fast_pow(3, 13, 7), "(pow:", pow(3, 13, 7), ")")

    # gcd and Bezout for (240, 46)
    g, x, y = egcd(240, 46)
    print(f"gcd(240,46)  = {g}, Bezout: 240*{x} + 46*{y} = {240*x + 46*y}")

    # Modular inverse
    print("3^-1 mod 7   =", modinv(3, 7))     # expected 5
    print("17^-1 mod 43 =", modinv(17, 43))   # expected 38

    # Python 3.8+ has pow(a, -1, m) built in to compute the inverse
    print("pow(17,-1,43) =", pow(17, -1, 43))

if __name__ == "__main__":
    main()
```

Output:

```
3^13 mod 7   = 3 (pow: 3 )
gcd(240,46)  = 2, Bezout: 240*-9 + 46*47 = 2
3^-1 mod 7   = 5
17^-1 mod 43 = 38
pow(17,-1,43) = 38
```

Every number matches the theory. `fast_pow(3,13,7) = 3` equals the built-in `pow(3,13,7)`, which shows that the square-and-multiply I wrote is correct. `egcd(240,46)` gives gcd = 2 and Bezout coefficients that satisfy `240*x + 46*y = 2`. The two ways of computing the inverse (my own `modinv` and the built-in `pow(a,-1,m)` from Python 3.8) give the same result, 38. From Python 3.8 on you only need `pow(a, -1, m)`, but understanding what happens underneath means that in another language where it is not built in, you can still write it by hand.

## 3. Lab

- Task: take a toy RSA with `n = 3233`, `e = 17`, where `n = p * q` with `p = 61, q = 53`, and a ciphertext `c = 2790`. By hand, compute `phi = (p-1)*(q-1)`, find the private key `d = e^{-1} mod phi` (use your own extended Euclid, do not call `pow(-1)` directly), then decrypt `m = c^d mod n`. The result should be a small number (hint: it is the ASCII code of a character).
- Files: none, all parameters are given above, so write the script yourself.
- Hints, step by step:
  - Hint 1: `phi = 60 * 52 = 3120`.
  - Hint 2: `d` is the inverse of 17 modulo 3120. Use the `modinv(17, 3120)` you just wrote.
  - Hint 3: decryption is `m = fast_pow(c, d, n)`. Then turn `m` into a character with `chr(m)`.
- Done when: you recover `m` and read the original character, entirely with your own tools. (Part 6 is a whole chapter on RSA, so this is only a first taste to show that modular arithmetic carries the whole thing.)

## 4. Key takeaways

- [ ] You may reduce mod at every step. Always reduce after each multiplication so numbers do not grow.
- [ ] Modular exponentiation must use square-and-multiply, O(log e). In Python that is `pow(base, exp, mod)`, never `base**exp % mod`.
- [ ] The modular inverse `a^{-1} mod m` exists if and only if `gcd(a, m) = 1`.
- [ ] Extended Euclid gives both the gcd and the Bezout coefficients, and from them the inverse, since if `a*x + m*y = 1` then `x mod m = a^{-1} mod m`.
- [ ] With a prime modulus, every nonzero element has an inverse.

## 5. Common pitfalls

- Writing `a**e % m` with large numbers. Python will try to compute the full `a**e` (a huge number) before reducing, which hangs the machine or uses all the RAM. Always use `pow(a, e, m)`.
- Forgetting that the inverse exists only when `gcd(a, m) = 1`. Calling `modinv` with a and m that are not coprime will (and should) raise an error. If it silently returns a wrong number, you will debug for a whole session.
- The sign of mod with negative numbers. In Python, `-5 % 43` gives 38 (always nonnegative), which is convenient. In C and Java, `-5 % 43` gives -5. When porting code or reading code in another language, normalize into the range `[0, m)`.
- Reducing the exponent arbitrarily. You may NOT do `a^e mod m = a^(e mod m) mod m`. The exponent reduces modulo `phi(m)`, not m, and also needs a gcd condition. Lesson 1.2 (Fermat and Euler) covers this fully.

## 6. Further reading

- "An Introduction to Mathematical Cryptography" (Hoffstein, Pipher, Silverman), chapter 1, which explains modular arithmetic and extended Euclid in detail.
- "Handbook of Applied Cryptography" (Menezes, van Oorschot, Vanstone), chapter 2, on the number theory background.
- CryptoHack (cryptohack.org), the Modular Arithmetic path, worth doing so it sticks.
- SageMath documentation, `IntegerModRing` and `xgcd`, to see how the stronger tool is used.
