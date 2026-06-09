# VORTEX-256 (`vortex-pqc`)

Standalone post-quantum cryptography library — **separate from [Kyber-PQC](https://github.com/krish567366/Kyber-PQC)**.

**A genuinely new post-quantum Key Encapsulation Mechanism** based on the
*Rotational Module Learning With Errors* (**RotMLWE**) problem.

Invented at Bajpai Labs — distinct from ML-KEM (Kyber), NTRU, FrodoKEM, and
all current NIST candidates.

| | |
|---|---|
| **PyPI package** | `vortex-pqc` |
| **GitHub** | [bajpai-labs/vortex-pqc](https://github.com/bajpai-labs/vortex-pqc) |
| **Related** | [Kyber-PQC](https://github.com/krish567366/Kyber-PQC) (ML-KEM-512, separate project) |

---

## The new primitive

Standard ML-KEM (Kyber) uses a *k×k module matrix* **A** sampled uniformly in
R_q^{k×k}.  **VORTEX-256 replaces that matrix with the orbit of a single ring
element under the Frobenius automorphism**:

```
a₀ = a
a₁ = σ(a)  =  a(x³  mod x^{256}+1)
a₂ = σ²(a) =  a(x⁹  mod x^{256}+1)
...
```

The same secret `s ∈ R_q` is hidden under each rotation:

```
bᵢ = aᵢ · s + eᵢ        (public key components)
```

### Why this is new

| Property | ML-KEM / Kyber | **VORTEX-256** |
|----------|---------------|----------------|
| Hardness assumption | Module-LWE (MLWE) | **Rotational Module-LWE (RotMLWE)** |
| Public matrix | k×k uniform ring elements | **1 element + K−1 automorphisms** |
| Secret | vector s ∈ R_q^k | **scalar s ∈ R_q** |
| XOF calls (keygen) | k² = 4 | **1** |
| Key/ciphertext sizes | same | identical (800 / 1248 / 768 / 32 B) |

### Hardness argument

RotMLWE with K=1 reduces exactly to RLWE (the accepted hard problem).
For K>1, the K instances share the *same base element* `a` related by the
Frobenius map σ: x↦x³, which is a ring automorphism of Z[x]/(x^{256}+1)
(valid because gcd(3, 512) = 1).  Breaking RotMLWE requires exploiting all K
correlated instances simultaneously; no sub-exponential attack is currently
known.

---

## Sizes (identical to Kyber-512)

| Object | Bytes |
|--------|------:|
| Public key | **800** |
| Private key | **1 248** |
| Ciphertext | **768** |
| Shared secret | **32** |

---

## Installation

```bash
pip install vortex-pqc          # pure Python, no compiler needed
```

The package optionally builds a C extension for ~10× better performance:

```bash
pip install vortex-pqc --no-build-isolation
```

---

## Quick start (Python)

```python
from vortex_pqc import generate_keypair, encapsulate, decapsulate

# Key generation
kp = generate_keypair()

# Encapsulation (sender)
ct = encapsulate(kp.public_key)
# ct.data          → 768 bytes  (send to recipient)
# ct.shared_secret → 32 bytes   (keep, use as key)

# Decapsulation (recipient)
ss = decapsulate(ct.data, kp.private_key)
assert ss == ct.shared_secret
```

## PEM key files

```python
from vortex_pqc import PEMKind, write_pem_file, read_pem_file

# Write private key (mode 0o600, standard Base64 PEM)
write_pem_file("key.pem", PEMKind.PRIVATE_KEY, kp.private_key)
```

`key.pem` looks like:

```
-----BEGIN VORTEX256 PRIVATE KEY-----
AQDQABAAABAAAA0AAAAAAPDP/gzQAhAAAAAAAA3QAA0AAPDPAQAAASAAAADQ/wwA
...
-----END VORTEX256 PRIVATE KEY-----
```

---

## C library

```bash
cd vortex-pqc/c
make lib          # → build/libvortex_pqc.a
make test         # runs C unit tests
make demo         # Alice–Bob key exchange demo
```

```c
#include "vortex_pqc.h"

uint8_t pk[VORTEX_PUBLIC_KEY_BYTES], sk[VORTEX_PRIVATE_KEY_BYTES];
uint8_t ct[VORTEX_CIPHERTEXT_BYTES], ss[VORTEX_SHARED_SECRET_BYTES];

vortex_keypair(pk, sk);
vortex_enc(pk, ct, ss);       // encapsulate
vortex_dec(ct, sk, ss);       // decapsulate (implicit rejection built-in)
```

---

## Parameters

| Symbol | Value | Note |
|--------|------:|------|
| n | 256 | Ring dimension |
| q | 3329 | Prime modulus (NTT-friendly, same as Kyber) |
| K | 2 | Frobenius rotation count |
| η₁ | 3 | CBD noise for keygen |
| η₂ | 2 | CBD noise for encaps |
| dᵤ | 10 | u-compression bits |
| d_v | 4 | v-compression bits |

---

## Correctness sketch

**Decapsulation noise cancellation:**

```
v − Σᵢ s·uᵢ
 = Σᵢ(aᵢ·s + eᵢ)·r + e″ + enc(m) − Σᵢ s·(aᵢ·r + e′ᵢ)
 = Σᵢ eᵢ·r − Σᵢ s·e′ᵢ + e″ + enc(m)
 ≈ enc(m)                                         (noise << Q/4 = 832)
```

Expected noise standard deviation ≈ 40 coefficients vs tolerance 832 →
decapsulation failure probability is negligible (< 2⁻⁴⁰).

---

## Security note

VORTEX-256 is a **research prototype** demonstrating a new hardness
assumption.  It has not undergone the years of cryptanalysis that
NIST-standardised algorithms have received.  **Do not use in production**
without independent security evaluation.

---

## License

MIT © Bajpai Labs
