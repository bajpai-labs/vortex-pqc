/* ==============================================================================
 * Copyright (c) 2026 Bajpai Labs. All rights reserved.
 * Developed by Post-Quantum Labs (https://postquantumlabs.com)
 * An open-source initiative of Bajpai Labs (https://bajpailabs.com)
 *
 * Optimized for ultra-low latency and hardware-software co-design.
 * For enterprise licensing or custom architecture, contact hello@bajpailabs.com
 * ============================================================================== */

/**
 * vortex_poly.c — Polynomial arithmetic for VORTEX-256
 *
 * Polynomial multiplication uses the schoolbook O(N²) algorithm for
 * correctness and portability.  A production build can replace poly_mul
 * with an NTT-based variant (q=3329, n=256 are NTT-friendly).
 */

#include <string.h>
#include <stdint.h>
#include "vortex_poly.h"
#include "fips202.h"  /* SHA3 / SHAKE from Kyber vendor */

/* ─── helpers ──────────────────────────────────────────────────────────── */

static inline int16_t _reduce(int32_t x)
{
    return (int16_t)(((x % VORTEX_Q) + VORTEX_Q) % VORTEX_Q);
}

/* ─── Polynomial arithmetic ─────────────────────────────────────────────── */

void vortex_poly_add(vortex_poly *r,
                     const vortex_poly *a,
                     const vortex_poly *b)
{
    for (int i = 0; i < VORTEX_N; i++)
        r->coeffs[i] = _reduce((int32_t)a->coeffs[i] + b->coeffs[i]);
}

void vortex_poly_sub(vortex_poly *r,
                     const vortex_poly *a,
                     const vortex_poly *b)
{
    for (int i = 0; i < VORTEX_N; i++)
        r->coeffs[i] = _reduce((int32_t)a->coeffs[i] - b->coeffs[i]);
}

void vortex_poly_mul(vortex_poly *r,
                     const vortex_poly *a,
                     const vortex_poly *b)
{
    int32_t tmp[VORTEX_N];
    memset(tmp, 0, sizeof(tmp));

    for (int i = 0; i < VORTEX_N; i++) {
        for (int j = 0; j < VORTEX_N; j++) {
            int32_t prod = (int32_t)a->coeffs[i] * b->coeffs[j];
            int k = i + j;
            if (k < VORTEX_N)
                tmp[k] += prod;
            else
                tmp[k - VORTEX_N] -= prod;
        }
    }
    for (int i = 0; i < VORTEX_N; i++)
        r->coeffs[i] = _reduce(tmp[i]);
}

/*
 * Frobenius automorphism: σ(f(x)) = f(x³ mod x^{256}+1)
 *
 * For coefficient at index i:
 *   k = (3·i) mod 512
 *   if k < 256:  r[k]     += a[i]
 *   else:        r[k-256] -= a[i]
 *
 * This is a ring automorphism because gcd(3, 512) = 1.
 */
void vortex_poly_frobenius(vortex_poly *r, const vortex_poly *a)
{
    int32_t tmp[VORTEX_N];
    memset(tmp, 0, sizeof(tmp));

    for (int i = 0; i < VORTEX_N; i++) {
        int k = (3 * i) & 511;   /* mod 512 */
        if (k < VORTEX_N)
            tmp[k] += a->coeffs[i];
        else
            tmp[k - VORTEX_N] -= a->coeffs[i];
    }
    for (int i = 0; i < VORTEX_N; i++)
        r->coeffs[i] = _reduce(tmp[i]);
}

/* ─── Serialisation ─────────────────────────────────────────────────────── */

void vortex_poly_pack(uint8_t r[VORTEX_POLY_BYTES], const vortex_poly *a)
{
    for (int i = 0; i < 128; i++) {
        uint16_t t0 = (uint16_t)(a->coeffs[2 * i]     & 0xFFF);
        uint16_t t1 = (uint16_t)(a->coeffs[2 * i + 1] & 0xFFF);
        r[3 * i]     = (uint8_t)(t0 >> 0);
        r[3 * i + 1] = (uint8_t)((t0 >> 8) | (t1 << 4));
        r[3 * i + 2] = (uint8_t)(t1 >> 4);
    }
}

void vortex_poly_unpack(vortex_poly *r, const uint8_t a[VORTEX_POLY_BYTES])
{
    for (int i = 0; i < 128; i++) {
        r->coeffs[2 * i]     = (int16_t)( (uint16_t)a[3*i]
                                         | ((uint16_t)(a[3*i+1] & 0x0F) << 8));
        r->coeffs[2 * i + 1] = (int16_t)(  (a[3*i+1] >> 4)
                                          | ((uint16_t)a[3*i+2] << 4));
    }
}

/* ─── Compression DU = 10 bits ──────────────────────────────────────────── */

void vortex_poly_compress_u(uint8_t r[VORTEX_POLY_COMPRESSED_U],
                             const vortex_poly *a)
{
    uint16_t t[4];
    for (int i = 0; i < 64; i++) {
        for (int j = 0; j < 4; j++) {
            uint32_t c = (uint32_t)((a->coeffs[4*i+j] % VORTEX_Q
                                     + VORTEX_Q) % VORTEX_Q);
            t[j] = (uint16_t)(((c << 10) + VORTEX_Q / 2) / VORTEX_Q & 0x3FF);
        }
        r[5*i+0] = (uint8_t)( t[0]        );
        r[5*i+1] = (uint8_t)((t[0] >>  8) | (t[1] << 2));
        r[5*i+2] = (uint8_t)((t[1] >>  6) | (t[2] << 4));
        r[5*i+3] = (uint8_t)((t[2] >>  4) | (t[3] << 6));
        r[5*i+4] = (uint8_t)( t[3] >>  2);
    }
}

void vortex_poly_decompress_u(vortex_poly *r,
                               const uint8_t a[VORTEX_POLY_COMPRESSED_U])
{
    for (int i = 0; i < 64; i++) {
        uint16_t t[4];
        t[0] = ((uint16_t)a[5*i+0])       | ((uint16_t)(a[5*i+1] & 0x03) << 8);
        t[1] = ((uint16_t)a[5*i+1] >> 2)  | ((uint16_t)(a[5*i+2] & 0x0F) << 6);
        t[2] = ((uint16_t)a[5*i+2] >> 4)  | ((uint16_t)(a[5*i+3] & 0x3F) << 4);
        t[3] = ((uint16_t)a[5*i+3] >> 6)  | ((uint16_t)a[5*i+4] << 2);
        for (int j = 0; j < 4; j++)
            r->coeffs[4*i+j] = (int16_t)(
                ((uint32_t)(t[j] & 0x3FF) * VORTEX_Q + 512) >> 10);
    }
}

/* ─── Compression DV = 4 bits ───────────────────────────────────────────── */

void vortex_poly_compress_v(uint8_t r[VORTEX_POLY_COMPRESSED_V],
                             const vortex_poly *a)
{
    for (int i = 0; i < 128; i++) {
        uint32_t c0 = (uint32_t)((a->coeffs[2*i]   % VORTEX_Q + VORTEX_Q) % VORTEX_Q);
        uint32_t c1 = (uint32_t)((a->coeffs[2*i+1] % VORTEX_Q + VORTEX_Q) % VORTEX_Q);
        uint8_t  t0 = (uint8_t)(((c0 << 4) + VORTEX_Q / 2) / VORTEX_Q & 0xF);
        uint8_t  t1 = (uint8_t)(((c1 << 4) + VORTEX_Q / 2) / VORTEX_Q & 0xF);
        r[i] = t0 | (uint8_t)(t1 << 4);
    }
}

void vortex_poly_decompress_v(vortex_poly *r,
                               const uint8_t a[VORTEX_POLY_COMPRESSED_V])
{
    for (int i = 0; i < 128; i++) {
        r->coeffs[2*i]   = (int16_t)(((uint32_t)(a[i] & 0xF) * VORTEX_Q + 8) >> 4);
        r->coeffs[2*i+1] = (int16_t)(((uint32_t)(a[i] >>  4) * VORTEX_Q + 8) >> 4);
    }
}

/* ─── Message encoding ──────────────────────────────────────────────────── */

void vortex_poly_encode_msg(vortex_poly *r, const uint8_t msg[32])
{
    for (int i = 0; i < VORTEX_N; i++) {
        int bit = (msg[i / 8] >> (i & 7)) & 1;
        r->coeffs[i] = (int16_t)(bit * (VORTEX_Q >> 1));
    }
}

void vortex_poly_decode_msg(uint8_t msg[32], const vortex_poly *r)
{
    memset(msg, 0, 32);
    for (int i = 0; i < VORTEX_N; i++) {
        /* Normalise to [0, Q) */
        uint32_t t = (uint32_t)((r->coeffs[i] % VORTEX_Q + VORTEX_Q) % VORTEX_Q);
        /* round to nearest {0, Q/2}:  (2t + Q/2) / Q  mod 2 */
        uint8_t bit = (uint8_t)((((t << 1) + (uint32_t)(VORTEX_Q >> 1))
                                  / (uint32_t)VORTEX_Q) & 1);
        msg[i / 8] |= (uint8_t)(bit << (i & 7));
    }
}

/* ─── CBD sampling (SHAKE-256 PRF) ─────────────────────────────────────── */

static void _cbd_impl(vortex_poly *r, const uint8_t *buf, int eta)
{
    for (int i = 0; i < VORTEX_N; i++) {
        int a_sum = 0, b_sum = 0;
        for (int j = 0; j < eta; j++) {
            int bit_a = 2 * eta * i + j;
            int bit_b = 2 * eta * i + eta + j;
            a_sum += (buf[bit_a / 8] >> (bit_a & 7)) & 1;
            b_sum += (buf[bit_b / 8] >> (bit_b & 7)) & 1;
        }
        r->coeffs[i] = _reduce((int32_t)(a_sum - b_sum));
    }
}

void vortex_cbd3(vortex_poly *r, const uint8_t seed[32], uint8_t nonce)
{
    uint8_t extseed[33];
    uint8_t buf[192];   /* ETA1=3: 2·3·256/8 = 192 bytes */
    memcpy(extseed, seed, 32);
    extseed[32] = nonce;
    shake256(buf, 192, extseed, 33);
    _cbd_impl(r, buf, 3);
}

void vortex_cbd2(vortex_poly *r, const uint8_t seed[32], uint8_t nonce)
{
    uint8_t extseed[33];
    uint8_t buf[128];   /* ETA2=2: 2·2·256/8 = 128 bytes */
    memcpy(extseed, seed, 32);
    extseed[32] = nonce;
    shake256(buf, 128, extseed, 33);
    _cbd_impl(r, buf, 2);
}

/* ─── Base element generation (SHAKE-128 + rejection sampling) ──────────── */

void vortex_gen_base(vortex_poly *r, const uint8_t rho[32])
{
    /* Domain-separator bytes [0x00, 0x00] appended to rho (matches Python). */
    uint8_t extseed[34];
    memcpy(extseed, rho, 32);
    extseed[32] = 0x00;
    extseed[33] = 0x00;

    /* 672 bytes → 448 candidate pairs; expected ~364 accepted. */
    uint8_t buf[672];
    shake128(buf, 672, extseed, 34);

    int j = 0, pos = 0;
    while (j < VORTEX_N && pos + 3 <= 672) {
        uint16_t d1 = (uint16_t)buf[pos]
                    | ((uint16_t)(buf[pos+1] & 0x0F) << 8);
        uint16_t d2 = ((uint16_t)(buf[pos+1] >> 4))
                    | ((uint16_t)buf[pos+2] << 4);
        pos += 3;
        if (d1 < VORTEX_Q) r->coeffs[j++] = (int16_t)d1;
        if (j < VORTEX_N && d2 < VORTEX_Q) r->coeffs[j++] = (int16_t)d2;
    }
    /* Pad with 0 on the astronomically unlikely miss */
    while (j < VORTEX_N) r->coeffs[j++] = 0;
}
