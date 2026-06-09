<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>Key Management</strong>
  &nbsp;·&nbsp;
  <a href="pem-format.md">PEM format →</a>
</p>

<h1 align="center">Key Management Guide</h1>

<p align="center">
  Generate, store, rotate, and protect VORTEX-256 key material
</p>

<br/>

## Key types

<table>
<thead>
<tr>
<th align="left">Material</th>
<th align="center">Size</th>
<th align="left">Sensitivity</th>
<th align="left">Lifetime</th>
</tr>
</thead>
<tbody>
<tr>
<td>Public key</td>
<td align="center">800 B</td>
<td>Public — can be distributed freely</td>
<td>Matches key pair lifetime</td>
</tr>
<tr>
<td>Private key</td>
<td align="center">1 248 B</td>
<td><strong>Secret</strong> — protect at all costs</td>
<td>Months to years (rotate on policy)</td>
</tr>
<tr>
<td>Ciphertext</td>
<td align="center">768 B</td>
<td>Per-session — safe to transmit</td>
<td>Single use</td>
</tr>
<tr>
<td>Shared secret</td>
<td align="center">32 B</td>
<td><strong>Secret</strong> — derive session keys, then discard</td>
<td>Single session</td>
</tr>
</tbody>
</table>

<br/>

## Generating keys

```python
from vortex_pqc import generate_keypair

kp = generate_keypair()
# kp.public_key  → 800 bytes
# kp.private_key → 1248 bytes
```

Each call produces a fresh, statistically independent key pair using the OS
CSPRNG.

<br/>

## PEM file storage

### Writing keys

```python
from vortex_pqc import PEMKind, write_pem_file, generate_keypair

kp = generate_keypair()

write_pem_file("server.pub", PEMKind.PUBLIC_KEY,  kp.public_key)
write_pem_file("server.key", PEMKind.PRIVATE_KEY, kp.private_key)
# server.key is automatically chmod 0600
```

### Reading keys

```python
from vortex_pqc import PEMKind, read_pem_file

pk = read_pem_file("server.pub", PEMKind.PUBLIC_KEY)
sk = read_pem_file("server.key", PEMKind.PRIVATE_KEY)
```

### PEM labels

| Kind | Header |
|:-----|:-------|
| Public key | `-----BEGIN VORTEX256 PUBLIC KEY-----` |
| Private key | `-----BEGIN VORTEX256 PRIVATE KEY-----` |
| Ciphertext | `-----BEGIN VORTEX256 CIPHERTEXT-----` |
| Shared secret | `-----BEGIN VORTEX256 SHARED SECRET-----` |

→ Full spec: [PEM format](pem-format.md)

<br/>

## Storage recommendations

<table>
<thead>
<tr>
<th align="left">Environment</th>
<th align="left">Public key</th>
<th align="left">Private key</th>
</tr>
</thead>
<tbody>
<tr>
<td>Development</td>
<td>PEM file in project (gitignored)</td>
<td>PEM file, mode 0600, gitignored</td>
</tr>
<tr>
<td>Server / VM</td>
<td>Config directory, world-readable OK</td>
<td>Encrypted volume or secrets manager</td>
</tr>
<tr>
<td>Container</td>
<td>ConfigMap / env var</td>
<td>Kubernetes Secret / Vault / sealed secret</td>
</tr>
<tr>
<td>Embedded / IoT</td>
<td>Flash, provisioned at factory</td>
<td>Secure element, TPM, or encrypted flash</td>
</tr>
</tbody>
</table>

<br/>

## Key rotation

```python
from vortex_pqc import generate_keypair, PEMKind, write_pem_file

def rotate_keys(path_prefix: str) -> None:
    """Generate new key pair and archive old ones."""
    import shutil
    from pathlib import Path

    for suffix in ("pub", "key"):
        old = Path(f"{path_prefix}.{suffix}")
        if old.exists():
            shutil.move(old, old.with_suffix(".bak"))

    kp = generate_keypair()
    write_pem_file(f"{path_prefix}.pub", PEMKind.PUBLIC_KEY,  kp.public_key)
    write_pem_file(f"{path_prefix}.key", PEMKind.PRIVATE_KEY, kp.private_key)
```

### Rotation policy guidelines

| Trigger | Action |
|:--------|:-------|
| Scheduled (e.g. annually) | Generate new pair, update distribution |
| Personnel change | Rotate immediately |
| Suspected compromise | Rotate immediately, investigate |
| Algorithm migration | Generate new pair with new library version |

<br/>

## Private key anatomy

Understanding what's inside the 1248-byte private key:

```
┌────────────┬──────────────────────────────────────────┐
│ Bytes      │ Content                                  │
├────────────┼──────────────────────────────────────────┤
│ 0 – 383    │ pack(s) — secret polynomial              │
│ 384 – 1183 │ Public key (embedded copy)               │
│ 1184–1215  │ H(pk) — SHA3-256 hash of public key      │
│ 1216–1247  │ z — implicit rejection token             │
└────────────┴──────────────────────────────────────────┘
```

Never expose bytes 0–383 or 1216–1247. The embedded public key (384–1183) is
safe to share.

<br/>

## .gitignore template

```gitignore
# VORTEX key material — never commit
*.key
*.pem
server.key
server.pub
```

<br/>

<p align="center">
  <a href="pem-format.md">PEM format spec</a>
  &nbsp;·&nbsp;
  <a href="security.md">Security model</a>
  &nbsp;·&nbsp;
  <a href="guides-key-exchange.md">Key exchange guide</a>
</p>
