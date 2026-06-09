"""Standard Base64 PEM serialization for VORTEX-256 key material.

PEM blocks use RFC 4716 style headers:

    -----BEGIN VORTEX256 PUBLIC KEY-----
    <base64 encoded bytes, 64 chars per line>
    -----END VORTEX256 PUBLIC KEY-----

The encoding uses Base64 (not hex) for compatibility with OpenSSL tooling
and standard PEM parsers.  Files written by :func:`write_pem_file` receive
permissions 0o600 (owner read/write only).
"""

from __future__ import annotations

import base64
import re
from enum import Enum
from pathlib import Path
from typing import Union

from .params import (
    CIPHERTEXT_BYTES,
    PRIVATE_KEY_BYTES,
    PUBLIC_KEY_BYTES,
    SHARED_SECRET_BYTES,
)

PEM_LINE_WIDTH = 64


class PEMKind(str, Enum):
    PUBLIC_KEY    = "PUBLIC KEY"
    PRIVATE_KEY   = "PRIVATE KEY"
    CIPHERTEXT    = "CIPHERTEXT"
    SHARED_SECRET = "SHARED SECRET"


_EXPECTED_BYTES: dict[PEMKind, int] = {
    PEMKind.PUBLIC_KEY:    PUBLIC_KEY_BYTES,
    PEMKind.PRIVATE_KEY:   PRIVATE_KEY_BYTES,
    PEMKind.CIPHERTEXT:    CIPHERTEXT_BYTES,
    PEMKind.SHARED_SECRET: SHARED_SECRET_BYTES,
}


def _header(kind: PEMKind) -> str:
    return f"-----BEGIN VORTEX256 {kind.value}-----"


def _footer(kind: PEMKind) -> str:
    return f"-----END VORTEX256 {kind.value}-----"


def encode_pem(kind: PEMKind, data: bytes) -> str:
    """Encode *data* as a VORTEX256 PEM block.

    Raises :class:`ValueError` if *data* has the wrong length for *kind*.
    """
    expected = _EXPECTED_BYTES[kind]
    if len(data) != expected:
        raise ValueError(
            f"invalid data length for {kind.value}: "
            f"expected {expected}, got {len(data)}"
        )
    b64 = base64.b64encode(data).decode("ascii")
    lines = [b64[i: i + PEM_LINE_WIDTH] for i in range(0, len(b64), PEM_LINE_WIDTH)]
    return "\n".join([_header(kind), *lines, _footer(kind), ""])


def decode_pem(kind: PEMKind, pem: str) -> bytes:
    """Decode a VORTEX256 PEM block back to raw bytes.

    Raises :class:`ValueError` on missing / malformed / wrong-kind blocks.
    """
    expected = _EXPECTED_BYTES[kind]
    begin    = re.escape(_header(kind))
    end      = re.escape(_footer(kind))
    match    = re.search(
        rf"{begin}\s*([A-Za-z0-9+/=\s]+?)\s*{end}",
        pem,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"missing or invalid PEM block for {kind.value}")
    body = re.sub(r"\s+", "", match.group(1))
    try:
        decoded = base64.b64decode(body, validate=True)
    except Exception as exc:
        raise ValueError(f"invalid Base64 payload for {kind.value}") from exc
    if len(decoded) != expected:
        raise ValueError(
            f"invalid decoded length for {kind.value}: "
            f"expected {expected}, got {len(decoded)}"
        )
    return decoded


def write_pem_file(
    path: Union[str, Path],
    kind: PEMKind,
    data: bytes,
) -> None:
    """Write *data* as a VORTEX256 PEM file at *path* with mode 0o600."""
    p = Path(path)
    p.write_text(encode_pem(kind, data), encoding="utf-8")
    p.chmod(0o600)


def read_pem_file(path: Union[str, Path], kind: PEMKind) -> bytes:
    """Read and decode a VORTEX256 PEM file."""
    return decode_pem(kind, Path(path).read_text(encoding="utf-8"))
