CC     ?= cc
ARCH   := $(shell uname -m)
CFLAGS ?= -Wall -Wextra -Wpedantic -O3 -Iinclude -Isrc \
           -Ivendor/sha3
ifeq ($(ARCH),arm64)
CFLAGS += -mcpu=native
endif
ifeq ($(ARCH),aarch64)
CFLAGS += -mcpu=native
endif

VENDOR := vendor/sha3
VENDOR_SRCS := \
	$(VENDOR)/fips202.c \
	$(VENDOR)/randombytes.c

LIB_SRCS := src/vortex_core.c src/vortex_poly.c
LIB_OBJS := $(LIB_SRCS:.c=.o) $(VENDOR_SRCS:.c=.o)

.PHONY: all lib test demo clean

all: lib test demo

# ── Static library ────────────────────────────────────────────────────────
lib: build/libvortex_pqc.a

build/libvortex_pqc.a: $(LIB_OBJS)
	mkdir -p build
	$(AR) rcs $@ $^

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c $< -o $@

$(VENDOR)/%.o: $(VENDOR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# ── Test ──────────────────────────────────────────────────────────────────
tests/test_vortex: tests/test_vortex.c build/libvortex_pqc.a
	$(CC) $(CFLAGS) $< build/libvortex_pqc.a -o $@

test: lib tests/test_vortex
	./tests/test_vortex

# ── Demo ──────────────────────────────────────────────────────────────────
examples/demo: examples/demo.c build/libvortex_pqc.a
	$(CC) $(CFLAGS) $< build/libvortex_pqc.a -o $@

demo: examples/demo
	./examples/demo

# ── Benchmark ─────────────────────────────────────────────────────────────
tests/test_bench: tests/test_bench.c build/libvortex_pqc.a
	$(CC) $(CFLAGS) -g $< build/libvortex_pqc.a -o $@

bench: lib tests/test_bench
	./tests/test_bench

clean:
	rm -rf build src/*.o $(VENDOR)/*.o \
	       tests/test_vortex examples/demo tests/test_bench
