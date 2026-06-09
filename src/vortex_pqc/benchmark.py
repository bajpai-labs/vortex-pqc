"""Throughput benchmarking for VORTEX-256 KEM operations."""

import statistics
import time

from .core import decapsulate, encapsulate, generate_keypair


def benchmark_throughput(operations: int = 50) -> dict:
    """
    Measure keygen, encapsulation, and decapsulation throughput.

    Returns mean ops/s and a 95% confidence interval for each operation.
    """
    if operations < 1:
        raise ValueError("operations must be >= 1")

    def _measure(op_callable, n: int) -> dict:
        for _ in range(min(100, n)):
            op_callable()

        ops_per_sec = []
        for _ in range(n):
            start = time.perf_counter_ns()
            op_callable()
            elapsed_ns = time.perf_counter_ns() - start
            if elapsed_ns > 0:
                ops_per_sec.append(1_000_000_000 / elapsed_ns)

        mean = statistics.mean(ops_per_sec)
        if len(ops_per_sec) > 1:
            ci = 1.96 * statistics.stdev(ops_per_sec) / (len(ops_per_sec) ** 0.5)
        else:
            ci = 0.0
        return {"mean_ops": mean, "confidence_interval": ci}

    kp = generate_keypair()
    ct = encapsulate(kp.public_key)
    pk, sk, ct_data = kp.public_key, kp.private_key, ct.data

    return {
        "keygen": _measure(generate_keypair, operations),
        "encaps": _measure(lambda: encapsulate(pk), operations),
        "decaps": _measure(lambda: decapsulate(ct_data, sk), operations),
    }


def run_profile(op_callable, iterations=10000):
    """
    Runs a profiling test for a given operation.

    Args:
        op_callable (function): The operation to be benchmarked.
        iterations (int): The number of iterations to run.

    Returns:
        A tuple containing the average latency in microseconds and operations per second.
    """
    # Warm-up phase
    for _ in range(1000):
        op_callable()
    
    timings = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        op_callable()
        end = time.perf_counter_ns()
        timings.append(end - start)
    
    median_latency_ns = statistics.median(timings)
    
    # Convert nanoseconds to microseconds for average latency
    avg_latency_us = median_latency_ns / 1000
    
    # Calculate operations per second
    ops_per_sec = 1_000_000_000 / median_latency_ns if median_latency_ns > 0 else 0
    
    return avg_latency_us, ops_per_sec

def main():
    """
    Main function to run the benchmarks.
    """
    import vortex_pqc

    print("--- VORTEX-PQC Python Benchmark ---")

    # --- Pure Python Implementation ---
    print("\n[+] Benchmarking pure-Python backend...")
    vortex_pqc.core._be = vortex_pqc._pure
    
    # Keygen
    avg_latency_us, ops_per_sec = run_profile(vortex_pqc.generate_keypair)
    print(f"  keygen: {avg_latency_us:.2f} µs/op  ({ops_per_sec:.2f} ops/sec)")

    # Encap
    kp = vortex_pqc.generate_keypair()
    avg_latency_us, ops_per_sec = run_profile(lambda: vortex_pqc.encapsulate(kp.public_key))
    print(f"  encap:  {avg_latency_us:.2f} µs/op  ({ops_per_sec:.2f} ops/sec)")

    # Decap
    ct = vortex_pqc.encapsulate(kp.public_key)
    avg_latency_us, ops_per_sec = run_profile(lambda: vortex_pqc.decapsulate(ct.data, kp.private_key))
    print(f"  decap:  {avg_latency_us:.2f} µs/op  ({ops_per_sec:.2f} ops/sec)")

    # --- Native C Implementation ---
    try:
        vortex_pqc.core._be = vortex_pqc._native
        print("\n[+] Benchmarking native C backend...")
        
        # Keygen
        avg_latency_us, ops_per_sec = run_profile(vortex_pqc.generate_keypair)
        print(f"  keygen: {avg_latency_us:.2f} µs/op  ({ops_per_sec:.2f} ops/sec)")

        # Encap
        kp = vortex_pqc.generate_keypair()
        avg_latency_us, ops_per_sec = run_profile(lambda: vortex_pqc.encapsulate(kp.public_key))
        print(f"  encap:  {avg_latency_us:.2f} µs/op  ({ops_per_sec:.2f} ops/sec)")

        # Decap
        ct = vortex_pqc.encapsulate(kp.public_key)
        avg_latency_us, ops_per_sec = run_profile(lambda: vortex_pqc.decapsulate(ct.data, kp.private_key))
        print(f"  decap:  {avg_latency_us:.2f} µs/op  ({ops_per_sec:.2f} ops/sec)")

    except ImportError:
        print("\n[-] Native C backend not available. Skipping.")

if __name__ == "__main__":
    main()

