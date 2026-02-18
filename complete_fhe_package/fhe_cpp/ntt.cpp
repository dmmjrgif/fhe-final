/*
 * NTT Implementation - Corrected for BFV Negacyclic Ring (X^N + 1)
 * Windows-Compatible
 */

#include "ntt.h"
#include <algorithm>
#include <cmath>
#include <iostream>

// Windows Intrinsics
#ifdef _MSC_VER
#include <intrin.h>
#pragma intrinsic(_umul128)
#pragma intrinsic(_udiv128)
#endif

namespace fhe_cpp {

ModInt extended_gcd(ModInt a, ModInt b, ModInt& x, ModInt& y) {
    if (b == 0) {
        x = 1;
        y = 0;
        return a;
    }
    ModInt x1, y1;
    ModInt gcd = extended_gcd(b, a % b, x1, y1);
    x = y1;
    y = x1 - (a / b) * y1;
    return gcd;
}

NTT::NTT(int N, ModInt q) : N(N), q(q) {
    if ((N & (N - 1)) != 0) throw std::invalid_argument("N must be power of 2");
    if ((q - 1) % (2 * N) != 0) throw std::invalid_argument("q must be 1 (mod 2N)");

    // 1. Find 2N-th root of unity (psi)
    ModInt root = find_primitive_root();
    psi = mod_exp(root, (q - 1) / (2 * N));
    psi_inv = mod_inv(psi);

    // 2. Compute N-th root (omega = psi^2) for the standard NTT core
    omega = mod_mul(psi, psi);
    omega_inv = mod_inv(omega);
    N_inv = mod_inv(N);

    // 3. Precompute tables
    psi_powers.resize(N);
    psi_inv_powers.resize(N);
    omega_powers.resize(N);
    omega_inv_powers.resize(N);

    ModInt curr_psi = 1;
    ModInt curr_psi_inv = 1;
    ModInt curr_omega = 1;
    ModInt curr_omega_inv = 1;

    for (int i = 0; i < N; i++) {
        psi_powers[i] = curr_psi;
        psi_inv_powers[i] = curr_psi_inv;
        omega_powers[i] = curr_omega;
        omega_inv_powers[i] = curr_omega_inv;

        curr_psi = mod_mul(curr_psi, psi);
        curr_psi_inv = mod_mul(curr_psi_inv, psi_inv);
        curr_omega = mod_mul(curr_omega, omega);
        curr_omega_inv = mod_mul(curr_omega_inv, omega_inv);
    }
}

ModInt NTT::mod_add(ModInt a, ModInt b) const {
    ModInt res = (a + b);
    return (res >= q) ? res - q : res;
}

ModInt NTT::mod_sub(ModInt a, ModInt b) const {
    return (a >= b) ? a - b : a - b + q;
}

ModInt NTT::mod_mul(ModInt a, ModInt b) const {
#ifdef _MSC_VER
    unsigned __int64 high, rem;
    unsigned __int64 low = _umul128((unsigned __int64)a, (unsigned __int64)b, &high);
    _udiv128(high, low, (unsigned __int64)q, &rem);
    return (ModInt)rem;
#else
    unsigned __int128 res = (unsigned __int128)a * b;
    return (ModInt)(res % q);
#endif
}

ModInt NTT::mod_exp(ModInt base, ModInt exp) const {
    ModInt res = 1;
    base %= q;
    while (exp > 0) {
        if (exp % 2 == 1) res = mod_mul(res, base);
        base = mod_mul(base, base);
        exp /= 2;
    }
    return res;
}

ModInt NTT::mod_inv(ModInt a) const {
    ModInt x, y;
    extended_gcd(a, q, x, y);
    return (x % q + q) % q;
}

ModInt NTT::find_primitive_root() {
    ModInt phi = q - 1;
    ModInt target_order = 2 * N;
    for (ModInt g = 2; g < q; g++) {
        ModInt val = mod_exp(g, phi / target_order);
        if (mod_exp(val, target_order) == 1 && mod_exp(val, N) != 1) return val;
    }
    return 0;
}

int NTT::bit_reverse(int x, int log_n) const {
    int res = 0;
    for (int i = 0; i < log_n; i++) {
        res = (res << 1) | (x & 1);
        x >>= 1;
    }
    return res;
}

void NTT::bit_reverse_copy(std::vector<ModInt>& a) const {
    int log_n = 0;
    int temp = N;
    while (temp > 1) { log_n++; temp >>= 1; }

    for (int i = 0; i < N; i++) {
        int rev = bit_reverse(i, log_n);
        if (i < rev) std::swap(a[i], a[rev]);
    }
}

// Standard Cooley-Tukey Butterfly
void NTT::ntt_core(std::vector<ModInt>& a, const std::vector<ModInt>& roots) const {
    bit_reverse_copy(a);

    for (int s = 1; s <= std::log2(N); s++) {
        int m = 1 << s;
        int m2 = m >> 1;

        // Stride through the precomputed roots (Cooley-Tukey optimization)
        int root_step = N / m;

        for (int k = 0; k < N; k += m) {
            for (int j = 0; j < m2; j++) {
                ModInt w = roots[j * root_step];
                ModInt t = mod_mul(w, a[k + j + m2]);
                ModInt u = a[k + j];

                a[k + j] = mod_add(u, t);
                a[k + j + m2] = mod_sub(u, t);
            }
        }
    }
}

void NTT::forward(std::vector<ModInt>& a) const {
    // Negacyclic Pre-processing: Multiply by psi^i
    for (int i = 0; i < N; i++) {
        a[i] = mod_mul(a[i], psi_powers[i]);
    }

    // Standard NTT
    ntt_core(a, omega_powers);
}

void NTT::inverse(std::vector<ModInt>& a) const {
    // Standard Inverse NTT
    ntt_core(a, omega_inv_powers);

    // Scale by N^-1 and Post-process (Multiply by psi^-i)
    for (int i = 0; i < N; i++) {
        ModInt val = mod_mul(a[i], N_inv);
        a[i] = mod_mul(val, psi_inv_powers[i]);
    }
}

std::vector<ModInt> NTT::multiply(const std::vector<ModInt>& a,
                                   const std::vector<ModInt>& b) const {
    std::vector<ModInt> a_ntt = a;
    std::vector<ModInt> b_ntt = b;

    forward(a_ntt);
    forward(b_ntt);

    for (int i = 0; i < N; i++) {
        a_ntt[i] = mod_mul(a_ntt[i], b_ntt[i]);
    }

    inverse(a_ntt);
    return a_ntt;
}

std::vector<ModInt> NTT::add(const std::vector<ModInt>& a, const std::vector<ModInt>& b) const {
    std::vector<ModInt> res(a.size());
    for (size_t i = 0; i < a.size(); i++) res[i] = mod_add(a[i], b[i]);
    return res;
}

std::vector<ModInt> NTT::subtract(const std::vector<ModInt>& a, const std::vector<ModInt>& b) const {
    std::vector<ModInt> res(a.size());
    for (size_t i = 0; i < a.size(); i++) res[i] = mod_sub(a[i], b[i]);
    return res;
}

std::vector<ModInt> NTT::scalar_mul(const std::vector<ModInt>& a, ModInt scalar) const {
    std::vector<ModInt> res(a.size());
    for (size_t i = 0; i < a.size(); i++) res[i] = mod_mul(a[i], scalar);
    return res;
}

bool NTT::is_valid() const {
    return psi != 0 && N > 0;
}

} // namespace fhe_cpp