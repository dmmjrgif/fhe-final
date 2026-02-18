/*
 * BFV Multiplier Header - FINAL FIXED
 * Includes get_delta() to satisfy bindings.cpp
 */

#ifndef FHE_BFV_MULT_H
#define FHE_BFV_MULT_H

#include "ntt.h"
#include <vector>

namespace fhe_cpp {

class BFVMultiplier {
private:
    NTT ntt;
    int N;
    ModInt q;
    ModInt t;
    ModInt delta;

public:
    BFVMultiplier(int N, ModInt q, ModInt t);

    // FIX: Added missing getter required by bindings.cpp
    ModInt get_delta() const { return delta; }

    // Returns {d0, d1, d2}
    std::vector<std::vector<ModInt>> multiply_ciphertexts(
        const std::vector<ModInt>& c1_0,
        const std::vector<ModInt>& c1_1,
        const std::vector<ModInt>& c2_0,
        const std::vector<ModInt>& c2_1);

    // Returns {c0, c1}
    std::vector<std::vector<ModInt>> relinearize(
        const std::vector<ModInt>& d0,
        const std::vector<ModInt>& d1,
        const std::vector<ModInt>& d2,
        const std::vector<std::vector<ModInt>>& relin_key);
};

} // namespace fhe_cpp

#endif // FHE_BFV_MULT_H