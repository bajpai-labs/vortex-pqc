/**
 * demo.c — VORTEX-256 key exchange demo
 *
 * Demonstrates a full Alice-sends-to-Bob key exchange using the novel
 * RotMLWE-based KEM.
 */

#include <stdio.h>
#include <string.h>
#include "vortex_pqc.h"

static void print_hex(const char *label, const uint8_t *buf, size_t len)
{
    printf("%s (first 16 bytes): ", label);
    for (size_t i = 0; i < 16 && i < len; i++)
        printf("%02x", buf[i]);
    printf("...\n");
}

int main(void)
{
    uint8_t alice_pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t alice_sk[VORTEX_PRIVATE_KEY_BYTES];
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t bob_ss[VORTEX_SHARED_SECRET_BYTES];
    uint8_t alice_ss[VORTEX_SHARED_SECRET_BYTES];

    printf("╔══════════════════════════════════════════════════════╗\n");
    printf("║          VORTEX-256  Key Exchange Demo               ║\n");
    printf("║  Novel RotMLWE post-quantum KEM  (Bajpai Labs)       ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n\n");

    printf("[Alice] Generating VORTEX-256 key pair…\n");
    vortex_keypair(alice_pk, alice_sk);
    print_hex("  public key", alice_pk, VORTEX_PUBLIC_KEY_BYTES);
    printf("  Public key size  : %d bytes\n", VORTEX_PUBLIC_KEY_BYTES);
    printf("  Private key size : %d bytes\n\n", VORTEX_PRIVATE_KEY_BYTES);

    printf("[Bob] Encapsulating shared secret to Alice's public key…\n");
    vortex_enc(alice_pk, ct, bob_ss);
    print_hex("  ciphertext",    ct,     VORTEX_CIPHERTEXT_BYTES);
    print_hex("  Bob's secret",  bob_ss, VORTEX_SHARED_SECRET_BYTES);
    printf("  Ciphertext size  : %d bytes\n\n", VORTEX_CIPHERTEXT_BYTES);

    printf("[Alice] Decapsulating ciphertext…\n");
    vortex_dec(ct, alice_sk, alice_ss);
    print_hex("  Alice's secret", alice_ss, VORTEX_SHARED_SECRET_BYTES);

    if (memcmp(bob_ss, alice_ss, VORTEX_SHARED_SECRET_BYTES) == 0)
        printf("\n✓ Shared secrets match!  Key exchange succeeded.\n");
    else
        printf("\n✗ Shared secrets differ!  Key exchange FAILED.\n");

    printf("\nAlgorithm parameters (RotMLWE):\n");
    printf("  Ring : Z_{%d}[x] / (x^{%d} + 1)\n", VORTEX_Q, VORTEX_N);
    printf("  K    : %d Frobenius rotations\n",      VORTEX_K);
    printf("  η₁   : %d  (keygen noise)\n",          VORTEX_ETA1);
    printf("  η₂   : %d  (encaps noise)\n",          VORTEX_ETA2);
    return 0;
}
