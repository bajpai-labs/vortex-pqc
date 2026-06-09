"""Throughput benchmarking for VORTEX-256 KEM operations."""

from __future__ import annotations

import statistics
import time
from typing import Callable, Dict, List, Sequence, TypeVar

from .core import decapsulate, encapsulate, generate_keypair

WARMUP_ITERATIONS = 5
CONFIDENCE_LEVEL  = 0.99

T = TypeVar("T")


def benchmark_throughput(operations: int) -> Dict[str, Dict[str, float]]:
    """Measure keygen / encaps / decaps throughput over *operations* iterations.

    Returns a dict mapping operation name → {"mean_ops": float, "confidence_interval": float}.
    """
    if operations < 1:
        raise ValueError("operations must be at least 1")

    keypairs   = [generate_keypair() for _ in range(operations)]
    pub_keys   = [kp.public_key for kp in keypairs]
    encapsulated = [encapsulate(pk) for pk in pub_keys]

    return {
        "keygen": _analyze(_time_op(generate_keypair, operations)),
        "encaps": _analyze(_time_op(lambda pk: encapsulate(pk), operations, pub_keys)),
        "decaps": _analyze(
            _time_op(
                lambda ct, sk: decapsulate(ct.data, sk),
                operations,
                list(zip(encapsulated, [kp.private_key for kp in keypairs])),
            )
        ),
    }


def _time_op(
    func: Callable[..., T],
    operations: int,
    inputs: Sequence = (),
) -> List[float]:
    def _call(item: object) -> None:
        if isinstance(item, tuple):
            func(*item)
        elif item is not None:
            func(item)
        else:
            func()

    first = inputs[0] if inputs else None
    for _ in range(WARMUP_ITERATIONS):
        _call(first)

    durations: List[float] = []
    for item in (inputs or ([None] * operations)):
        t0 = time.perf_counter()
        _call(item)
        durations.append(time.perf_counter() - t0)
    return durations


def _analyze(durations: Sequence[float]) -> Dict[str, float]:
    if not durations:
        return {"mean_ops": 0.0, "confidence_interval": 0.0}
    mean = statistics.mean(durations)
    if len(durations) < 2:
        return {"mean_ops": 1 / mean, "confidence_interval": 0.0}
    stdev  = statistics.stdev(durations)
    z_val  = statistics.NormalDist().inv_cdf((1 + CONFIDENCE_LEVEL) / 2)
    margin = (z_val * stdev) / (len(durations) ** 0.5)
    return {"mean_ops": 1 / mean, "confidence_interval": margin / mean}
