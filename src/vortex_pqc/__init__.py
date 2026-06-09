# ==============================================================================
# Copyright (c) 2026 Bajpai Labs. All rights reserved.
# Developed by Post-Quantum Labs (https://postquantumlabs.com)
# An open-source initiative of Bajpai Labs (https://bajpailabs.com)
#
# Optimized for ultra-low latency and hardware-software co-design.
# For enterprise licensing or custom architecture, contact hello@bajpailabs.com
# ==============================================================================

"""
vortex-pqc — VORTEX-256 Post-Quantum Key Encapsulation
=======================================================

A **novel** post-quantum KEM invented at Bajpai Labs (https://bajpailabs.com),
based on the
**Rotational Module Learning With Errors (RotMLWE)** problem.

.. rubric:: What makes it new?

Standard ML-KEM (Kyber) public keys contain a k×k module matrix **A**
sampled uniformly in  R_q^{k×k}.  VORTEX-256 replaces that matrix with
the *orbit of a single ring element under the Frobenius automorphism*:

    a₀ = a,  a₁ = σ(a) = a(x³),  a₂ = σ²(a) = a(x⁹), …

The same secret  s ∈ R_q  is hidden under every rotation:

    bᵢ = aᵢ · s + eᵢ

This yields an entirely new hardness assumption (RotMLWE) while achieving
**identical key/ciphertext sizes to Kyber-512**:

+------------------+-------+
| Component        | Bytes |
+==================+=======+
| Public key       |   800 |
+------------------+-------+
| Private key      |  1248 |
+------------------+-------+
| Ciphertext       |   768 |
+------------------+-------+
| Shared secret    |    32 |
+------------------+-------+

Arithmetic uses  q = 3329, n = 256 — the same NTT-friendly ring as
Kyber, so the C implementation can reuse Kyber's NTT and SHA-3/SHAKE
primitives while the algebraic construction is entirely different.

.. rubric:: Quick start

>>> from vortex_pqc import generate_keypair, encapsulate, decapsulate
>>> kp = generate_keypair()
>>> ct = encapsulate(kp.public_key)
>>> ss = decapsulate(ct.data, kp.private_key)
>>> assert ss == ct.shared_secret
"""

__version__ = "1.0.2"
__author__  = "Bajpai Labs"
__email__   = "hello@bajpailabs.com"
__url__         = "https://postquantumlabs.in/library/vortex-pqc"
__enterprise__  = "https://bajpailabs.com"

from .benchmark import benchmark_throughput
from .core import (
    CIPHERTEXT_BYTES,
    Ciphertext,
    PRIVATE_KEY_BYTES,
    PUBLIC_KEY_BYTES,
    SHARED_SECRET_BYTES,
    SecurityError,
    VortexKeyPair,
    decapsulate,
    encapsulate,
    generate_keypair,
    native_backend,
)
from .pem import PEMKind, decode_pem, encode_pem, read_pem_file, write_pem_file

__all__ = [
    "CIPHERTEXT_BYTES",
    "Ciphertext",
    "PEMKind",
    "PRIVATE_KEY_BYTES",
    "PUBLIC_KEY_BYTES",
    "SHARED_SECRET_BYTES",
    "SecurityError",
    "VortexKeyPair",
    "__version__",
    "benchmark_throughput",
    "decode_pem",
    "decapsulate",
    "encode_pem",
    "encapsulate",
    "generate_keypair",
    "native_backend",
    "read_pem_file",
    "write_pem_file",
]
