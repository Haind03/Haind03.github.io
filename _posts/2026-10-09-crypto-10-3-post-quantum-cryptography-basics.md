---
title: "Lesson 10.3: Post-Quantum Cryptography Basics"
image:
  path: /assets/img/covers/crypto-10-3-post-quantum-cryptography-basics.webp
  alt: "Post-Quantum Cryptography Basics"
date: 2023-12-02 01:55:00 +0700
categories: ["Cryptography", "Crypto · Crypto in Practice"]
tags: [cryptography, post-quantum, lattice, lwe]
render_with_liquid: false
---

A large enough quantum computer will break RSA and ECC in polynomial time. This is not because it is faster. It is because it runs a fundamentally different algorithm (Shor). This lesson explains why, why hashes and symmetric ciphers are only weakened by half and not broken (Grover), what a lattice is and why it was chosen as the base for the post-quantum standards, and gives an overview of the new NIST PQC standards such as ML-KEM (Kyber) and ML-DSA (Dilithium). It is mostly theory, with two small runnable demos to build intuition.

![Shor, Grover and post-quantum cryptography](/assets/img/crypto/crypto-10-3-post-quantum-cryptography-basics.svg)
_Shor breaks factoring and discrete log at any key size. Grover only halves symmetric strength. The replacement is a different hard problem._

Part 10 (Crypto in Practice) | Time: about 55 minutes | Difficulty: medium, concept heavy

**Prerequisites:** Lesson 6.1 (RSA), Lesson 7.1 (Diffie-Hellman, discrete log), Lesson 8.1 (ECC). You need to know that RSA relies on factoring and ECC relies on discrete log to see why Shor breaks both.

**Tools:** Python 3 (standard library). The two demos use ordinary arithmetic and need nothing extra. This lesson leans toward theory, and the demos are only for intuition.

## Goals

By the end of this lesson you can explain why Shor breaks RSA and ECC while Grover only weakens symmetric ciphers and hashes by half. You know why the answer is to switch to a different hard problem and not to use endlessly longer keys. You understand what a lattice is at an intuitive level, and how LWE and NTRU build hardness on it. You can name the main NIST PQC standards and say what each is used for.

## 1. Theory

### 1.1. Why quantum computers break RSA and ECC

RSA is secure because factoring a large number n = p·q is hard for ordinary machines. ECC and Diffie-Hellman are secure because the discrete log (finding x given g and g^x) is hard. What they share is that both reduce to period finding of a periodic function.

Shor's algorithm (Peter Shor, 1994) does exactly that. To factor n, pick a random number a and find the period r of the function f(x) = a^x mod n, that is, the smallest r such that a^r ≡ 1 (mod n). An ordinary machine finds r very slowly, but a quantum computer uses the quantum Fourier transform to find r in polynomial time. Once r is known, the rest is simple classical arithmetic: if r is even and a^(r/2) is not congruent to -1, then gcd(a^(r/2) - 1, n) gives a real factor of n.

The key point is that the hardness of RSA and ECC rests on ordinary machines being unable to find the period. When that part falls, the whole family of public-key cryptography based on factoring and discrete log (RSA, DH, DSA, ECDH, ECDSA) falls with it. Longer keys do not help, because Shor runs in polynomial time in the number of bits. Doubling the key length only makes it a little slower, not exponentially slower.

### 1.2. Grover only halves the strength

For symmetric ciphers (AES) and hashes (SHA-2, SHA-3), the quantum tool is Grover's algorithm, a search algorithm. To find a key in a space of 2^k elements, an ordinary machine needs about 2^k trials, and Grover needs about 2^(k/2). That is a square-root advantage, not a polynomial one.

The consequence is easy to remember, since Grover cuts the strength of a symmetric key to half the bits. AES-128 keeps about 64 bits of quantum security (a bit thin), so AES-256 (which keeps 128 bits) is the safe choice. For hashes, SHA-256 preimage resistance drops to about 128 bits, which is still plenty. In short, symmetric ciphers and hashes only need to double their length, with no need to replace the algorithm. The public-key part is what has to be rebuilt from scratch.

### 1.3. The answer: switch to a different hard problem

Post-quantum cryptography means public-key systems built on problems that neither ordinary nor quantum machines are known to solve quickly. There are several candidate families: lattice-based (the most common), code-based (such as McEliece), hash-based (for signatures, such as SPHINCS+), and isogeny-based (once promising, but SIKE was broken in 2022). After many years of selection, NIST has standardized mostly lattice systems.

### 1.4. What a lattice is

A lattice is the set of all integer combinations of a set of basis vectors. In the plane, given two vectors, the lattice is every point you can reach by taking integer steps along those two vectors, which forms an infinite grid of points. In many dimensions, two problems become very hard:

- SVP (Shortest Vector Problem): find the shortest non-zero vector in the lattice.
- CVP (Closest Vector Problem): given an arbitrary point, find the lattice point closest to it.

In high dimensions, with a "bad" basis (long vectors that are nearly parallel), both problems are extremely hard, even for quantum computers. Lattice cryptography hides the secret in exactly that distance.

LWE (Learning With Errors) is the base problem for Kyber and many other systems. The idea is that you are given many linear equations in a secret s, but each equation has a small random error added. Without errors, solving the linear system is easy (Gaussian elimination). With small errors, recovering s becomes as hard as SVP on a lattice. The small noise is what makes the problem hard.

NTRU is another, older lattice family based on arithmetic in a polynomial ring. It is fast and compact, and it is the predecessor in spirit of many modern systems.

### 1.5. The NIST PQC standards

In 2024 NIST published the first official standards (FIPS):

- ML-KEM (FIPS 203), originally Kyber: a KEM (Key Encapsulation Mechanism) for key exchange, replacing the role of ECDH in TLS. Based on Module-LWE.
- ML-DSA (FIPS 204), originally Dilithium: a digital signature, replacing ECDSA/RSA signing. Also lattice-based.
- SLH-DSA (FIPS 205), originally SPHINCS+: a digital signature based entirely on hashes. It is slow and signatures are large, but it has minimal security assumptions (it only needs a secure hash), so it serves as a backup option.

In practice, hybrid deployment has started: TLS exchanges keys with both X25519 (classical) and ML-KEM at the same time, so that if one breaks, the other still holds. The "harvest now, decrypt later" concern is the main driver: an adversary records encrypted traffic today and waits for a future quantum computer to decrypt it, so data that must stay secret for a long time has to move to PQC now.

## 2. Demo

Two small demos. They are not real PQC implementations, only a way to build intuition for the two main ideas of the lesson: Shor reduces to period finding, and LWE hides a secret behind noise.

### 2.1. The classical part of Shor: find the period, then factor n

The quantum computer handles the step of finding the period r of a^x mod n. For a small n we find r by trying values (only as an illustration), and the rest is classical arithmetic that turns r into factors. Running on n = 15:

```python
# shor_classic.py: illustrates the classical POST-PROCESSING part of Shor on n = 15
from math import gcd

n = 15
for a in [2, 7, 8, 11, 13]:
    r, val = None, 1
    for k in range(1, n + 1):            # find the period r: a^r mod n == 1 (a quantum computer does this step)
        val = (val * a) % n
        if val == 1:
            r = k
            break
    line = f"a={a:2d}  period r={r}"
    if r is not None and r % 2 == 0:
        t = pow(a, r // 2, n)
        if t != n - 1:                   # a^(r/2) != -1 mod n
            p, q = gcd(t - 1, n), gcd(t + 1, n)
            line += f"  ->  {n} = {p} x {q}"
        else:
            line += "  ->  a^(r/2) = -1 mod n, try another a"
    else:
        line += "  ->  r is odd, try another a"
    print(line)
```

Output:

```
a= 2  period r=4  ->  15 = 3 x 5
a= 7  period r=4  ->  15 = 3 x 5
a= 8  period r=4  ->  15 = 3 x 5
a=11  period r=2  ->  15 = 5 x 3
a=13  period r=4  ->  15 = 3 x 5
```

The whole step that turns r into factors is school arithmetic, and an ordinary machine does it instantly. The only thing the quantum computer does is find r quickly for an n of thousands of bits, where the trial loop above would never finish. This shows that RSA does not break because the arithmetic is hard. It breaks because the period finding step stops being hard.

### 2.2. A toy LWE: small noise is the barrier

A demo of a tiny LWE system that encrypts one bit in the Regev style. The secret is a vector s, and the public key is many equations a·s plus small noise. A bit is encrypted by adding a random subset and then adding q/2 if the bit is 1.

```python
# lwe_toy.py: toy LWE, encrypts 1 bit. Illustration only, NOT secure.
import random
random.seed(1337)

q, n, m, bound = 97, 8, 40, 2            # modulus, secret dimension, number of samples, noise bound

def dot(a, b):
    return sum(x * y for x, y in zip(a, b)) % q

s = [random.randrange(q) for _ in range(n)]
A = [[random.randrange(q) for _ in range(n)] for _ in range(m)]
e = [random.randint(-bound, bound) for _ in range(m)]     # small noise
b = [(dot(A[i], s) + e[i]) % q for i in range(m)]         # b = A.s + e

def encrypt(bit):
    S = [i for i in range(m) if random.random() < 0.5]    # random subset
    a_sum = [sum(A[i][j] for i in S) % q for j in range(n)]
    b_sum = (sum(b[i] for i in S) + bit * (q // 2)) % q
    return a_sum, b_sum

def decrypt(ct):
    a_sum, b_sum = ct
    v = (b_sum - dot(a_sum, s)) % q       # ~ bit*q/2 + sum of small noise
    return 1 if q // 4 <= v < 3 * q // 4 else 0

ok = all(decrypt(encrypt(bit)) == bit for bit in [0, 1] for _ in range(500))
print("secret s      =", s)
print("1000 decryptions all correct:", ok)
```

Output:

```
secret s      = [79, 68, 90, 46, 73, 74, 93, 21]
1000 decryptions all correct: True
```

The holder of s decrypts easily because the total noise is still small compared with q/2, so v near 0 gives bit 0 and v near q/2 gives bit 1. Someone without s sees only noisy linear equations in the pile of (A, b), and the noise breaks Gaussian elimination, pushing the recovery of s into a hard lattice problem. If `bound` is made large (noise too big), even the key holder decrypts wrongly, because the total noise exceeds q/4. That is why LWE parameters must be balanced: enough noise to be hard, small enough to still decrypt correctly.

## 3. Lab

- Light task (this lesson is mostly theory and has no graded lab): run `shor_classic.py` with n = 21 and n = 35, and find an a that gives factors. Observe when r is odd or when a^(r/2) ≡ -1 forces you to try another a.
- Experiment with LWE: in `lwe_toy.py`, raise `bound` step by step from 2 to 5, 10 and 20, run it again, and see at what threshold "1000 decryptions all correct" changes to False. Explain it using the relation between the total noise and q/4.
- Reading task: get the parameters of ML-KEM-768 (n, q, public key and ciphertext sizes) from FIPS 203 and compare the sizes with RSA-3072 and X25519. Write down your observation that PQC trades larger keys for security.
- Done when: you can explain in words why Shor kills RSA but Grover does not kill AES-256, and why noise is the core of LWE.

## 4. Key takeaways

- Shor reduces factoring and discrete log to period finding. Quantum computers find periods quickly, so RSA, DH and ECC all break.
- Grover only takes the square root of the key space, so symmetric ciphers and hashes only need to double their length (use AES-256, SHA-384 or higher).
- The answer is not longer keys but a different hard problem: lattice, code-based, hash-based.
- LWE hides a secret behind small noise. Without noise, Gaussian elimination solves it at once. With noise it is as hard as SVP.
- The main NIST standards: ML-KEM (Kyber) for key exchange, ML-DSA (Dilithium) and SLH-DSA (SPHINCS+) for signatures.
- "Harvest now, decrypt later" is the reason data that must stay secret for a long time should move to PQC now.

## 5. Common pitfalls

- Thinking that raising RSA to 8192 or 16384 bits is enough against quantum computers. It is not. Shor runs in polynomial time, so more bits only slow it down linearly and do not stop it.
- Treating Grover as equal to Shor. Grover only gives a square root, which is why symmetric ciphers survive and public-key systems do not.
- Thinking post-quantum means running on a quantum computer. It is the opposite, because PQC runs on ordinary machines and simply chooses problems that quantum computers cannot break either.
- Treating every PQC system as safe forever. SIKE (isogeny) reached the later rounds of NIST and was then broken on an ordinary machine in 2022. PQC means candidates that have not been broken yet, not proven absolute security.
- Forgetting the cost of PQC: keys and signatures are much larger than with ECC. Protocol design has to account for bandwidth and memory.
- Confusing a KEM with direct encryption. ML-KEM encapsulates a symmetric key and then uses that key to encrypt data with AEAD. It does not encrypt long data directly with a lattice.

## 6. Further reading

- NIST FIPS 203 (ML-KEM), 204 (ML-DSA), 205 (SLH-DSA): the official standard documents. Read the overview and the parameter tables.
- The talk "A Decade of Lattice Cryptography" by Chris Peikert: a serious but readable introduction to lattices and LWE.
- The SIKE break by Castryck and Decru (2022): a clear example that a PQC candidate can still fall.
- Lesson 6.1 (RSA) and Lesson 8.1 (ECC) in this series: review the exact hard problems that Shor targets.
- The pq-crystals.org site (Kyber, Dilithium) has reference implementations and design documents.
