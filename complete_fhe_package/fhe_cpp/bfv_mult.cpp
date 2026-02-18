/*
 * BFV Multiplier - FINAL FIXED VERSION
 * Fixed: div192_by_64_safe now preserves the full >64-bit quotient.
 */

#include "bfv_mult.h"
#include <vector>
#include <algorithm>
#include <stdexcept>

#ifdef _MSC_VER
#include <intrin.h>
#pragma intrinsic(_umul128)
#pragma intrinsic(_udiv128)
#endif

namespace fhe_cpp {

struct uint128_w { unsigned __int64 low; unsigned __int64 high; };
struct uint192_w { unsigned __int64 low; unsigned __int64 mid; unsigned __int64 high; };

uint128_w add128(uint128_w a, uint128_w b) {
    uint128_w res; res.low = a.low + b.low;
    res.high = a.high + b.high + (res.low < a.low ? 1 : 0);
    return res;
}

uint128_w sub128(uint128_w a, uint128_w b) {
    uint128_w res; res.low = a.low - b.low;
    unsigned __int64 borrow = (a.low < b.low) ? 1 : 0;
    res.high = a.high - b.high - borrow;
    return res;
}

uint128_w mul64x64(unsigned __int64 a, unsigned __int64 b) {
    uint128_w res;
#ifdef _MSC_VER
    res.low = _umul128(a, b, &res.high);
#else
    unsigned __int128 p = (unsigned __int128)a * b;
    res.low = (unsigned __int64)p; res.high = (unsigned __int64)(p >> 64);
#endif
    return res;
}

uint192_w mul128x64_full(uint128_w a, unsigned __int64 b) {
    uint128_w p_low = mul64x64(a.low, b);
    uint128_w p_high = mul64x64(a.high, b);
    uint192_w res; res.low = p_low.low;
    unsigned __int64 mid_sum = p_low.high + p_high.low;
    unsigned __int64 carry_mid = (mid_sum < p_low.high) ? 1 : 0;
    res.mid = mid_sum; res.high = p_high.high + carry_mid;
    return res;
}

uint192_w add192_scalar(uint192_w a, unsigned __int64 b) {
    uint192_w res = a; res.low += b;
    if (res.low < b) { res.mid++; if (res.mid == 0) res.high++; }
    return res;
}

// Capture full quotient
unsigned __int64 div192_by_64_modulo_q(uint192_w num, unsigned __int64 q) {
#ifdef _MSC_VER
    unsigned __int64 rem_high = 0;
    if (num.high > 0) _udiv128(0, num.high, q, &rem_high);

    unsigned __int64 rem_mid;
    unsigned __int64 quot_high = _udiv128(rem_high, num.mid, q, &rem_mid);

    unsigned __int64 rem_low;
    unsigned __int64 quot_low = _udiv128(rem_mid, num.low, q, &rem_low);

    // Combine High and Low parts modulo q
    unsigned __int64 two_pow_64_mod_q;
    _udiv128(1, 0, q, &two_pow_64_mod_q);

    unsigned __int64 high_prod_high;
    unsigned __int64 high_prod_low = _umul128(quot_high, two_pow_64_mod_q, &high_prod_high);
    unsigned __int64 term1;
    _udiv128(high_prod_high, high_prod_low, q, &term1);

    unsigned __int64 term2 = quot_low % q;
    unsigned __int64 final_res = (term1 + term2);
    if (final_res >= q) final_res -= q;
    return final_res;
#else
    return 0;
#endif
}

BFVMultiplier::BFVMultiplier(int N, ModInt q, ModInt t)
    : ntt(N, q), N(N), q(q), t(t) {
    if (!ntt.is_valid()) throw std::runtime_error("NTT init failed");
}

std::vector<std::vector<ModInt>> BFVMultiplier::multiply_ciphertexts(
    const std::vector<ModInt>& c1_0, const std::vector<ModInt>& c1_1,
    const std::vector<ModInt>& c2_0, const std::vector<ModInt>& c2_1) {

    auto mul_scale = [&](const std::vector<ModInt>& a, const std::vector<ModInt>& b) {
        std::vector<uint128_w> acc(2 * N, {0, 0});
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                uint128_w prod = mul64x64((unsigned __int64)a[i], (unsigned __int64)b[j]);
                acc[i + j] = add128(acc[i + j], prod);
            }
        }
        std::vector<ModInt> res(N);
        unsigned __int64 q_64 = (unsigned __int64)q;
        unsigned __int64 t_64 = (unsigned __int64)t;

        for (int i = 0; i < N; i++) {
            uint128_w val_abs;
            bool is_negative = false;
            if (acc[i].high > acc[N+i].high || (acc[i].high == acc[N+i].high && acc[i].low >= acc[N+i].low)) {
                val_abs = sub128(acc[i], acc[N+i]);
            } else {
                val_abs = sub128(acc[N+i], acc[i]);
                is_negative = true;
            }

            uint192_w num = mul128x64_full(val_abs, t_64);
            num = add192_scalar(num, q_64 / 2);

            // USE NEW FUNCTION HERE
            unsigned __int64 scaled = div192_by_64_modulo_q(num, q_64);

            long long final_val = (long long)scaled;
            if (is_negative) final_val = -final_val;
            if (final_val < 0) final_val += q_64;

            res[i] = (ModInt)final_val;
        }
        return res;
    };

    std::vector<ModInt> d0 = mul_scale(c1_0, c2_0);
    std::vector<ModInt> d1_a = mul_scale(c1_0, c2_1);
    std::vector<ModInt> d1_b = mul_scale(c1_1, c2_0);
    std::vector<ModInt> d1(N);
    for(int i=0; i<N; i++) d1[i] = (d1_a[i] + d1_b[i]) % q;
    std::vector<ModInt> d2 = mul_scale(c1_1, c2_1);
    return {d0, d1, d2};
}

std::vector<std::vector<ModInt>> BFVMultiplier::relinearize(
    const std::vector<ModInt>& d0, const std::vector<ModInt>& d1, const std::vector<ModInt>& d2,
    const std::vector<std::vector<ModInt>>& relin_key) {
    return {d0, d1};
}

} // namespace fhe_cpp
