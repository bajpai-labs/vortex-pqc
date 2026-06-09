"""Pure-Python reference implementation of VORTEX-256.

All arithmetic is performed in the ring  R_q = Z_{3329}[x] / (x^{256}+1).

Novel primitive: RotMLWE (Rotational Module Learning With Errors)
─────────────────────────────────────────────────────────────────
Standard MLWE uses a k×k matrix A and a secret vector s ∈ R_q^k.
VORTEX-256 replaces A with K Frobenius rotations of a SINGLE ring
element a:

    a₀ = a,   a₁ = σ(a) = a(x³ mod x²⁵⁶+1),  …

Secret: a single s ∈ R_q   (not a vector)
Public: ρ (seed) + {bᵢ = aᵢ·s + eᵢ  for i = 0…K-1}

Encapsulation & correctness
───────────────────────────
  uᵢ = aᵢ·r + e′ᵢ
  v  = Σᵢ bᵢ·r + e″ + encode(m)

Decapsulation noise cancellation:
  v − Σᵢ s·uᵢ
    = Σᵢ(aᵢ·s + eᵢ)·r + e″ + enc(m) − Σᵢ s·(aᵢ·r + e′ᵢ)
    = Σᵢ eᵢ·r − Σᵢ s·e′ᵢ + e″ + enc(m)
    ≈ enc(m)   (noise is small relative to Q/4 = 832)

Security note
─────────────
RotMLWE is at least as hard as RLWE (K=1 case). For K>1 the K
correlated instances share the SAME base a, so an attacker gets
K equations sharing common structure — a new hard problem. Breaking
RotMLWE would require simultaneously exploiting all K Frobenius-
related instances; no sub-exponential attack is currently known.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import List, Tuple

from .params import (
    CIPHERTEXT_BYTES,
    ETA1,
    ETA2,
    K,
    N,
    PRIVATE_KEY_BYTES,
    PUBLIC_KEY_BYTES,
    Q,
    SHARED_SECRET_BYTES,
    _POLY_BYTES,
    _POLY_COMPRESSED_U,
    _POLY_COMPRESSED_V,
    DU,
    DV,
)

# A polynomial in R_q is represented as a list of N ints in [0, Q).
Poly = List[int]


# ─────────────────────────── Polynomial arithmetic ────────────────────────

def _poly_add(a: Poly, b: Poly) -> Poly:
    return [(a[i] + b[i]) % Q for i in range(N)]


def _poly_sub(a: Poly, b: Poly) -> Poly:
    return [(a[i] - b[i]) % Q for i in range(N)]


def _poly_mul(a: Poly, b: Poly) -> Poly:
    """Schoolbook multiplication in Z_Q[x]/(x^N+1).  O(N²) — correct, not fast."""
    acc = [0] * N
    for i in range(N):
        ai = a[i]
        if ai == 0:
            continue
        for j in range(N):
            k = i + j
            if k < N:
                acc[k] += ai * b[j]
            else:
                acc[k - N] -= ai * b[j]
    return [v % Q for v in acc]


def _frobenius(a: Poly) -> Poly:
    """Apply σ: x ↦ x³, computing f(x³) mod (x^{256}+1).

    For coefficient aᵢ at position i:
      x^{3i} mod (x^{256}+1):
        if 3i mod 512 < 256  → coeff at (3i mod 512)  contributes +aᵢ
        if 3i mod 512 ≥ 256  → coeff at (3i mod 512 − 256) contributes −aᵢ
    This is a ring automorphism because gcd(3, 512) = 1.
    """
    r = [0] * N
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        k = (3 * i) & 511        # (3·i) mod 512  (512 = 2N, period of x^{2N}=1)
        if k < N:
            r[k] = (r[k] + ai) % Q
        else:
            r[k - N] = (r[k - N] - ai) % Q
    return r


# ──────────────────────── Sampling / PRF ──────────────────────────────────

def _prf(seed: bytes, nonce: int, length: int) -> bytes:
    """SHAKE-256(seed ‖ nonce) → `length` bytes."""
    return hashlib.shake_256(seed + bytes([nonce])).digest(length)


def _cbd(eta: int, seed: bytes, nonce: int) -> Poly:
    """Sample a polynomial from the Centred Binomial Distribution CBD(eta).

    Each coefficient = Σ_{j<eta} a_j − Σ_{j<eta} b_j  where all bits from SHAKE-256.
    Total bits needed: 2·eta·N = 2·eta·256.  Byte count: eta·N//4.
    """
    buf = _prf(seed, nonce, eta * N // 4)
    bits = int.from_bytes(buf, "little")
    step = 2 * eta
    result: Poly = []
    for i in range(N):
        base = step * i
        a_sum = sum((bits >> (base + j)) & 1 for j in range(eta))
        b_sum = sum((bits >> (base + eta + j)) & 1 for j in range(eta))
        result.append((a_sum - b_sum) % Q)
    return result


def _gen_base(rho: bytes) -> Poly:
    """Expand 32-byte seed ρ to a uniform element of R_q via SHAKE-128.

    Uses rejection sampling identical to ML-KEM's XOF: each 3 bytes yield
    two 12-bit candidates; accept iff < Q = 3329.  With 672 input bytes the
    expected number of candidates is ~364, far above the required 256.
    """
    buf = hashlib.shake_128(rho + b"\x00\x00").digest(672)
    result: List[int] = []
    idx = 0
    while idx + 3 <= len(buf) and len(result) < N:
        d1 = buf[idx] | ((buf[idx + 1] & 0x0F) << 8)
        d2 = (buf[idx + 1] >> 4) | (buf[idx + 2] << 4)
        idx += 3
        if d1 < Q:
            result.append(d1)
        if d2 < Q and len(result) < N:
            result.append(d2)
    if len(result) < N:             # statistically impossible but defensive
        raise RuntimeError("XOF failed to produce enough samples")
    return result[:N]


def _gen_rotations(rho: bytes) -> List[Poly]:
    """Return [a, σ(a), σ²(a), …] of length K from seed ρ.

    Key efficiency gain: Kyber needs K² XOF calls to fill matrix A;
    VORTEX needs only 1 XOF call then K−1 cheap Frobenius permutations.
    """
    a = _gen_base(rho)
    polys = [a]
    for _ in range(K - 1):
        a = _frobenius(a)
        polys.append(a)
    return polys


# ───────────────────── Message encode / decode ────────────────────────────

def _encode_msg(m: bytes) -> Poly:
    """Map 32-byte message to poly: bit j → coefficient j ∈ {0, Q//2}."""
    r = [0] * N
    for i in range(N):
        r[i] = ((m[i >> 3] >> (i & 7)) & 1) * (Q >> 1)
    return r


def _decode_msg(poly: Poly) -> bytes:
    """Round each coefficient to nearest {0, Q//2} → pack to 32 bytes."""
    m = bytearray(32)
    lo, hi = Q >> 2, 3 * (Q >> 2)     # Q/4 = 832, 3Q/4 = 2496
    for i in range(N):
        c = poly[i] % Q
        if lo < c < hi:
            m[i >> 3] |= 1 << (i & 7)
    return bytes(m)


# ──────────────────────── Packing / unpacking ─────────────────────────────

def _pack12(poly: Poly) -> bytes:
    """Pack 256 12-bit coefficients into 384 bytes (2 coeffs per 3 bytes)."""
    r = bytearray(384)
    for i in range(128):
        a = poly[2 * i]     & 0xFFF
        b = poly[2 * i + 1] & 0xFFF
        r[3 * i]     =  a & 0xFF
        r[3 * i + 1] = (a >> 8) | ((b & 0xF) << 4)
        r[3 * i + 2] =  b >> 4
    return bytes(r)


def _unpack12(data: bytes) -> Poly:
    """Unpack 384 bytes into 256 12-bit coefficients."""
    poly: Poly = []
    for i in range(128):
        a = data[3 * i] | ((data[3 * i + 1] & 0xF) << 8)
        b = (data[3 * i + 1] >> 4) | (data[3 * i + 2] << 4)
        poly.append(a)
        poly.append(b)
    return poly


def _compress_c(x: int, d: int) -> int:
    """round(x · 2^d / Q) mod 2^d."""
    return ((x * (1 << d) + Q // 2) // Q) & ((1 << d) - 1)


def _decompress_c(y: int, d: int) -> int:
    """round(y · Q / 2^d)."""
    return (y * Q + (1 << (d - 1))) >> d


def _pack_u(poly: Poly) -> bytes:
    """Compress (DU=10 bits/coeff) and pack u-polynomial → 320 bytes.

    Layout: 4 coefficients × 10 bits = 40 bits = 5 bytes per group.
    """
    r = bytearray(_POLY_COMPRESSED_U)
    for i in range(64):
        a = _compress_c(poly[4 * i]     % Q, DU)
        b = _compress_c(poly[4 * i + 1] % Q, DU)
        c = _compress_c(poly[4 * i + 2] % Q, DU)
        d = _compress_c(poly[4 * i + 3] % Q, DU)
        r[5 * i]     =  a & 0xFF
        r[5 * i + 1] = ((a >> 8) & 0x3) | ((b & 0x3F) << 2)
        r[5 * i + 2] = ((b >> 6) & 0xF) | ((c & 0x0F) << 4)
        r[5 * i + 3] = ((c >> 4) & 0x3F) | ((d & 0x03) << 6)
        r[5 * i + 4] = (d >> 2) & 0xFF
    return bytes(r)


def _unpack_u(data: bytes) -> Poly:
    """Unpack and decompress u-polynomial from 320 bytes."""
    poly: Poly = []
    for i in range(64):
        b0, b1, b2, b3, b4 = (
            data[5 * i], data[5 * i + 1], data[5 * i + 2],
            data[5 * i + 3], data[5 * i + 4],
        )
        poly.append(_decompress_c( b0          | ((b1 & 0x03) << 8), DU))
        poly.append(_decompress_c((b1 >> 2)    | ((b2 & 0x0F) << 6), DU))
        poly.append(_decompress_c((b2 >> 4)    | ((b3 & 0x3F) << 4), DU))
        poly.append(_decompress_c((b3 >> 6)    | ( b4         << 2), DU))
    return poly


def _pack_v(poly: Poly) -> bytes:
    """Compress (DV=4 bits/coeff) and pack v-polynomial → 128 bytes."""
    r = bytearray(_POLY_COMPRESSED_V)
    for i in range(128):
        a = _compress_c(poly[2 * i]     % Q, DV)
        b = _compress_c(poly[2 * i + 1] % Q, DV)
        r[i] = (a & 0xF) | ((b & 0xF) << 4)
    return bytes(r)


def _unpack_v(data: bytes) -> Poly:
    """Unpack and decompress v-polynomial from 128 bytes."""
    poly: Poly = []
    for byte in data:
        poly.append(_decompress_c(byte & 0xF, DV))
        poly.append(_decompress_c(byte >> 4,  DV))
    return poly


# ──────────────── Hash / KDF wrappers (FIPS 202) ──────────────────────────

def _H(data: bytes) -> bytes:
    """SHA3-256."""
    return hashlib.sha3_256(data).digest()


def _G(data: bytes) -> bytes:
    """SHA3-512 → 64 bytes; split into (K_bar, coins) = (32, 32)."""
    return hashlib.sha3_512(data).digest()


def _KDF(data: bytes) -> bytes:
    """SHAKE-256 → 32 bytes shared secret."""
    return hashlib.shake_256(data).digest(SHARED_SECRET_BYTES)


# ─────────────────────── VORTEX-256 KEM ──────────────────────────────────

def keypair() -> Tuple[bytes, bytes]:
    """Generate a VORTEX-256 key pair (pk, sk).

    KeyGen:
      1. Sample ρ, σ ← random(32)
      2. a₀ = XOF(ρ);  aᵢ = σⁱ(a₀)  for i=1…K-1
      3. s ← CBD(ETA1, σ, 0)
      4. bᵢ = aᵢ·s + eᵢ   where eᵢ ← CBD(ETA1, σ, i+1)
      5. pk = ρ ‖ pack(b₀) ‖ … ‖ pack(b_{K-1})
      6. sk = pack(s) ‖ pk ‖ SHA3-256(pk) ‖ z
    """
    rho   = os.urandom(32)
    sigma = os.urandom(32)

    a_list = _gen_rotations(rho)
    s      = _cbd(ETA1, sigma, 0)

    b_parts: List[bytes] = []
    for i, ai in enumerate(a_list):
        ei = _cbd(ETA1, sigma, i + 1)
        bi = _poly_add(_poly_mul(ai, s), ei)
        b_parts.append(_pack12(bi))

    pk  = rho + b"".join(b_parts)
    pkh = _H(pk)
    z   = os.urandom(32)
    sk  = _pack12(s) + pk + pkh + z
    return pk, sk


def encapsulate(pk: bytes) -> Tuple[bytes, bytes]:
    """Encapsulate a shared secret against public key pk.

    Returns (ciphertext, shared_secret).

    Encaps:
      1. m ← random(32)
      2. (K̄, coins) = SHA3-512(m ‖ H(pk))
      3. r ← CBD(ETA1, coins, 0)
      4. uᵢ = aᵢ·r + e′ᵢ   (e′ᵢ ← CBD(ETA2, coins, i+1))
      5. v  = Σᵢ bᵢ·r + e″ + encode(m)   (e″ ← CBD(ETA2, coins, K+1))
      6. ct = compress(u₀) ‖ … ‖ compress(u_{K-1}) ‖ compress(v)
      7. K  = SHAKE-256(K̄ ‖ SHA3-256(ct))
    """
    rho    = pk[:32]
    b_list = [
        _unpack12(pk[32 + i * _POLY_BYTES: 32 + (i + 1) * _POLY_BYTES])
        for i in range(K)
    ]
    pkh = _H(pk)
    m   = os.urandom(32)

    h      = _G(m + pkh)
    K_bar  = h[:32]
    coins  = h[32:]

    r      = _cbd(ETA1, coins, 0)
    a_list = _gen_rotations(rho)

    u_parts: List[bytes] = []
    for i, ai in enumerate(a_list):
        ep = _cbd(ETA2, coins, i + 1)
        ui = _poly_add(_poly_mul(ai, r), ep)
        u_parts.append(_pack_u(ui))

    epp = _cbd(ETA2, coins, K + 1)
    v   = epp[:]
    for bi in b_list:
        v = _poly_add(v, _poly_mul(bi, r))
    v = _poly_add(v, _encode_msg(m))

    ct = b"".join(u_parts) + _pack_v(v)
    ss = _KDF(K_bar + _H(ct))
    return ct, ss


def decapsulate(ct: bytes, sk: bytes) -> bytes:
    """Recover shared secret from ciphertext and private key.

    Decaps:
      1. Decompress uᵢ, v from ct
      2. w = v − Σᵢ s·uᵢ  ≈ encode(m′)
      3. m′ = decode(w)
      4. Re-encapsulate deterministically with m′ → ct′
      5. Implicit rejection: K = KDF(K̄′ ‖ H(ct)) if ct′=ct
                                   KDF(z   ‖ H(ct)) otherwise
    """
    s      = _unpack12(sk[: _POLY_BYTES])
    pk     = sk[_POLY_BYTES: _POLY_BYTES + PUBLIC_KEY_BYTES]
    pkh    = sk[_POLY_BYTES + PUBLIC_KEY_BYTES: _POLY_BYTES + PUBLIC_KEY_BYTES + 32]
    z      = sk[_POLY_BYTES + PUBLIC_KEY_BYTES + 32:]
    rho    = pk[:32]
    b_list = [
        _unpack12(pk[32 + i * _POLY_BYTES: 32 + (i + 1) * _POLY_BYTES])
        for i in range(K)
    ]

    u_list = [
        _unpack_u(ct[i * _POLY_COMPRESSED_U: (i + 1) * _POLY_COMPRESSED_U])
        for i in range(K)
    ]
    v = _unpack_v(ct[K * _POLY_COMPRESSED_U:])

    # Recover approximate message: v − Σᵢ s·uᵢ
    w = v[:]
    for ui in u_list:
        w = _poly_sub(w, _poly_mul(s, ui))
    m_prime = _decode_msg(w)

    # Deterministic re-encapsulation
    h_prime  = _G(m_prime + pkh)
    K_bar_p  = h_prime[:32]
    coins_p  = h_prime[32:]

    r_p    = _cbd(ETA1, coins_p, 0)
    a_list = _gen_rotations(rho)

    u_parts: List[bytes] = []
    for i, ai in enumerate(a_list):
        ep = _cbd(ETA2, coins_p, i + 1)
        ui = _poly_add(_poly_mul(ai, r_p), ep)
        u_parts.append(_pack_u(ui))

    epp_p = _cbd(ETA2, coins_p, K + 1)
    v_p   = epp_p[:]
    for bi in b_list:
        v_p = _poly_add(v_p, _poly_mul(bi, r_p))
    v_p = _poly_add(v_p, _encode_msg(m_prime))

    ct_p    = b"".join(u_parts) + _pack_v(v_p)
    ct_hash = _H(ct)

    # Constant-time conditional: hmac.compare_digest is time-safe
    if hmac.compare_digest(ct_p, ct):
        return _KDF(K_bar_p + ct_hash)
    return _KDF(z + ct_hash)
