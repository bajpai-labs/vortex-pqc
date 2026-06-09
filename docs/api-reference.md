<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>API Reference</strong>
  &nbsp;·&nbsp;
  <a href="pem-format.md">PEM Format →</a>
</p>

<h1 align="center">API Reference</h1>

<p align="center">
  Complete reference for the Python package <code>vortex_pqc</code><br/>
  and the C library <code>vortex_pqc.h</code>
</p>

<br/>

## Python package · `vortex_pqc`

### Constants

| Name | Value | Description |
|------|------:|-------------|
| `PUBLIC_KEY_BYTES` | 800 | Public key size |
| `PRIVATE_KEY_BYTES` | 1248 | Private key size |
| `CIPHERTEXT_BYTES` | 768 | Ciphertext size |
| `SHARED_SECRET_BYTES` | 32 | Shared secret size |
| `__version__` | `"0.1.0"` | Package version |

---

### `generate_keypair() → VortexKeyPair`

Generate a fresh VORTEX-256 key pair.

**Returns:** `VortexKeyPair(public_key: bytes, private_key: bytes)`

```python
kp = generate_keypair()
len(kp.public_key)   # 800
len(kp.private_key)  # 1248
```

---

### `encapsulate(public_key: bytes) → Ciphertext`

Encapsulate a shared secret to a public key.

**Parameters:**
- `public_key` — exactly 800 bytes

**Returns:** `Ciphertext(data: bytes, shared_secret: bytes)`
- `data` — 768-byte ciphertext (send to recipient)
- `shared_secret` — 32-byte derived secret (keep locally)

**Raises:** `ValueError` if `public_key` length is wrong.

```python
ct = encapsulate(kp.public_key)
```

---

### `decapsulate(ciphertext: bytes, private_key: bytes) → bytes`

Recover the shared secret from a ciphertext and private key.

**Parameters:**
- `ciphertext` — exactly 768 bytes
- `private_key` — exactly 1248 bytes

**Returns:** 32-byte shared secret.

**Raises:**
- `ValueError` — wrong input lengths
- `SecurityError` — native backend integrity failure (rare; pure Python uses implicit rejection instead)

**Implicit rejection:** On tampered ciphertexts the function returns a
pseudorandom 32-byte value derived from the private key's rejection token `z`.
It does **not** raise on invalid ciphertexts in the pure-Python path.

```python
ss = decapsulate(ct.data, kp.private_key)
```

---

### `native_backend() → str`

Return the active implementation backend name.

```python
native_backend()  # "vortex-pqc-native-aarch64" or "vortex-pqc-pure-python"
```

---

### `benchmark_throughput(operations: int) → dict`

Measure keygen, encapsulation, and decapsulation throughput.

**Parameters:**
- `operations` — number of iterations (≥ 1)

**Returns:**

```python
{
    "keygen": {"mean_ops": float, "confidence_interval": float},
    "encaps": {"mean_ops": float, "confidence_interval": float},
    "decaps": {"mean_ops": float, "confidence_interval": float},
}
```

---

## PEM module

### `PEMKind` (enum)

| Member | PEM header label | Expected bytes |
|--------|------------------|---------------:|
| `PEMKind.PUBLIC_KEY` | `VORTEX256 PUBLIC KEY` | 800 |
| `PEMKind.PRIVATE_KEY` | `VORTEX256 PRIVATE KEY` | 1248 |
| `PEMKind.CIPHERTEXT` | `VORTEX256 CIPHERTEXT` | 768 |
| `PEMKind.SHARED_SECRET` | `VORTEX256 SHARED SECRET` | 32 |

### `encode_pem(kind: PEMKind, data: bytes) → str`

Encode binary data as a PEM block string (trailing newline included).

### `decode_pem(kind: PEMKind, pem: str) → bytes`

Decode a PEM block back to raw bytes.

### `write_pem_file(path, kind, data) → None`

Write a PEM file and set permissions to `0o600`.

### `read_pem_file(path, kind) → bytes`

Read and decode a PEM file.

---

## Exceptions

### `SecurityError`

Raised when a cryptographic integrity check fails in the native backend.
Subclass of `Exception`.

---

## C library (`vortex_pqc.h`)

Include: `c/include/vortex_pqc.h`  
Link: `c/build/libvortex_pqc.a`

### Constants

```c
#define VORTEX_N                     256
#define VORTEX_Q                     3329
#define VORTEX_K                     2
#define VORTEX_PUBLIC_KEY_BYTES      800
#define VORTEX_PRIVATE_KEY_BYTES     1248
#define VORTEX_CIPHERTEXT_BYTES      768
#define VORTEX_SHARED_SECRET_BYTES   32
```

### `int vortex_keypair(uint8_t *pk, uint8_t *sk)`

Generate a key pair. Returns `0` on success, negative on error.

### `int vortex_enc(const uint8_t *pk, uint8_t *ct, uint8_t *ss)`

Encapsulate. Returns `0` on success.

### `int vortex_dec(const uint8_t *ct, const uint8_t *sk, uint8_t *ss)`

Decapsulate with implicit rejection. Always returns `0`; on tampered
ciphertexts the output `ss` is a pseudorandom value (not the original secret).

---

## Private key layout (1248 bytes)

| Offset | Size | Content |
|--------|-----:|---------|
| 0 | 384 | `pack(s)` — secret polynomial (12-bit coefficients) |
| 384 | 800 | Public key (embedded copy) |
| 1184 | 32 | `H(pk)` — SHA3-256 hash of public key |
| 1216 | 32 | `z` — implicit rejection seed |

## Public key layout (800 bytes)

| Offset | Size | Content |
|--------|-----:|---------|
| 0 | 32 | `ρ` — seed for base element expansion |
| 32 | 384 | `pack(b₀)` |
| 416 | 384 | `pack(b₁)` |

## Ciphertext layout (768 bytes)

| Offset | Size | Content |
|--------|-----:|---------|
| 0 | 320 | Compressed `u₀` (10 bits/coefficient) |
| 320 | 320 | Compressed `u₁` (10 bits/coefficient) |
| 640 | 128 | Compressed `v` (4 bits/coefficient) |
