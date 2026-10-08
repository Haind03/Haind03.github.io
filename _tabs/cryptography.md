---
title: Cryptography
icon: fas fa-lock
order: 3
render_with_liquid: false
---

My notes on cryptography for CTF, from the math foundations through classical ciphers, symmetric and public-key crypto, to the real attacks you see in challenges. Most crypto challenges are not about breaking AES or RSA, they are about finding where someone used them wrong.

The labs are small challenges with a working solve script. Everything is for learning, CTFs, and systems you are allowed to test.
{: .prompt-warning }

## Crypto · Getting Started

| # | Lesson |
|---|---|
| 0.1 | [Cryptography Goals and Threat Models](/posts/crypto-0-1-cryptography-goals-threat-models/) |
| 0.2 | [Kerckhoffs's Principle and Ethics](/posts/crypto-0-2-kerckhoffs-principle-ethics/) |
| 0.3 | [Setting Up a Crypto Lab](/posts/crypto-0-3-setting-up-crypto-lab/) |

## Crypto · Math Foundations

| # | Lesson |
|---|---|
| 1.1 | [Modular Arithmetic](/posts/crypto-1-1-modular-arithmetic/) |
| 1.2 | [Primes, Euler's Totient, and the Fermat and Euler Theorems](/posts/crypto-1-2-primes-euler-totient-fermat-euler/) |
| 1.3 | [CRT and the Chinese Remainder Theorem](/posts/crypto-1-3-crt-chinese-remainder-theorem/) |
| 1.4 | [Groups, Rings and Finite Fields](/posts/crypto-1-4-groups-rings-finite-fields/) |
| 1.5 | [Probability, the Birthday Paradox and Entropy](/posts/crypto-1-5-probability-birthday-paradox-entropy/) |

## Crypto · Classical Ciphers

| # | Lesson |
|---|---|
| 2.1 | [Encoding Is Not Encryption](/posts/crypto-2-1-encoding-not-encryption/) |
| 2.2 | [Caesar, Vigenere and Frequency Analysis](/posts/crypto-2-2-caesar-vigenere-frequency-analysis/) |
| 2.3 | [Rail Fence, Playfair, and Enigma](/posts/crypto-2-3-rail-fence-playfair-enigma/) |

## Crypto · XOR and OTP

| # | Lesson |
|---|---|
| 3.1 | [Single-Byte and Multi-Byte XOR](/posts/crypto-3-1-single-byte-multi-byte-xor/) |
| 3.2 | [One-Time Pad and Key Reuse](/posts/crypto-3-2-one-time-pad-key-reuse/) |
| 3.3 | [Lab on Breaking Repeating-Key XOR](/posts/crypto-3-3-lab-breaking-repeating-key-xor/) |

## Crypto · Symmetric Encryption

| # | Lesson |
|---|---|
| 4.1 | [Block Ciphers and AES Basics](/posts/crypto-4-1-block-ciphers-aes-basics/) |
| 4.2 | [ECB, CBC, CTR and GCM modes of operation](/posts/crypto-4-2-ecb-cbc-ctr-gcm-modes/) |
| 4.3 | [PKCS#7 padding and the padding oracle attack](/posts/crypto-4-3-pkcs7-padding-oracle-attack/) |
| 4.4 | [CBC bit flipping and missing integrity](/posts/crypto-4-4-cbc-bit-flipping-missing-integrity/) |
| 4.5 | [Stream ciphers, RC4, ChaCha20 and nonce reuse](/posts/crypto-4-5-stream-ciphers-rc4-chacha20-nonce-reuse/) |
| 4.6 | [Padding oracle and byte-at-a-time ECB lab](/posts/crypto-4-6-padding-oracle-ecb-lab/) |

## Crypto · Hashes and MACs

| # | Lesson |
|---|---|
| 5.1 | [Hash Functions, MD5/SHA, and Collisions](/posts/crypto-5-1-hash-functions-md5-sha-collisions/) |
| 5.2 | [Length Extension Attack](/posts/crypto-5-2-length-extension-attack/) |
| 5.3 | [MAC, HMAC, and Timing Attacks on Tag Comparison](/posts/crypto-5-3-mac-hmac-timing-attacks-tag-comparison/) |
| 5.4 | [Password Storage and Cracking with hashcat](/posts/crypto-5-4-password-storage-cracking-hashcat/) |

## Crypto · RSA

| # | Lesson |
|---|---|
| 6.1 | [How RSA Works](/posts/crypto-6-1-rsa-works/) |
| 6.2 | [Attacks on Weak RSA Parameters](/posts/crypto-6-2-attacks-weak-rsa-parameters/) |
| 6.3 | [Common Modulus and Hastad Broadcast Attacks](/posts/crypto-6-3-common-modulus-hastad-broadcast-attacks/) |
| 6.4 | [Wiener Attack and Coppersmith](/posts/crypto-6-4-wiener-attack-coppersmith/) |
| 6.5 | [RSA Padding, PKCS#1 v1.5, Bleichenbacher and OAEP](/posts/crypto-6-5-rsa-padding-pkcs1-bleichenbacher-oaep/) |
| 6.6 | [RSA CTF Lab from Easy to Hard](/posts/crypto-6-6-rsa-ctf-lab-easy-hard/) |

## Crypto · Diffie-Hellman

| # | Lesson |
|---|---|
| 7.1 | [Diffie-Hellman and the Discrete Logarithm Problem](/posts/crypto-7-1-diffie-hellman-discrete-logarithm/) |
| 7.2 | [Attacks on Diffie-Hellman](/posts/crypto-7-2-attacks-diffie-hellman/) |

## Crypto · Elliptic Curves

| # | Lesson |
|---|---|
| 8.1 | [ECC Basics, ECDH and ECDSA](/posts/crypto-8-1-ecc-basics-ecdh-ecdsa/) |
| 8.2 | [ECDSA Private Key Recovery from Nonce Reuse](/posts/crypto-8-2-ecdsa-nonce-reuse/) |
| 8.3 | [Weak Elliptic Curves](/posts/crypto-8-3-weak-elliptic-curves/) |

## Crypto · Randomness

| # | Lesson |
|---|---|
| 9.1 | [PRNG vs CSPRNG and Mersenne Twister](/posts/crypto-9-1-prng-csprng-mersenne-twister/) |
| 9.2 | [Recovering MT19937 State and Breaking LCG](/posts/crypto-9-2-recovering-mt19937-state-breaking-lcg/) |

## Crypto · Crypto in Practice

| # | Lesson |
|---|---|
| 10.1 | [TLS and PKI Certificate Chains](/posts/crypto-10-1-tls-pki-certificate-chains/) |
| 10.2 | [Z3 and SMT for Crypto](/posts/crypto-10-2-z3-smt-crypto/) |
| 10.3 | [Post-Quantum Cryptography Basics](/posts/crypto-10-3-post-quantum-cryptography-basics/) |

## Crypto · Real-World Practice

| # | Lesson |
|---|---|
| 11.1 | [Cryptopals Sets 1 to 3](/posts/crypto-11-1-cryptopals-sets-1-3/) |
| 11.2 | [Writing a Crypto CTF Writeup for ECDSA Nonce Reuse](/posts/crypto-11-2-writing-crypto-ctf-writeup-ecdsa/) |
| 11.3 | [Final Project Breaking a Custom Token Protocol](/posts/crypto-11-3-final-project-breaking-custom-token-protocol/) |
