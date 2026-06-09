/**
 * vortex_core.c — VORTEX-256 KEM: KeyGen / Encaps / Decaps
 *
 * Follows the Fujisaki-Okamoto (FO) transform with implicit rejection,
 * matching the structure of ML-KEM (FIPS 203) while using the novel
 * RotMLWE hardness assumption.
 */

#include <string.h>
#include <stdint.h>
#include "../include/vortex_pqc.h"
#include "vortex_poly.h"
#include "fips202.h"
#include "randombytes.h"

/* Compiler barrier to prevent optimisation of secret clearing. */
static void secure_zero(void *v, size_t n)
{
    volatile uint8_t *p = (volatile uint8_t *)v;
    while (n--) *p++ = 0;
}

/* Constant-time byte-array compare.  Returns 0 if equal, non-zero otherwise. */
static uint8_t ct_ne(const uint8_t *a, const uint8_t *b, size_t n)
{
    uint8_t diff = 0;
    for (size_t i = 0; i < n; i++) diff |= a[i] ^ b[i];
    return diff;
}

/* ─── Key generation ─────────────────────────────────────────────────────── */

int vortex_keypair(uint8_t *pk, uint8_t *sk)
{
    uint8_t rho[32], sigma[32];
    vortex_poly a_list[VORTEX_K], s, e, b;

    randombytes(rho,   32);
    randombytes(sigma, 32);

    /* Generate base ring element and K−1 Frobenius rotations */
    vortex_gen_base(&a_list[0], rho);
    for (int i = 1; i < VORTEX_K; i++)
        vortex_poly_frobenius(&a_list[i], &a_list[i - 1]);

    /* Sample secret s ~ CBD(ETA1) */
    vortex_cbd3(&s, sigma, 0);

    /* Build public key: ρ ‖ pack(b₀) ‖ … ‖ pack(b_{K-1}) */
    memcpy(pk, rho, 32);
    for (int i = 0; i < VORTEX_K; i++) {
        vortex_cbd3(&e, sigma, (uint8_t)(i + 1));
        vortex_poly_mul(&b, &a_list[i], &s);
        vortex_poly_add(&b, &b, &e);
        vortex_poly_pack(pk + 32 + i * VORTEX_POLY_BYTES, &b);
    }

    /* Build private key: pack(s) ‖ pk ‖ H(pk) ‖ z */
    vortex_poly_pack(sk, &s);
    memcpy(sk + VORTEX_POLY_BYTES, pk, VORTEX_PUBLIC_KEY_BYTES);
    sha3_256(sk + VORTEX_POLY_BYTES + VORTEX_PUBLIC_KEY_BYTES,
             pk, VORTEX_PUBLIC_KEY_BYTES);
    randombytes(sk + VORTEX_POLY_BYTES + VORTEX_PUBLIC_KEY_BYTES + 32, 32);

    secure_zero(&s, sizeof(s));
    return 0;
}

/* ─── Helper: encapsulate internals (shared by enc and dec re-encrypt) ───── */

static void _do_enc(uint8_t *ct,
                    uint8_t *K_bar_out,
                    const uint8_t *pk,
                    const uint8_t *m)
{
    const uint8_t *rho  = pk;
    uint8_t pkh[32], g_out[64];
    vortex_poly a_list[VORTEX_K], b_list[VORTEX_K];
    vortex_poly r, ep, epp, u, v, tmp;

    sha3_256(pkh, pk, VORTEX_PUBLIC_KEY_BYTES);

    /* G(m ‖ H(pk)) → (K̄, coins) */
    {
        uint8_t buf[64];
        memcpy(buf,      m,   32);
        memcpy(buf + 32, pkh, 32);
        sha3_512(g_out, buf, 64);
    }
    memcpy(K_bar_out, g_out, 32);
    const uint8_t *coins = g_out + 32;

    /* Sample r ~ CBD(ETA1) from coins */
    vortex_cbd3(&r, coins, 0);

    /* Regenerate Frobenius rotations */
    vortex_gen_base(&a_list[0], rho);
    for (int i = 1; i < VORTEX_K; i++)
        vortex_poly_frobenius(&a_list[i], &a_list[i - 1]);

    /* Unpack b_i from pk */
    for (int i = 0; i < VORTEX_K; i++)
        vortex_poly_unpack(&b_list[i], pk + 32 + i * VORTEX_POLY_BYTES);

    /* u_i = a_i · r + e′_i  (compressed) */
    for (int i = 0; i < VORTEX_K; i++) {
        vortex_cbd2(&ep, coins, (uint8_t)(i + 1));
        vortex_poly_mul(&u, &a_list[i], &r);
        vortex_poly_add(&u, &u, &ep);
        vortex_poly_compress_u(ct + i * VORTEX_POLY_COMPRESSED_U, &u);
    }

    /* v = Σᵢ b_i · r + e″ + encode(m) */
    vortex_cbd2(&epp, coins, (uint8_t)(VORTEX_K + 1));
    memcpy(&v, &epp, sizeof(v));
    for (int i = 0; i < VORTEX_K; i++) {
        vortex_poly_mul(&tmp, &b_list[i], &r);
        vortex_poly_add(&v, &v, &tmp);
    }
    vortex_poly_encode_msg(&tmp, m);
    vortex_poly_add(&v, &v, &tmp);
    vortex_poly_compress_v(ct + VORTEX_K * VORTEX_POLY_COMPRESSED_U, &v);
}

/* ─── Encapsulation ──────────────────────────────────────────────────────── */

int vortex_enc(const uint8_t *pk, uint8_t *ct, uint8_t *ss)
{
    uint8_t m[32], K_bar[32], ct_hash[32], kdf_in[64];

    randombytes(m, 32);
    _do_enc(ct, K_bar, pk, m);

    /* ss = SHAKE-256(K̄ ‖ H(ct)) */
    sha3_256(ct_hash, ct, VORTEX_CIPHERTEXT_BYTES);
    memcpy(kdf_in,      K_bar,   32);
    memcpy(kdf_in + 32, ct_hash, 32);
    shake256(ss, VORTEX_SHARED_SECRET_BYTES, kdf_in, 64);

    secure_zero(m, 32);
    return 0;
}

/* ─── Decapsulation ──────────────────────────────────────────────────────── */

int vortex_dec(const uint8_t *ct, const uint8_t *sk, uint8_t *ss)
{
    const uint8_t *sk_s  = sk;
    const uint8_t *pk    = sk  + VORTEX_POLY_BYTES;
    const uint8_t *pkh   = pk  + VORTEX_PUBLIC_KEY_BYTES;
    const uint8_t *z     = pkh + 32;

    vortex_poly s, u_list[VORTEX_K], v, w, tmp;
    uint8_t m_prime[32], K_bar_p[32];
    uint8_t ct_prime[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ct_hash[32], kdf_in[64];

    /* Unpack secret s */
    vortex_poly_unpack(&s, sk_s);

    /* Decompress u_i and v from ciphertext */
    for (int i = 0; i < VORTEX_K; i++)
        vortex_poly_decompress_u(&u_list[i],
                                  ct + i * VORTEX_POLY_COMPRESSED_U);
    vortex_poly_decompress_v(&v, ct + VORTEX_K * VORTEX_POLY_COMPRESSED_U);

    /* Recover m′: w = v − Σᵢ s·u_i  ≈ encode(m) */
    memcpy(&w, &v, sizeof(v));
    for (int i = 0; i < VORTEX_K; i++) {
        vortex_poly_mul(&tmp, &s, &u_list[i]);
        vortex_poly_sub(&w, &w, &tmp);
    }
    vortex_poly_decode_msg(m_prime, &w);

    /*
     * Re-encapsulate deterministically with m′.
     * pkh stored in sk at offset POLY_BYTES + PK_BYTES is already H(pk),
     * but _do_enc recomputes it internally — pass pk.
     */
    _do_enc(ct_prime, K_bar_p, pk, m_prime);

    /* Shared secret derivation with implicit rejection */
    sha3_256(ct_hash, ct, VORTEX_CIPHERTEXT_BYTES);

    uint8_t fail = ct_ne(ct_prime, ct, VORTEX_CIPHERTEXT_BYTES);
    /* fail = 0 → use K̄′;  fail ≠ 0 → use z  (both constant-time paths) */
    uint8_t mask = (uint8_t)((uint32_t)(-(int32_t)(fail != 0)) >> 24);
    /* mask = 0x00 on success, 0xFF on failure */

    uint8_t kdf_key[32];
    for (int i = 0; i < 32; i++)
        kdf_key[i] = K_bar_p[i] ^ (mask & (K_bar_p[i] ^ z[i]));

    memcpy(kdf_in,      kdf_key, 32);
    memcpy(kdf_in + 32, ct_hash, 32);
    shake256(ss, VORTEX_SHARED_SECRET_BYTES, kdf_in, 64);

    secure_zero(&s, sizeof(s));
    secure_zero(m_prime, 32);
    return 0;
}
