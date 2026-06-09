"""VORTEX-256 scheme parameters and derived size constants.

VORTEX-256 is a novel Key Encapsulation Mechanism based on the
Rotational Module Learning With Errors (RotMLWE) problem.

Ring:      R_q = Z_{3329}[x] / (x^{256} + 1)
Automorphism: σ(f(x)) = f(x^3 mod (x^{256}+1))
Module rank: K = 2 rotational instances

Key insight: the public matrix is replaced by K Frobenius rotations
of a SINGLE base element a, giving identical sizes to Kyber-512 but
a fundamentally different algebraic hardness assumption.
"""

N: int = 256      # Ring dimension
Q: int = 3329     # Prime modulus (same as ML-KEM, enabling NTT reuse)
K: int = 2        # Number of Frobenius rotation instances

ETA1: int = 3     # Noise bound for secret / keygen errors
ETA2: int = 2     # Noise bound for encapsulation errors

DU: int = 10      # Ciphertext compression bits per u-coefficient
DV: int = 4       # Ciphertext compression bits per v-coefficient

# ── Derived byte counts ────────────────────────────────────────────────────
_POLY_BYTES: int        = N * 12 // 8    # 384  – uncompressed 12-bit poly
_POLY_COMPRESSED_U: int = N * DU // 8   # 320  – compressed u poly (10-bit)
_POLY_COMPRESSED_V: int = N * DV // 8   # 128  – compressed v poly (4-bit)

#  pk  = ρ-seed (32) + K × packed_b (K×384)      → 800 bytes  (= Kyber-512 pk)
#  sk  = packed_s (384) + pk (800) + H(pk) (32) + z (32)  → 1248 bytes
#  ct  = K × compressed_u (K×320) + compressed_v (128)   → 768 bytes  (= Kyber-512 ct)
PUBLIC_KEY_BYTES:    int = 32 + K * _POLY_BYTES                      # 800
PRIVATE_KEY_BYTES:   int = _POLY_BYTES + PUBLIC_KEY_BYTES + 32 + 32  # 1248
CIPHERTEXT_BYTES:    int = K * _POLY_COMPRESSED_U + _POLY_COMPRESSED_V  # 768
SHARED_SECRET_BYTES: int = 32
