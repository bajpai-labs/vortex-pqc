# Architecture

Overview of the **vortex-pqc** repository structure, implementation layers,
and build pipeline.

---

## Repository layout

```
vortex-pqc/
├── src/
│   ├── vortex_pqc/          # Python package
│   │   ├── __init__.py      # Public exports
│   │   ├── params.py        # Scheme constants and sizes
│   │   ├── core.py          # Public API (backend dispatch)
│   │   ├── _pure.py         # Pure-Python reference implementation
│   │   ├── _native*.so      # Compiled C extension (optional, built at install)
│   │   ├── pem.py           # PEM encode/decode
│   │   └── benchmark.py     # Throughput measurement
│   └── tests/
│       ├── test_core.py     # KEM correctness tests
│       └── test_pem.py      # PEM round-trip tests
├── c/
│   ├── include/
│   │   └── vortex_pqc.h     # Public C API
│   ├── src/
│   │   ├── vortex_core.c    # KeyGen / Enc / Dec
│   │   ├── vortex_poly.c    # Polynomial arithmetic
│   │   ├── vortex_poly.h
│   │   └── python_module.c  # Python C extension bindings
│   ├── vendor/sha3/         # SHA-3 / SHAKE (fips202, randombytes)
│   ├── tests/test_vortex.c
│   ├── examples/demo.c
│   └── Makefile
├── docs/                    # Documentation (this folder)
├── .github/workflows/
│   ├── ci.yml               # CI on push/PR
│   └── release.yml          # PyPI publish on release
├── pyproject.toml
├── setup.py                 # C extension build config
├── Makefile                 # Dev shortcuts
└── README.md
```

---

## Implementation layers

```
┌─────────────────────────────────────────────────┐
│  Application / Integration                      │
│  (TLS, apps, scripts)                           │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  Python API  (core.py, pem.py, benchmark.py)    │
└────────┬───────────────────────┬────────────────┘
         │                       │
┌────────▼────────┐    ┌─────────▼───────────────┐
│  _native (.so)  │    │  _pure.py (reference)   │
│  C extension    │    │  Always available       │
└────────┬────────┘    └─────────────────────────┘
         │
┌────────▼────────────────────────────────────────┐
│  C library  (vortex_core.c, vortex_poly.c)    │
│  + vendor/sha3 (fips202, randombytes)         │
└─────────────────────────────────────────────────┘
```

### Backend selection (`core.py`)

```python
try:
    from . import _native as _be
except ImportError:
    from . import _pure as _be
```

- **`_native`** — compiled via `setup.py`; ~10× faster on typical hardware
- **`_pure`** — zero-dependency fallback; correct but slower (schoolbook poly mul)

Both backends expose the same interface: `keypair()`, `encapsulate()`, `decapsulate()`.

---

## C library

The C layer is self-contained:

| Component | Role |
|-----------|------|
| `vortex_poly.c` | Ring arithmetic, Frobenius, compression, CBD sampling |
| `vortex_core.c` | KEM operations, FO transform, implicit rejection |
| `vendor/sha3/fips202.c` | SHA-3 / SHAKE (FIPS 202) |
| `vendor/sha3/randombytes.c` | OS CSPRNG interface |

Polynomial multiplication currently uses **schoolbook O(n²)** for portability.
The ring parameters (`q=3329`, `n=256`) are NTT-friendly; a future optimisation
can swap in NTT-based multiplication without changing the API.

---

## Build targets

| Command | Output |
|---------|--------|
| `make install` | Editable Python install with dev deps |
| `make test` | Python + C tests |
| `make build` | Python wheel in `dist/` |
| `make -C c lib` | `c/build/libvortex_pqc.a` |
| `make -C c test` | C unit tests |
| `make -C c demo` | Alice–Bob CLI demo |
| `make lint` | flake8 + mypy |
| `make clean` | Remove build artifacts |

---

## CI pipeline

**`.github/workflows/ci.yml`** runs on push/PR to `main`/`master`:

1. **Python matrix** — Ubuntu + macOS × Python 3.10/3.11/3.12
   - `pip install -e ".[dev]"`
   - `pytest src/tests/`
   - flake8 + mypy (non-blocking)

2. **C library** — Ubuntu + macOS
   - `make -C c test`

---

## Release pipeline

**`.github/workflows/release.yml`** triggers on GitHub Release creation:

1. Run full test suite
2. `python -m build --sdist --wheel`
3. `twine check dist/*`
4. Publish to PyPI via `PYPI_API_TOKEN` secret

---

## Relationship to Kyber-PQC

| | vortex-pqc | kyber-pqc |
|---|-----------|-----------|
| Repo | [bajpai-labs/vortex-pqc](https://github.com/bajpai-labs/vortex-pqc) | [krish567366/Kyber-PQC](https://github.com/krish567366/Kyber-PQC) |
| Algorithm | VORTEX-256 (RotMLWE) | ML-KEM-512 (Kyber) |
| PyPI | `vortex-pqc` | `kyber-pqc` |
| Shared code | SHA-3 vendor only | Full Kyber reference |

The projects are **fully independent**. No cross-imports at runtime.
