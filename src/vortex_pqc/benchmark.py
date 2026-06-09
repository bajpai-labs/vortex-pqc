"""Throughput benchmarking for VORTEX-256 KEM operations."""

import time
import statistics
import vortex_pqc

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

