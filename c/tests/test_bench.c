/**
 * test_bench.c — VORTEX-256 C library micro-architectural benchmark
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "vortex_pqc.h"

#define WARMUP_ITERATIONS 10000
#define BENCHMARK_ITERATIONS 100000

#include <inttypes.h>

static inline uint64_t rdtsc_start(void) {
    uint32_t cycles_high, cycles_low;
    __asm__ __volatile__ (
        "CPUID\n\t"
        "RDTSC\n\t"
        "mov %%edx, %0\n\t"
        "mov %%eax, %1\n\t"
        : "=r" (cycles_high), "=r" (cycles_low)
        :: "rax", "rbx", "rcx", "rdx"
    );
    return ((uint64_t)cycles_high << 32) | cycles_low;
}

static inline uint64_t rdtsc_end(void) {
    uint32_t cycles_high, cycles_low;
    __asm__ __volatile__ (
        "RDTSCP\n\t"
        "mov %%edx, %0\n\t"
        "mov %%eax, %1\n\t"
        "CPUID\n\t"
        : "=r" (cycles_high), "=r" (cycles_low)
        :: "rax", "rbx", "rcx", "rdx"
    );
    return ((uint64_t)cycles_high << 32) | cycles_low;
}

int compare_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a;
    uint64_t y = *(const uint64_t *)b;
    if (x < y) return -1;
    if (x > y) return 1;
    return 0;
}

uint64_t median(uint64_t *values, int count) {
    qsort(values, count, sizeof(uint64_t), compare_u64);
    if (count % 2 == 0) {
        return (values[count / 2 - 1] + values[count / 2]) / 2;
    }
    return values[count / 2];
}

void bench_keygen(void) {
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];
    uint64_t timings[BENCHMARK_ITERATIONS];
    uint64_t start, end;

    for (int i = 0; i < WARMUP_ITERATIONS; ++i) {
        vortex_keypair(pk, sk);
    }

    for (int i = 0; i < BENCHMARK_ITERATIONS; ++i) {
        start = rdtsc_start();
        vortex_keypair(pk, sk);
        end = rdtsc_end();
        timings[i] = end - start;
    }

    printf("keygen: %" PRIu64 " cycles\n", median(timings, BENCHMARK_ITERATIONS));
}

void bench_encap(void) {
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ss_enc[VORTEX_SHARED_SECRET_BYTES];
    uint64_t timings[BENCHMARK_ITERATIONS];
    uint64_t start, end;

    vortex_keypair(pk, sk);

    for (int i = 0; i < WARMUP_ITERATIONS; ++i) {
        vortex_enc(pk, ct, ss_enc);
    }

    for (int i = 0; i < BENCHMARK_ITERATIONS; ++i) {
        start = rdtsc_start();
        vortex_enc(pk, ct, ss_enc);
        end = rdtsc_end();
        timings[i] = end - start;
    }

    printf("encap:  %" PRIu64 " cycles\n", median(timings, BENCHMARK_ITERATIONS));
}

void bench_decap(void) {
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ss_enc[VORTEX_SHARED_SECRET_BYTES];
    uint8_t ss_dec[VORTEX_SHARED_SECRET_BYTES];
    uint64_t timings[BENCHMARK_ITERATIONS];
    uint64_t start, end;

    vortex_keypair(pk, sk);
    vortex_enc(pk, ct, ss_enc);

    for (int i = 0; i < WARMUP_ITERATIONS; ++i) {
        vortex_dec(ct, sk, ss_dec);
    }

    for (int i = 0; i < BENCHMARK_ITERATIONS; ++i) {
        start = rdtsc_start();
        vortex_dec(ct, sk, ss_dec);
        end = rdtsc_end();
        timings[i] = end - start;
    }

    printf("decap:  %" PRIu64 " cycles\n", median(timings, BENCHMARK_ITERATIONS));
}

int main(void) {
    printf("=== VORTEX-256 C library benchmark ===\n");
    bench_keygen();
    bench_encap();
    bench_decap();
    return 0;
}
