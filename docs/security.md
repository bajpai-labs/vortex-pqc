<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>Security Model</strong>
  &nbsp;·&nbsp;
  <a href="comparison.md">Comparison →</a>
</p>

<h1 align="center">Security Model</h1>

<p align="center">
  Threat model, security guarantees, limitations,<br/>
  and responsible use of VORTEX-256
</p>

<br/>

## Security goals

VORTEX-256 targets **IND-CCA2** security as a KEM:

| Property | Meaning |
|:---------|:--------|
| **Confidentiality** | Ciphertexts reveal nothing about the shared secret |
| **Integrity** | Tampered ciphertexts produce wrong secrets (implicit rejection) |
| **Forward secrecy** (per session) | Each encapsulation uses fresh randomness |

<br/>

## Threat model

### In scope (defended against)

<table>
<thead>
<tr><th align="left">Threat</th><th align="left">Mitigation</th></tr>
</thead>
<tbody>
<tr>
<td>Passive eavesdropping</td>
<td>Lattice hardness (RotMLWE) — ciphertext reveals nothing about shared secret</td>
</tr>
<tr>
<td>Ciphertext tampering</td>
<td>FO transform + implicit rejection — wrong secret returned, no error leak</td>
</tr>
<tr>
<td>Chosen-ciphertext attacks</td>
<td>IND-CCA2 via FO — decapsulation safe even with attacker-crafted inputs</td>
</tr>
<tr>
<td>Quantum computers</td>
<td>Lattice assumption — no known polynomial-time quantum algorithm for RotMLWE</td>
</tr>
</tbody>
</table>

### Out of scope (your responsibility)

<table>
<thead>
<tr><th align="left">Threat</th><th align="left">What you must do</th></tr>
</thead>
<tbody>
<tr>
<td>Private key compromise</td>
<td>Protect <code>sk</code> at rest (PEM mode 0600, HSM, KMS)</td>
</tr>
<tr>
<td>Side-channel attacks</td>
<td>Use native C backend; avoid pure Python in timing-sensitive paths</td>
</tr>
<tr>
<td>Implementation bugs</td>
<td>Keep dependencies updated; run test suite; report vulnerabilities</td>
</tr>
<tr>
<td>Algorithm breakthrough</td>
<td>Monitor cryptanalysis; plan algorithm agility</td>
</tr>
<tr>
<td>Shared secret misuse</td>
<td>Derive application keys with a proper KDF (HKDF, etc.) — don't use raw 32 B directly</td>
</tr>
</tbody>
</table>

<br/>

## Cryptographic assumptions

### Primary: RotMLWE

Breaking VORTEX requires solving the **Rotational Module Learning With Errors**
problem: given `(a₀, b₀), (a₁, b₁), …, (a_{K-1}, b_{K-1})` where `aᵢ = σⁱ(a)`
and `bᵢ = aᵢ·s + eᵢ`, recover the secret `s`.

| Case | Known relationship |
|:-----|:-------------------|
| K = 1 | Reduces to standard RLWE |
| K > 1 | **Open research question** — correlated instances share structure |

### Secondary: Random oracle model

The FO transform and KDF are analyzed in the **random oracle model**, assuming
SHA-3 and SHAKE behave as ideal hash functions.

<br/>

## Security properties by operation

<table>
<thead>
<tr>
<th align="left">Operation</th>
<th align="left">Security level</th>
<th align="left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>generate_keypair()</code></td>
<td>IND-CPA secure public key</td>
<td>Secret <code>s</code> and rejection token <code>z</code> never exposed</td>
</tr>
<tr>
<td><code>encapsulate(pk)</code></td>
<td>IND-CCA2 shared secret</td>
<td>Fresh randomness per call; deterministic given same coins</td>
</tr>
<tr>
<td><code>decapsulate(ct, sk)</code></td>
<td>Implicit rejection</td>
<td>Never leaks validity via return value or exception (pure Python path)</td>
</tr>
<tr>
<td>PEM encoding</td>
<td>Encoding only — no additional security</td>
<td>Private key files set to mode <code>0600</code></td>
</tr>
</tbody>
</table>

<br/>

## Key material handling

### Do

```
✓  Store private keys encrypted at rest
✓  Use PEM with restrictive file permissions (automatic with write_pem_file)
✓  Rotate keys on compromise or schedule
✓  Derive application keys: HKDF(shared_secret, salt, info)
✓  Zero sensitive buffers after use (C library does this for stack copies)
✓  Use native backend in production-facing code paths
```

### Don't

```
✗  Log public keys, private keys, ciphertexts, or shared secrets
✗  Commit .pem or .key files to version control
✗  Use the raw 32-byte shared secret directly as an AES key without derivation
✗  Assume IND-CCA2 extends to your application protocol without analysis
✗  Deploy in production without independent security review
```

<br/>

## Research preview limitations

> VORTEX-256 has **not** been standardised by NIST and has **not** received
> the years of public cryptanalysis that ML-KEM (FIPS 203) has.

| Concern | Status |
|:--------|:-------|
| Novel assumption (RotMLWE) | Published for community review |
| Parameter selection | Based on ML-KEM analogues; not independently optimised |
| Side-channel resistance | Best-effort in C; pure Python is not constant-time |
| Formal security proof | FO reduction to RotMLWE; RotMLWE-to-RLWE reduction open for K>1 |
| Post-quantum security level | Estimated ~128-bit quantum (same ring as Kyber-512) |

<br/>

## Reporting vulnerabilities

If you discover a security issue:

1. **Do not** open a public GitHub issue
2. Email **hello@bajpailabs.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if any)
3. Allow 90 days for remediation before public disclosure

We follow coordinated disclosure practices.

<br/>

## Compliance guidance

| Requirement | VORTEX-256 status |
|:------------|:-----------------|
| FIPS 140 validated | ❌ Not validated |
| NIST-approved (FIPS 203) | ❌ Different algorithm |
| Export control (EAR) | Consult legal counsel — open-source crypto software |
| GDPR / data protection | KEM itself is agnostic; your key management must comply |

For regulated environments requiring NIST-approved algorithms, use
[ML-KEM (Kyber)](https://github.com/krish567366/Kyber-PQC) instead.

<br/>

## Security checklist for integrators

```
□  Threat model documented for your use case
□  Private keys stored securely (encrypted, access-controlled)
□  Shared secret derived with HKDF before use as session key
□  Ciphertext length validated (768 bytes) before decapsulation
□  No secret material in logs, metrics, or error messages
□  Native backend used in timing-sensitive deployments
□  Key rotation policy defined
□  Independent security review completed (for production)
```

<br/>

<p align="center">
  <a href="comparison.md">Comparison with other KEMs</a>
  &nbsp;·&nbsp;
  <a href="guides-key-management.md">Key management guide</a>
  &nbsp;·&nbsp;
  <a href="faq.md">FAQ</a>
</p>
