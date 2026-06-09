/**
 * vortex_pqc.h — VORTEX-256 Key Encapsulation Mechanism
 *
 * Novel post-quantum primitive based on Rotational Module LWE (RotMLWE).
 *
 * Instead of a k×k module matrix (as in ML-KEM/Kyber), VORTEX-256 derives
 * K public ring elements from a SINGLE base element via Frobenius automorphisms:
 *
 *   a₀ = a,  a₁ = σ(a) = a(x³ mod x^{256}+1),  …
 *
 * The same secret  s ∈ R_q  underlies all K instances, giving a new hardness
 * assumption with identical key/ciphertext footprints to Kyber-512.
 *
 * Parameters
 * ──────────
 *   Ring:        Z_{3329}[x] / (x^{256} + 1)
 *   Module rank: K = 2
 *   Noise:       η₁ = 3 (keygen),  η₂ = 2 (encaps)
 *   Compression: dᵤ = 10 bits,  d_v = 4 bits
 *
 * Sizes (identical to ML-KEM-512 / Kyber-512)
 * ─────────────────────────────────────────────
 *   Public key   : 800 bytes
 *   Private key  : 1248 bytes
 *   Ciphertext   : 768 bytes
 *   Shared secret: 32 bytes
 */

#ifndef VORTEX_PQC_H
#define VORTEX_PQC_H

#include <stddef.h>
#include <stdint.h>

/* ── Scheme parameters ─────────────────────────────────────────────────── */
#define VORTEX_N    256
#define VORTEX_Q    3329
#define VORTEX_K    2
#define VORTEX_ETA1 3
#define VORTEX_ETA2 2
#define VORTEX_DU   10
#define VORTEX_DV   4

/* ── Object sizes in bytes ──────────────────────────────────────────────── */
#define VORTEX_POLY_BYTES          384   /* 256 × 12 bits / 8 */
#define VORTEX_POLY_COMPRESSED_U   320   /* 256 × 10 bits / 8 */
#define VORTEX_POLY_COMPRESSED_V   128   /* 256 ×  4 bits / 8 */

#define VORTEX_PUBLIC_KEY_BYTES    800   /* 32 + K×384  */
#define VORTEX_PRIVATE_KEY_BYTES   1248  /* 384 + 800 + 32 + 32 */
#define VORTEX_CIPHERTEXT_BYTES    768   /* K×320 + 128 */
#define VORTEX_SHARED_SECRET_BYTES 32

/* ── Public API ─────────────────────────────────────────────────────────── */

/**
 * vortex_keypair - Generate a VORTEX-256 key pair.
 * @pk: Output public key  (VORTEX_PUBLIC_KEY_BYTES)
 * @sk: Output private key (VORTEX_PRIVATE_KEY_BYTES)
 * Returns 0 on success, negative on error.
 */
int vortex_keypair(uint8_t *pk, uint8_t *sk);

/**
 * vortex_enc - Encapsulate a shared secret.
 * @pk: Input  public key   (VORTEX_PUBLIC_KEY_BYTES)
 * @ct: Output ciphertext   (VORTEX_CIPHERTEXT_BYTES)
 * @ss: Output shared secret (VORTEX_SHARED_SECRET_BYTES)
 * Returns 0 on success.
 */
int vortex_enc(const uint8_t *pk, uint8_t *ct, uint8_t *ss);

/**
 * vortex_dec - Decapsulate (implicit rejection on tampered ciphertext).
 * @ct: Input  ciphertext    (VORTEX_CIPHERTEXT_BYTES)
 * @sk: Input  private key   (VORTEX_PRIVATE_KEY_BYTES)
 * @ss: Output shared secret (VORTEX_SHARED_SECRET_BYTES)
 * Returns 0 always (implicit rejection — never fails hard).
 */
int vortex_dec(const uint8_t *ct, const uint8_t *sk, uint8_t *ss);

#endif /* VORTEX_PQC_H */
