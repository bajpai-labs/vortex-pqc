"""VORTEX-256 Core API.

Dispatches to the compiled C extension (_native) when available;
falls back to the pure-Python reference implementation (_pure) so
the package is always installable without a C compiler.
"""

from __future__ import annotations

from typing import NamedTuple

from .params import (
    CIPHERTEXT_BYTES,
    PRIVATE_KEY_BYTES,
    PUBLIC_KEY_BYTES,
    SHARED_SECRET_BYTES,
)


class SecurityError(Exception):
    """Raised when a cryptographic integrity check fails."""


class VortexKeyPair(NamedTuple):
    """A VORTEX-256 key pair."""
    public_key:  bytes
    private_key: bytes


class Ciphertext(NamedTuple):
    """VORTEX-256 ciphertext together with the encapsulated shared secret."""
    data:          bytes
    shared_secret: bytes


# ── Backend selection ──────────────────────────────────────────────────────
try:
    from . import _native as _be  # type: ignore[attr-defined]
    _BACKEND = "vortex-pqc-native"
except ImportError:
    from . import _pure as _be  # type: ignore[assignment]
    _BACKEND = "vortex-pqc-pure-python"


def native_backend() -> str:
    """Return the name of the active backend."""
    try:
        return str(_be.backend_name())   # C extension provides this
    except AttributeError:
        return _BACKEND


def generate_keypair() -> VortexKeyPair:
    """Generate a fresh VORTEX-256 key pair."""
    pk, sk = _be.keypair()
    return VortexKeyPair(pk, sk)


def encapsulate(public_key: bytes) -> Ciphertext:
    """Encapsulate a shared secret to *public_key*.

    Returns a :class:`Ciphertext` containing the ciphertext bytes and the
    derived shared secret.
    """
    if len(public_key) != PUBLIC_KEY_BYTES:
        raise ValueError(
            f"Invalid public key length: "
            f"expected {PUBLIC_KEY_BYTES}, got {len(public_key)}"
        )
    ct, ss = _be.encapsulate(public_key)
    return Ciphertext(ct, ss)


def decapsulate(ciphertext: bytes, private_key: bytes) -> bytes:
    """Recover the shared secret from *ciphertext* using *private_key*.

    Returns 32 bytes.  On ciphertext tampering the scheme performs implicit
    rejection (returns a pseudorandom value derived from the private key's
    rejection token *z*) so the function never raises on invalid ciphertexts —
    it silently returns a different shared secret.
    """
    if len(ciphertext) != CIPHERTEXT_BYTES:
        raise ValueError(
            f"Invalid ciphertext length: "
            f"expected {CIPHERTEXT_BYTES}, got {len(ciphertext)}"
        )
    if len(private_key) != PRIVATE_KEY_BYTES:
        raise ValueError(
            f"Invalid private key length: "
            f"expected {PRIVATE_KEY_BYTES}, got {len(private_key)}"
        )
    try:
        return _be.decapsulate(ciphertext, private_key)
    except RuntimeError as exc:
        raise SecurityError("Decapsulation failed") from exc
