"""PEM serialization tests for VORTEX-256."""

import tempfile
from pathlib import Path

import pytest

from vortex_pqc import (
    CIPHERTEXT_BYTES,
    PRIVATE_KEY_BYTES,
    PUBLIC_KEY_BYTES,
    SHARED_SECRET_BYTES,
    PEMKind,
    decode_pem,
    encode_pem,
    encapsulate,
    generate_keypair,
    read_pem_file,
    write_pem_file,
)


# ── Encode / decode round-trips ───────────────────────────────────────────

def test_public_key_pem_round_trip():
    kp  = generate_keypair()
    pem = encode_pem(PEMKind.PUBLIC_KEY, kp.public_key)
    assert "-----BEGIN VORTEX256 PUBLIC KEY-----" in pem
    assert "-----END VORTEX256 PUBLIC KEY-----" in pem
    assert decode_pem(PEMKind.PUBLIC_KEY, pem) == kp.public_key


def test_private_key_pem_round_trip():
    kp  = generate_keypair()
    pem = encode_pem(PEMKind.PRIVATE_KEY, kp.private_key)
    assert "-----BEGIN VORTEX256 PRIVATE KEY-----" in pem
    assert decode_pem(PEMKind.PRIVATE_KEY, pem) == kp.private_key


def test_ciphertext_pem_round_trip():
    kp  = generate_keypair()
    ct  = encapsulate(kp.public_key)
    pem = encode_pem(PEMKind.CIPHERTEXT, ct.data)
    assert "-----BEGIN VORTEX256 CIPHERTEXT-----" in pem
    assert decode_pem(PEMKind.CIPHERTEXT, pem) == ct.data


def test_shared_secret_pem_round_trip():
    kp  = generate_keypair()
    ct  = encapsulate(kp.public_key)
    pem = encode_pem(PEMKind.SHARED_SECRET, ct.shared_secret)
    assert "VORTEX256 SHARED SECRET" in pem
    assert decode_pem(PEMKind.SHARED_SECRET, pem) == ct.shared_secret


# ── File I/O ──────────────────────────────────────────────────────────────

def test_write_read_pem_file_public():
    kp = generate_keypair()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "pub.pem"
        write_pem_file(p, PEMKind.PUBLIC_KEY, kp.public_key)
        assert read_pem_file(p, PEMKind.PUBLIC_KEY) == kp.public_key


def test_write_read_pem_file_private():
    kp = generate_keypair()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "key.pem"
        write_pem_file(p, PEMKind.PRIVATE_KEY, kp.private_key)
        assert read_pem_file(p, PEMKind.PRIVATE_KEY) == kp.private_key


def test_private_key_file_mode_is_600():
    kp = generate_keypair()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "key.pem"
        write_pem_file(p, PEMKind.PRIVATE_KEY, kp.private_key)
        mode = oct(p.stat().st_mode)
        assert mode.endswith("600"), f"expected mode 600, got {mode}"


# ── Validation ────────────────────────────────────────────────────────────

def test_encode_wrong_length_raises():
    with pytest.raises(ValueError, match="invalid data length"):
        encode_pem(PEMKind.PUBLIC_KEY, b"\x00" * (PUBLIC_KEY_BYTES - 1))


def test_decode_wrong_kind_raises():
    kp  = generate_keypair()
    pem = encode_pem(PEMKind.PUBLIC_KEY, kp.public_key)
    with pytest.raises(ValueError):
        decode_pem(PEMKind.PRIVATE_KEY, pem)


def test_decode_truncated_b64_raises():
    kp  = generate_keypair()
    pem = encode_pem(PEMKind.PUBLIC_KEY, kp.public_key)
    broken = pem.replace(pem[40:80], "????")
    with pytest.raises(ValueError):
        decode_pem(PEMKind.PUBLIC_KEY, broken)


# ── PEM is standard Base64, compatible with external tooling ─────────────

def test_pem_uses_base64_not_hex():
    import base64
    kp   = generate_keypair()
    pem  = encode_pem(PEMKind.PUBLIC_KEY, kp.public_key)
    lines = [
        ln for ln in pem.splitlines()
        if ln and not ln.startswith("-----")
    ]
    body  = "".join(lines)
    # Must decode cleanly as standard base64
    decoded = base64.b64decode(body)
    assert decoded == kp.public_key
