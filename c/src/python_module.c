/**
 * python_module.c — Python C extension for VORTEX-256
 *
 * Exposes keypair(), encapsulate(), decapsulate(), backend_name()
 * matching the interface of the Kyber _native extension so core.py
 * can dispatch transparently.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "../include/vortex_pqc.h"

static PyObject *py_keypair(PyObject *self, PyObject *Py_UNUSED(args))
{
    uint8_t pk[VORTEX_PUBLIC_KEY_BYTES];
    uint8_t sk[VORTEX_PRIVATE_KEY_BYTES];

    (void)self;
    if (vortex_keypair(pk, sk) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "vortex keypair failed");
        return NULL;
    }
    return Py_BuildValue(
        "y#y#",
        pk, (Py_ssize_t)VORTEX_PUBLIC_KEY_BYTES,
        sk, (Py_ssize_t)VORTEX_PRIVATE_KEY_BYTES
    );
}

static PyObject *py_encapsulate(PyObject *self, PyObject *args)
{
    const char *pk_buf = NULL;
    Py_ssize_t  pk_len = 0;
    uint8_t ct[VORTEX_CIPHERTEXT_BYTES];
    uint8_t ss[VORTEX_SHARED_SECRET_BYTES];

    (void)self;
    if (!PyArg_ParseTuple(args, "y#", &pk_buf, &pk_len))
        return NULL;
    if (pk_len != VORTEX_PUBLIC_KEY_BYTES) {
        PyErr_SetString(PyExc_ValueError, "invalid public key length");
        return NULL;
    }
    if (vortex_enc((const uint8_t *)pk_buf, ct, ss) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "vortex encapsulation failed");
        return NULL;
    }
    return Py_BuildValue(
        "y#y#",
        ct, (Py_ssize_t)VORTEX_CIPHERTEXT_BYTES,
        ss, (Py_ssize_t)VORTEX_SHARED_SECRET_BYTES
    );
}

static PyObject *py_decapsulate(PyObject *self, PyObject *args)
{
    const char *ct_buf = NULL, *sk_buf = NULL;
    Py_ssize_t  ct_len = 0,    sk_len = 0;
    uint8_t ss[VORTEX_SHARED_SECRET_BYTES];
    PyObject *result = NULL;

    (void)self;
    if (!PyArg_ParseTuple(args, "y#y#", &ct_buf, &ct_len, &sk_buf, &sk_len))
        return NULL;
    if (ct_len != VORTEX_CIPHERTEXT_BYTES) {
        PyErr_SetString(PyExc_ValueError, "invalid ciphertext length");
        return NULL;
    }
    if (sk_len != VORTEX_PRIVATE_KEY_BYTES) {
        PyErr_SetString(PyExc_ValueError, "invalid private key length");
        return NULL;
    }
    vortex_dec((const uint8_t *)ct_buf, (const uint8_t *)sk_buf, ss);
    result = PyBytes_FromStringAndSize((const char *)ss,
                                       (Py_ssize_t)VORTEX_SHARED_SECRET_BYTES);
    /* Zero the stack copy of ss */
    volatile uint8_t *p = ss;
    for (int i = 0; i < VORTEX_SHARED_SECRET_BYTES; i++) p[i] = 0;
    return result;
}

static PyObject *py_backend_name(PyObject *self, PyObject *Py_UNUSED(args))
{
    (void)self;
#if defined(__aarch64__) || defined(__arm64__)
    return PyUnicode_FromString("vortex-pqc-native-aarch64");
#elif defined(__AVX2__)
    return PyUnicode_FromString("vortex-pqc-native-avx2");
#else
    return PyUnicode_FromString("vortex-pqc-native-x86_64");
#endif
}

static PyMethodDef VortexMethods[] = {
    {"keypair",      py_keypair,      METH_NOARGS,  "Generate a VORTEX-256 key pair."},
    {"encapsulate",  py_encapsulate,  METH_VARARGS, "Encapsulate a shared secret."},
    {"decapsulate",  py_decapsulate,  METH_VARARGS, "Decapsulate a shared secret."},
    {"backend_name", py_backend_name, METH_NOARGS,  "Return active backend string."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef vortex_module = {
    PyModuleDef_HEAD_INIT,
    "_native",
    "VORTEX-256 native RotMLWE implementation.",
    -1,
    VortexMethods
};

PyMODINIT_FUNC PyInit__native(void)
{
    return PyModule_Create(&vortex_module);
}
