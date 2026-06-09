<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>C Library Guide</strong>
  &nbsp;·&nbsp;
  <a href="performance.md">Performance →</a>
</p>

<h1 align="center">C Library Guide</h1>

<p align="center">
  Build, link, and embed <code>libvortex_pqc.a</code> in native applications
</p>

<br/>

## Build

```bash
cd c
make lib      # → build/libvortex_pqc.a
make test     # verify correctness
make demo     # Alice–Bob CLI demo
```

Requirements: C compiler (clang/gcc), `make`, `ar`.

<br/>

## Header

```c
#include "vortex_pqc.h"
```

Key constants:

```c
VORTEX_PUBLIC_KEY_BYTES      // 800
VORTEX_PRIVATE_KEY_BYTES     // 1248
VORTEX_CIPHERTEXT_BYTES      // 768
VORTEX_SHARED_SECRET_BYTES   // 32
```

<br/>

## API

```c
int vortex_keypair(uint8_t *pk, uint8_t *sk);
int vortex_enc(const uint8_t *pk, uint8_t *ct, uint8_t *ss);
int vortex_dec(const uint8_t *ct, const uint8_t *sk, uint8_t *ss);
```

| Function | Returns | Notes |
|:---------|:--------|:------|
| `vortex_keypair` | `0` success, `<0` error | Fills pk[800] and sk[1248] |
| `vortex_enc` | `0` success | Fills ct[768] and ss[32] |
| `vortex_dec` | Always `0` | Implicit rejection — ss is wrong on tampered ct |

<br/>

## Linking

```bash
cc -O2 -I c/include my_app.c c/build/libvortex_pqc.a -o my_app
```

Include paths needed:

```
-I c/include          # vortex_pqc.h
-I c/src              # vortex_poly.h (internal)
-I c/vendor/sha3      # fips202.h
```

<br/>

## Complete example

```c
#include <stdio.h>
#include <string.h>
#include "vortex_pqc.h"

int main(void) {
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ss_enc[VORTEX_SHARED_SECRET_BYTES];
    uint8_t ss_dec[VORTEX_SHARED_SECRET_BYTES];

    if (vortex_keypair(pk, sk) != 0) {
        fprintf(stderr, "keypair failed\n");
        return 1;
    }

    if (vortex_enc(pk, ct, ss_enc) != 0) {
        fprintf(stderr, "encapsulation failed\n");
        return 1;
    }

    vortex_dec(ct, sk, ss_dec);

    if (memcmp(ss_enc, ss_dec, VORTEX_SHARED_SECRET_BYTES) == 0) {
        printf("Key exchange succeeded.\n");
    } else {
        printf("Key exchange FAILED.\n");
        return 1;
    }

    return 0;
}
```

<br/>

## Memory safety

<table>
<thead>
<tr><th align="left">Practice</th><th align="left">Detail</th></tr>
</thead>
<tbody>
<tr>
<td>Stack buffers</td>
<td>All API buffers can be stack-allocated with fixed sizes from header</td>
</tr>
<tr>
<td>Secret clearing</td>
<td>C library zeroes shared secret stack copies after Python binding returns</td>
</tr>
<tr>
<td>No heap allocation</td>
<td>Library does not call <code>malloc</code> — safe for embedded use</td>
</tr>
<tr>
<td>Thread safety</td>
<td>Functions are stateless — safe to call from multiple threads</td>
</tr>
</tbody>
</table>

<br/>

## Python C extension

The same C sources power the Python `_native` module via `python_module.c`.
Built automatically by `setup.py` during `pip install`.

```bash
pip install -e .          # builds _native.so / .pyd
python -c "import vortex_pqc; print(vortex_pqc.native_backend())"
```

<br/>

## Embedding in firmware

```
Flash budget estimate:
  libvortex_pqc.a  ≈  50–80 KB (platform-dependent)
  Stack per operation ≈  3 KB (pk + sk + ct + ss buffers)
  Heap               ≈  0 bytes
```

For constrained devices, consider:
- Pre-computing key pairs offline
- Using only `vortex_enc` / `vortex_dec` (skip keygen on device)
- Replacing schoolbook poly mul with NTT (future optimisation)

<br/>

<p align="center">
  <a href="api-reference.md">API reference</a>
  &nbsp;·&nbsp;
  <a href="architecture.md">Architecture</a>
  &nbsp;·&nbsp;
  <a href="performance.md">Performance</a>
</p>
