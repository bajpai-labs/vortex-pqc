/**
 * test_vortex.c — VORTEX-256 C library self-test
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "vortex_pqc.h"

static int test_round_trip(void)
{
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ss_enc[VORTEX_SHARED_SECRET_BYTES];
    uint8_t ss_dec[VORTEX_SHARED_SECRET_BYTES];

    if (vortex_keypair(pk, sk) != 0) {
        fprintf(stderr, "FAIL: keypair returned error\n");
        return 1;
    }
    if (vortex_enc(pk, ct, ss_enc) != 0) {
        fprintf(stderr, "FAIL: enc returned error\n");
        return 1;
    }
    if (vortex_dec(ct, sk, ss_dec) != 0) {
        fprintf(stderr, "FAIL: dec returned error\n");
        return 1;
    }
    if (memcmp(ss_enc, ss_dec, VORTEX_SHARED_SECRET_BYTES) != 0) {
        fprintf(stderr, "FAIL: shared secrets differ\n");
        return 1;
    }
    printf("PASS: round-trip (enc == dec shared secret)\n");
    return 0;
}

static int test_tamper_rejection(void)
{
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ss_enc[VORTEX_SHARED_SECRET_BYTES];
    uint8_t ss_dec[VORTEX_SHARED_SECRET_BYTES];

    vortex_keypair(pk, sk);
    vortex_enc(pk, ct, ss_enc);

    /* Flip first byte of ciphertext */
    ct[0] ^= 0x01;
    vortex_dec(ct, sk, ss_dec);

    if (memcmp(ss_enc, ss_dec, VORTEX_SHARED_SECRET_BYTES) == 0) {
        fprintf(stderr, "FAIL: tampered ct produced same secret (no rejection)\n");
        return 1;
    }
    printf("PASS: implicit rejection on tampered ciphertext\n");
    return 0;
}

static int test_size_constants(void)
{
    int ok = 1;
#define CHECK(name, val, expected) \
    if ((val) != (expected)) { \
        fprintf(stderr, "FAIL: %s = %d, expected %d\n", name, val, expected); \
        ok = 0; \
    }
    CHECK("PUBLIC_KEY_BYTES",    VORTEX_PUBLIC_KEY_BYTES,    800);
    CHECK("PRIVATE_KEY_BYTES",   VORTEX_PRIVATE_KEY_BYTES,   1248);
    CHECK("CIPHERTEXT_BYTES",    VORTEX_CIPHERTEXT_BYTES,    768);
    CHECK("SHARED_SECRET_BYTES", VORTEX_SHARED_SECRET_BYTES, 32);
#undef CHECK
    if (ok) printf("PASS: size constants match specification\n");
    return !ok;
}

int main(void)
{
    int failures = 0;
    printf("=== VORTEX-256 C library tests ===\n");
    failures += test_size_constants();
    failures += test_round_trip();
    failures += test_tamper_rejection();

    if (failures == 0)
        printf("\nAll tests passed.\n");
    else
        fprintf(stderr, "\n%d test(s) FAILED.\n", failures);
    return failures;
}
