# PEM Format Specification

VORTEX-256 defines a PEM encoding for keys, ciphertexts, and shared secrets.
The format follows RFC 7468 conventions with project-specific labels.

---

## Design goals

1. **Standard Base64** — compatible with OpenSSL, `openssl base64`, and generic PEM parsers
2. **Explicit labels** — `VORTEX256` prefix prevents confusion with RSA/EC/X.509 PEM
3. **Fixed sizes** — each PEM kind maps to an exact byte length
4. **Secure file permissions** — `write_pem_file` sets mode `0o600` on private material

---

## Block structure

```
-----BEGIN VORTEX256 <KIND>-----
<base64 body, 64 characters per line>
-----END VORTEX256 <KIND>-----
```

Trailing newline after the footer is optional but recommended.

---

## Supported kinds

| `PEMKind` | BEGIN label | Raw bytes |
|-----------|-------------|----------:|
| `PUBLIC_KEY` | `VORTEX256 PUBLIC KEY` | 800 |
| `PRIVATE_KEY` | `VORTEX256 PRIVATE KEY` | 1248 |
| `CIPHERTEXT` | `VORTEX256 CIPHERTEXT` | 768 |
| `SHARED_SECRET` | `VORTEX256 SHARED SECRET` | 32 |

---

## Encoding rules

1. Raw binary data is encoded with standard Base64 (RFC 4648, no URL-safe alphabet).
2. Lines are wrapped at **64 characters** (configurable via `PEM_LINE_WIDTH = 64`).
3. Whitespace (spaces, newlines) in the body is ignored during decoding.
4. Decoded length must exactly match the expected size for the kind; otherwise
   `ValueError` is raised.

---

## Example: private key

```
-----BEGIN VORTEX256 PRIVATE KEY-----
AQDQABAAABAAAA0AAAAAAPDP/gzQAhAAAAAAAA3QAA0AAPDPAQAAASAAAADQ/wwA
AAAAAA//zPAC0AAO3PARAAAQAAAP3PAQDQAPDPAiAAABAAAA0A/wzQARAAARAA
ADAAAA3QAAAAAQDQAQAAAADQAP3PAAAAAA0AAB0A/ywAAAAAAA0AAB0AAADQAhAA
...
-----END VORTEX256 PRIVATE KEY-----
```

---

## Python usage

```python
from vortex_pqc import PEMKind, encode_pem, decode_pem, write_pem_file, read_pem_file

# Encode / decode in memory
pem_str = encode_pem(PEMKind.PUBLIC_KEY, public_key_bytes)
raw     = decode_pem(PEMKind.PUBLIC_KEY, pem_str)

# File I/O (private keys written with mode 0o600)
write_pem_file("key.pem", PEMKind.PRIVATE_KEY, private_key_bytes)
sk = read_pem_file("key.pem", PEMKind.PRIVATE_KEY)
```

---

## Validation errors

| Error message | Cause |
|---------------|-------|
| `invalid data length for <KIND>` | Input bytes don't match expected size on encode |
| `missing or invalid PEM block for <KIND>` | Header/footer not found or wrong kind |
| `invalid Base64 payload for <KIND>` | Body is not valid Base64 |
| `invalid decoded length for <KIND>` | Decoded bytes don't match expected size |

---

## Interoperability notes

- PEM labels are **not** registered with IANA; they are VORTEX-specific.
- Do not mix VORTEX PEM files with ML-KEM/Kyber PEM files — labels and layouts differ.
- For TLS integration, use raw byte APIs (`generate_keypair`, `encapsulate`,
  `decapsulate`) rather than PEM on the wire.
