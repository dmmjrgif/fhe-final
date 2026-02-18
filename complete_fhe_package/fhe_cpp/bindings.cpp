/*
 * Python bindings for FHE C++ multiplication module
 * Uses pybind11 seamless Python/C++ integration
 * FIXED: Removed 'const' qualifiers for mutable BFVMultiplier methods
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "ntt.h"
#include "bfv_mult.h"

namespace py = pybind11;
using namespace fhe_cpp;

// Helper to convert numpy arrays to std::vector
std::vector<ModInt> numpy_to_vector(py::array_t<int64_t> arr) {
    auto buf = arr.request();
    int64_t* ptr = static_cast<int64_t*>(buf.ptr);
    return std::vector<ModInt>(ptr, ptr + buf.size);
}

// Helper to convert std::vector to numpy array
py::array_t<int64_t> vector_to_numpy(const std::vector<ModInt>& vec) {
    return py::array_t<int64_t>(vec.size(), vec.data());
}

PYBIND11_MODULE(fhe_fast_mult, m) {
    m.doc() = "Fast FHE multiplication using NTT (C++ backend)";

    // NTT class bindings
    py::class_<NTT>(m, "NTT")
        .def(py::init<int, ModInt>(),
             py::arg("N"), py::arg("q"),
             "Initialize NTT with polynomial degree N and modulus q")

        .def("multiply", [](const NTT& ntt,
                           py::array_t<int64_t> a,
                           py::array_t<int64_t> b) {
            auto vec_a = numpy_to_vector(a);
            auto vec_b = numpy_to_vector(b);
            auto result = ntt.multiply(vec_a, vec_b);
            return vector_to_numpy(result);
        }, "Multiply two polynomials using NTT")

        .def("add", [](const NTT& ntt,
                      py::array_t<int64_t> a,
                      py::array_t<int64_t> b) {
            auto vec_a = numpy_to_vector(a);
            auto vec_b = numpy_to_vector(b);
            auto result = ntt.add(vec_a, vec_b);
            return vector_to_numpy(result);
        }, "Add two polynomials")

        .def("subtract", [](const NTT& ntt,
                           py::array_t<int64_t> a,
                           py::array_t<int64_t> b) {
            auto vec_a = numpy_to_vector(a);
            auto vec_b = numpy_to_vector(b);
            auto result = ntt.subtract(vec_a, vec_b);
            return vector_to_numpy(result);
        }, "Subtract two polynomials")

        .def("scalar_mul", [](const NTT& ntt,
                             py::array_t<int64_t> a,
                             int64_t scalar) {
            auto vec_a = numpy_to_vector(a);
            auto result = ntt.scalar_mul(vec_a, scalar);
            return vector_to_numpy(result);
        }, "Multiply polynomial by scalar")

        .def("is_valid", &NTT::is_valid,
             "Check if NTT is properly initialized")

        .def("get_N", &NTT::get_N, "Get polynomial degree")
        .def("get_q", &NTT::get_q, "Get modulus");

    // BFVMultiplier class bindings
    py::class_<BFVMultiplier>(m, "BFVMultiplier")
        .def(py::init<int, ModInt, ModInt>(),
             py::arg("N"), py::arg("q"), py::arg("t"),
             "Initialize BFV multiplier with N, q (ciphertext modulus), t (plaintext modulus)")

        // FIXED: Removed 'const' from BFVMultiplier& mult
        .def("multiply_ciphertexts", [](BFVMultiplier& mult,
                                        py::array_t<int64_t> c1_0,
                                        py::array_t<int64_t> c1_1,
                                        py::array_t<int64_t> c2_0,
                                        py::array_t<int64_t> c2_1) {
            auto result = mult.multiply_ciphertexts(
                numpy_to_vector(c1_0),
                numpy_to_vector(c1_1),
                numpy_to_vector(c2_0),
                numpy_to_vector(c2_1)
            );

            // Return tuple of 3 numpy arrays
            return py::make_tuple(
                vector_to_numpy(result[0]),
                vector_to_numpy(result[1]),
                vector_to_numpy(result[2])
            );
        }, "Multiply two ciphertexts (returns d0, d1, d2)")

        // FIXED: Removed 'const' from BFVMultiplier& mult
        .def("relinearize", [](BFVMultiplier& mult,
                              py::array_t<int64_t> d0,
                              py::array_t<int64_t> d1,
                              py::array_t<int64_t> d2,
                              py::array_t<int64_t> rk0,
                              py::array_t<int64_t> rk1) {
            std::vector<std::vector<ModInt>> relin_key = {
                numpy_to_vector(rk0),
                numpy_to_vector(rk1)
            };

            auto result = mult.relinearize(
                numpy_to_vector(d0),
                numpy_to_vector(d1),
                numpy_to_vector(d2),
                relin_key
            );

            return py::make_tuple(
                vector_to_numpy(result[0]),
                vector_to_numpy(result[1])
            );
        }, "Relinearize (d0, d1, d2) to (c0, c1)")

        .def("get_delta", &BFVMultiplier::get_delta,
             "Get delta = floor(q/t)");

    // Utility functions
    m.def("find_ntt_prime", [](int N) -> int64_t {
        // Find a prime q such that q = 1 (mod 2N)
        int64_t q = 2 * N + 1;

        auto is_prime = [](int64_t n) {
            if (n < 2) return false;
            if (n == 2) return true;
            if (n % 2 == 0) return false;
            for (int64_t i = 3; i * i <= n; i += 2) {
                if (n % i == 0) return false;
            }
            return true;
        };

        while (!is_prime(q)) {
            q += 2 * N;
        }

        return q;
    }, "Find a prime suitable for NTT with given N");
}
