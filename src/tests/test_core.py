"""VORTEX-256 core correctness tests."""

import pytest

from vortex_pqc import (
    CIPHERTEXT_BYTES,
    PRIVATE_KEY_BYTES,
    PUBLIC_KEY_BYTES,
    SHARED_SECRET_BYTES,
    SecurityError,
    decapsulate,
    encapsulate,
    generate_keypair,
    native_backend,
)


# ── Smoke tests ───────────────────────────────────────────────────────────

def test_backend_name_is_string():
    assert isinstance(native_backend(), str)
    assert len(native_backend()) > 0


def test_keypair_byte_lengths():
    kp = generate_keypair()
    assert len(kp.public_key)  == PUBLIC_KEY_BYTES,  "wrong public key size"
    assert len(kp.private_key) == PRIVATE_KEY_BYTES, "wrong private key size"


def test_encapsulate_byte_lengths():
    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    assert len(ct.data)          == CIPHERTEXT_BYTES,    "wrong ciphertext size"
    assert len(ct.shared_secret) == SHARED_SECRET_BYTES, "wrong shared secret size"


# ── Correctness: encrypt-then-decrypt ────────────────────────────────────

def test_round_trip_basic():
    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    ss = decapsulate(ct.data, kp.private_key)
    assert ss == ct.shared_secret, "shared secrets do not match"


def test_round_trip_ten_times():
    for _ in range(10):
        kp = generate_keypair()
        ct = encapsulate(kp.public_key)
        ss = decapsulate(ct.data, kp.private_key)
        assert ss == ct.shared_secret, "decapsulation mismatch"


def test_shared_secret_is_32_bytes():
    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    ss = decapsulate(ct.data, kp.private_key)
    assert len(ss) == 32


# ── IND-CCA2 / implicit rejection ─────────────────────────────────────────

def test_tampered_ciphertext_gives_different_secret():
    """Bit-flipping the ciphertext must produce a different (random-looking) secret."""
    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    tampered = bytes(b ^ 0x01 for b in ct.data[:32]) + ct.data[32:]
    ss_bad   = decapsulate(tampered, kp.private_key)
    assert ss_bad != ct.shared_secret, "implicit rejection failed"


def test_wrong_private_key_gives_different_secret():
    kp1 = generate_keypair()
    kp2 = generate_keypair()
    ct  = encapsulate(kp1.public_key)
    ss1 = decapsulate(ct.data, kp1.private_key)
    ss2 = decapsulate(ct.data, kp2.private_key)
    assert ss1 != ss2


def test_encap_is_probabilistic():
    """Two encapsulations of the same pk must differ."""
    kp  = generate_keypair()
    ct1 = encapsulate(kp.public_key)
    ct2 = encapsulate(kp.public_key)
    assert ct1.data != ct2.data
    assert ct1.shared_secret != ct2.shared_secret


# ── Input validation ──────────────────────────────────────────────────────

def test_encapsulate_wrong_pk_length():
    with pytest.raises(ValueError, match="public key"):
        encapsulate(b"\x00" * (PUBLIC_KEY_BYTES - 1))


def test_decapsulate_wrong_ct_length():
    kp = generate_keypair()
    with pytest.raises(ValueError, match="ciphertext"):
        decapsulate(b"\x00" * (CIPHERTEXT_BYTES - 1), kp.private_key)


def test_decapsulate_wrong_sk_length():
    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    with pytest.raises(ValueError, match="private key"):
        decapsulate(ct.data, b"\x00" * (PRIVATE_KEY_BYTES - 1))


# ── Determinism given same coins (re-encapsulation property) ─────────────

def test_pure_decap_deterministic():
    """Decapsulation is deterministic: same inputs → same output."""
    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    ss_a = decapsulate(ct.data, kp.private_key)
    ss_b = decapsulate(ct.data, kp.private_key)
    assert ss_a == ss_b


# ── RotMLWE parameter sanity checks ──────────────────────────────────────

def test_public_key_seed_is_deterministic_portion():
    """First 32 bytes of pk (seed ρ) should differ across key pairs."""
    seeds = {generate_keypair().public_key[:32] for _ in range(5)}
    assert len(seeds) == 5, "seeds must be uniformly random"


def test_private_key_contains_public_key():
    """Private key format: pack(s) | pk | H(pk) | z."""
    from vortex_pqc.params import _POLY_BYTES, PUBLIC_KEY_BYTES
    kp   = generate_keypair()
    pk_embedded = kp.private_key[_POLY_BYTES: _POLY_BYTES + PUBLIC_KEY_BYTES]
    assert pk_embedded == kp.public_key, "pk not embedded in sk"
