"""
setup.py — optional C extension for VORTEX-256.

The pure-Python implementation in vortex_pqc._pure works without any
compilation step.  This file builds an optional native extension
(vortex_pqc._native) for higher throughput.
"""

import platform
from setuptools import Extension, setup

_VENDOR = "c/vendor/sha3"

NATIVE_SOURCES = [
    "c/src/python_module.c",
    "c/src/vortex_core.c",
    "c/src/vortex_poly.c",
    f"{_VENDOR}/fips202.c",
    f"{_VENDOR}/randombytes.c",
]

extra_compile_args = ["-O3", "-Wall"]
if platform.machine() in {"arm64", "aarch64"}:
    extra_compile_args.append("-mcpu=native")

setup(
    ext_modules=[
        Extension(
            "vortex_pqc._native",
            sources=NATIVE_SOURCES,
            include_dirs=[
                "c/include",
                "c/src",
                _VENDOR,
            ],
            extra_compile_args=extra_compile_args,
        )
    ]
)
