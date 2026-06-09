<p align="center">
  <a href="README.md">← Documentation</a>
  &nbsp;·&nbsp;
  <strong>Glossary</strong>
</p>

<h1 align="center">Glossary</h1>

<p align="center">
  Terms and notation used throughout the VORTEX-256 documentation
</p>

<br/>

<table>
<thead>
<tr>
<th align="left">Term</th>
<th align="left">Definition</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>CBD(η)</strong></td>
<td>Centered Binomial Distribution — noise sampling method. Each coefficient is a sum of η random bits minus η random bits.</td>
</tr>
<tr>
<td><strong>Ciphertext (ct)</strong></td>
<td>768-byte output of encapsulation. Sent from sender to receiver.</td>
</tr>
<tr>
<td><strong>Decapsulation</strong></td>
<td>Receiver operation: recover shared secret from ciphertext + private key.</td>
</tr>
<tr>
<td><strong>Encapsulation</strong></td>
<td>Sender operation: generate ciphertext + shared secret from public key.</td>
</tr>
<tr>
<td><strong>FO transform</strong></td>
<td>Fujisaki–Okamoto transform — converts IND-CPA scheme to IND-CCA2 KEM using hashing and re-encryption.</td>
</tr>
<tr>
<td><strong>Frobenius map (σ)</strong></td>
<td>Ring automorphism σ(f(x)) = f(x³ mod x²⁵⁶+1). Generates the rotation orbit.</td>
</tr>
<tr>
<td><strong>Implicit rejection</strong></td>
<td>On invalid ciphertext, return pseudorandom secret (from token z) instead of error.</td>
</tr>
<tr>
<td><strong>IND-CCA2</strong></td>
<td>Indistinguishability under adaptive chosen-ciphertext attack — the gold standard for KEM security.</td>
</tr>
<tr>
<td><strong>KEM</strong></td>
<td>Key Encapsulation Mechanism — establishes a shared secret via public-key cryptography.</td>
</tr>
<tr>
<td><strong>K</strong></td>
<td>Module rank = 2. Number of Frobenius rotation instances in VORTEX-256.</td>
</tr>
<tr>
<td><strong>ML-KEM</strong></td>
<td>NIST-standardised Module-Lattice KEM (FIPS 203), formerly known as Kyber.</td>
</tr>
<tr>
<td><strong>MLWE</strong></td>
<td>Module Learning With Errors — standard lattice assumption used by Kyber.</td>
</tr>
<tr>
<td><strong>n</strong></td>
<td>Ring dimension = 256. Number of coefficients per polynomial.</td>
</tr>
<tr>
<td><strong>PEM</strong></td>
<td>Privacy-Enhanced Mail format — Base64 encoding with BEGIN/END headers.</td>
</tr>
<tr>
<td><strong>Post-quantum (PQC)</strong></td>
<td>Cryptography resistant to attacks by quantum computers (e.g. Shor's algorithm).</td>
</tr>
<tr>
<td><strong>Public key (pk)</strong></td>
<td>800-byte value published by the receiver. Safe to distribute.</td>
</tr>
<tr>
<td><strong>Private key (sk)</strong></td>
<td>1248-byte secret value. Must be protected.</td>
</tr>
<tr>
<td><strong>q</strong></td>
<td>Prime modulus = 3329. All coefficient arithmetic is mod q.</td>
</tr>
<tr>
<td><strong>R_q</strong></td>
<td>Polynomial ring ℤ_q[x]/(x²⁵⁶+1) — the algebraic setting for VORTEX.</td>
</tr>
<tr>
<td><strong>RotMLWE</strong></td>
<td>Rotational Module Learning With Errors — VORTEX's novel hardness assumption.</td>
</tr>
<tr>
<td><strong>Shared secret (ss)</strong></td>
<td>32-byte output of KEM. Both parties derive the same value.</td>
</tr>
<tr>
<td><strong>SHAKE-128/256</strong></td>
<td>Extendable-output functions (XOF) from SHA-3 family. Used for expansion and KDF.</td>
</tr>
<tr>
<td><strong>XOF</strong></td>
<td>Extendable Output Function — hash function with arbitrary output length.</td>
</tr>
<tr>
<td><strong>η₁, η₂</strong></td>
<td>CBD noise parameters. η₁=3 for keygen, η₂=2 for encapsulation.</td>
</tr>
<tr>
<td><strong>ρ (rho)</strong></td>
<td>32-byte seed for expanding the base ring element a₀.</td>
</tr>
<tr>
<td><strong>z</strong></td>
<td>32-byte implicit rejection token stored in the private key.</td>
</tr>
</tbody>
</table>

<br/>

<p align="center">
  <a href="concepts.md">Core concepts</a>
  &nbsp;·&nbsp;
  <a href="cryptography.md">Cryptography deep dive</a>
</p>
