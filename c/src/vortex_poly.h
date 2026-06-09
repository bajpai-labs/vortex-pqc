/**
 * vortex_poly.h — Polynomial arithmetic for VORTEX-256
 *
 * All arithmetic is in the ring R_q = Z_{3329}[x] / (x^{256}+1).
 */

#ifndef VORTEX_POLY_H
#define VORTEX_POLY_H

#include <stdint.h>
#include "../include/vortex_pqc.h"

/* A polynomial: 256 coefficients in [0, Q). */
typedef struct { int16_t coeffs[VORTEX_N]; } vortex_poly;

/* ── Arithmetic ──────────────────────────────────────────────────────────── */
void vortex_poly_add(vortex_poly *r, const vortex_poly *a, const vortex_poly *b);
void vortex_poly_sub(vortex_poly *r, const vortex_poly *a, const vortex_poly *b);
void vortex_poly_mul(vortex_poly *r, const vortex_poly *a, const vortex_poly *b);

/* Frobenius: σ(f(x)) = f(x^3 mod x^{256}+1) */
void vortex_poly_frobenius(vortex_poly *r, const vortex_poly *a);

/* ── Serialisation (12 bits/coeff uncompressed) ─────────────────────────── */
void vortex_poly_pack  (uint8_t r[VORTEX_POLY_BYTES], const vortex_poly *a);
void vortex_poly_unpack(vortex_poly *r, const uint8_t a[VORTEX_POLY_BYTES]);

/* ── Compression (DU=10 bits, DV=4 bits) ───────────────────────────────── */
void vortex_poly_compress_u  (uint8_t r[VORTEX_POLY_COMPRESSED_U], const vortex_poly *a);
void vortex_poly_decompress_u(vortex_poly *r, const uint8_t a[VORTEX_POLY_COMPRESSED_U]);
void vortex_poly_compress_v  (uint8_t r[VORTEX_POLY_COMPRESSED_V], const vortex_poly *a);
void vortex_poly_decompress_v(vortex_poly *r, const uint8_t a[VORTEX_POLY_COMPRESSED_V]);

/* ── Message encoding (1 bit per coefficient) ───────────────────────────── */
void vortex_poly_encode_msg(vortex_poly *r, const uint8_t msg[32]);
void vortex_poly_decode_msg(uint8_t msg[32], const vortex_poly *r);

/* ── Noise sampling via SHAKE-256 ───────────────────────────────────────── */
void vortex_cbd3(vortex_poly *r, const uint8_t seed[32], uint8_t nonce);
void vortex_cbd2(vortex_poly *r, const uint8_t seed[32], uint8_t nonce);

/* ── Base element generation ────────────────────────────────────────────── */
void vortex_gen_base(vortex_poly *r, const uint8_t rho[32]);

#endif /* VORTEX_POLY_H */
