<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>FAQ</strong>
</p>

<h1 align="center">Frequently Asked Questions</h1>

<br/>

<details>
<summary><strong>What is VORTEX-256?</strong></summary>

<br/>

A post-quantum Key Encapsulation Mechanism based on **Rotational Module
Learning With Errors (RotMLWE)**. It establishes a 32-byte shared secret
between two parties and uses the same wire sizes as Kyber-512.

→ [Overview](overview.md)

</details>

<details>
<summary><strong>Is VORTEX-256 NIST-approved?</strong></summary>

<br/>

No. VORTEX-256 is a **research preview** with a novel cryptographic assumption.
For NIST-approved post-quantum KEM, use **ML-KEM** (FIPS 203) via
[Kyber-PQC](https://github.com/krish567366/Kyber-PQC).

→ [Comparison guide](comparison.md)

</details>

<details>
<summary><strong>Can I use VORTEX keys with Kyber?</strong></summary>

<br/>

No. Although public keys (800 B) and ciphertexts (768 B) are the same **size**,
the byte layouts and algorithms are completely different. Keys and ciphertexts
are not interchangeable.

</details>

<details>
<summary><strong>Do I need a C compiler?</strong></summary>

<br/>

No. The package installs and works with pure Python only. A C compiler enables
the faster native backend (~10× throughput).

```bash
pip install vortex-pqc   # works either way
```

</details>

<details>
<summary><strong>What Python versions are supported?</strong></summary>

<br/>

Python **3.10, 3.11, 3.12, 3.13, 3.14** (and newer). Tested in CI on 3.10–3.12
across Ubuntu and macOS.

</details>

<details>
<summary><strong>What happens if someone tampers with a ciphertext?</strong></summary>

<br/>

VORTEX uses **implicit rejection**: decapsulation returns a pseudorandom
32-byte value (not the real shared secret) without raising an error. This
prevents padding oracle attacks.

→ [Core concepts — Implicit rejection](concepts.md#7--implicit-rejection)

</details>

<details>
<summary><strong>Can I use the 32-byte shared secret directly as an AES key?</strong></summary>

<br/>

You should **derive** an application key with HKDF:

```python
import hashlib
session_key = hashlib.hkdf_derive("sha256", 32, shared_secret,
                                   salt=b"my-app", info=b"session")
```

</details>

<details>
<summary><strong>What is RotMLWE?</strong></summary>

<br/>

A variant of Module-LWE where the public matrix is replaced by Frobenius
rotations of a single ring element. The same scalar secret is hidden under
each rotation.

→ [Core concepts](concepts.md#3--rotmlwe--the-novel-assumption)

</details>

<details>
<summary><strong>How does VORTEX compare to Google's post-quantum efforts?</strong></summary>

<br/>

Google has integrated **ML-KEM (Kyber)** into Chrome/TLS for production
post-quantum hybrid key exchange. VORTEX-256 is a **research alternative**
exploring a different lattice assumption at the same wire footprint. It is
not a drop-in replacement for Google's ML-KEM deployment.

→ [Comparison guide](comparison.md)

</details>

<details>
<summary><strong>Where is the documentation published?</strong></summary>

<br/>

- Library home: [postquantumlabs.in/library/vortex-pqc](https://postquantumlabs.in/library/vortex-pqc)
- In-repo: [docs/](README.md)
- Published docs: [postquantumlabs.in/docs/vortex-pqc](https://postquantumlabs.in/docs/vortex-pqc)
- Enterprise: [Bajpai Labs](https://bajpailabs.com)
- Auto-synced on every push to `main` that changes `docs/`

</details>

<details>
<summary><strong>How do I report a security bug?</strong></summary>

<br/>

Email **hello@bajpailabs.com** — do not file a public issue.

→ [Security model — Reporting](security.md#reporting-vulnerabilities)

</details>

<details>
<summary><strong>What license is VORTEX-256 under?</strong></summary>

<br/>

MIT License. Free for commercial and non-commercial use.

</details>

<br/>

<p align="center">
  Didn't find your answer?
  <a href="https://github.com/bajpai-labs/vortex-pqc/issues">Open an issue</a>
</p>
