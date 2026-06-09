<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>Python Guide</strong>
  &nbsp;·&nbsp;
  <a href="guides-c-library.md">C library →</a>
</p>

<h1 align="center">Python Guide</h1>

<p align="center">
  Patterns, backends, and best practices for the <code>vortex_pqc</code> package
</p>

<br/>

## Installation

```bash
# Runtime only
pip install vortex-pqc

# Development
pip install "vortex-pqc[dev]"

# With benchmarking extras
pip install "vortex-pqc[benchmark]"
```

Requirements: **Python ≥ 3.10**, no runtime dependencies.

<br/>

## Imports

```python
# Core KEM operations
from vortex_pqc import (
    generate_keypair,
    encapsulate,
    decapsulate,
    native_backend,
)

# Size constants
from vortex_pqc import (
    PUBLIC_KEY_BYTES,     # 800
    PRIVATE_KEY_BYTES,    # 1248
    CIPHERTEXT_BYTES,     # 768
    SHARED_SECRET_BYTES,  # 32
)

# Types
from vortex_pqc import VortexKeyPair, Ciphertext, SecurityError

# PEM encoding
from vortex_pqc import PEMKind, encode_pem, decode_pem
from vortex_pqc import write_pem_file, read_pem_file

# Benchmarking
from vortex_pqc import benchmark_throughput
```

<br/>

## Backends

<table>
<thead>
<tr><th align="left">Backend</th><th align="left">When active</th><th align="left">Performance</th></tr>
</thead>
<tbody>
<tr>
<td><code>vortex-pqc-native-*</code></td>
<td>C extension compiled at install time</td>
<td>Fast — production path</td>
</tr>
<tr>
<td><code>vortex-pqc-pure-python</code></td>
<td>No C compiler or build failure</td>
<td>Slower — always correct</td>
</tr>
</tbody>
</table>

```python
import vortex_pqc

print(vortex_pqc.native_backend())
# "vortex-pqc-native-aarch64" on Apple Silicon with C extension
# "vortex-pqc-pure-python" without compiled extension
```

The API is identical regardless of backend. Code never needs to branch on
backend name.

<br/>

## Typed usage patterns

### Key pair as a named tuple

```python
kp: vortex_pqc.VortexKeyPair = generate_keypair()
pk: bytes = kp.public_key    # always 800 bytes
sk: bytes = kp.private_key   # always 1248 bytes
```

### Ciphertext as a named tuple

```python
ct: vortex_pqc.Ciphertext = encapsulate(pk)
wire: bytes = ct.data              # send this (768 bytes)
secret: bytes = ct.shared_secret   # keep this (32 bytes)
```

<br/>

## Error handling

```python
from vortex_pqc import encapsulate, decapsulate, SecurityError

# Length validation — raises ValueError
try:
    encapsulate(b"\x00" * 100)
except ValueError as e:
    print(f"Bad input: {e}")

# Decapsulation never raises on tampered ciphertexts (implicit rejection)
ss = decapsulate(tampered_ct, sk)   # returns wrong 32 bytes, no exception

# Native backend integrity failure (rare)
try:
    decapsulate(ct, sk)
except SecurityError:
    pass
```

<br/>

## Idiomatic patterns

<details>
<summary><strong>Context manager for ephemeral keys</strong></summary>

<br/>

```python
from contextlib import contextmanager
from vortex_pqc import generate_keypair, VortexKeyPair

@contextmanager
def ephemeral_keypair():
    kp = generate_keypair()
    try:
        yield kp
    finally:
        # Best-effort zeroing (Python bytes are immutable, but drop refs)
        del kp

with ephemeral_keypair() as alice:
    ct = encapsulate(alice.public_key)
```

</details>

<details>
<summary><strong>Validate-then-operate</strong></summary>

<br/>

```python
from vortex_pqc import PUBLIC_KEY_BYTES, CIPHERTEXT_BYTES, encapsulate, decapsulate

def safe_encapsulate(pk: bytes):
    if len(pk) != PUBLIC_KEY_BYTES:
        raise ValueError(f"expected {PUBLIC_KEY_BYTES} bytes, got {len(pk)}")
    return encapsulate(pk)

def safe_decapsulate(ct: bytes, sk: bytes):
    if len(ct) != CIPHERTEXT_BYTES:
        raise ValueError(f"expected {CIPHERTEXT_BYTES} bytes, got {len(ct)}")
    return decapsulate(ct, sk)
```

</details>

<br/>

## Testing your integration

```python
def test_vortex_round_trip():
    from vortex_pqc import generate_keypair, encapsulate, decapsulate

    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    ss = decapsulate(ct.data, kp.private_key)
    assert ss == ct.shared_secret
    assert len(ss) == 32

def test_vortex_rejects_wrong_key():
    from vortex_pqc import generate_keypair, encapsulate, decapsulate

    kp1 = generate_keypair()
    kp2 = generate_keypair()
    ct = encapsulate(kp1.public_key)
    ss_wrong = decapsulate(ct.data, kp2.private_key)
    assert ss_wrong != ct.shared_secret
```

<br/>

<p align="center">
  <a href="api-reference.md">API reference</a>
  &nbsp;·&nbsp;
  <a href="performance.md">Performance</a>
  &nbsp;·&nbsp;
  <a href="guides-key-exchange.md">Key exchange guide</a>
</p>
