/*
 * NTT (Number Theoretic Transform) Implementation
 * Supports Negacyclic Convolution for BFV (X^N + 1)
 */

#ifndef FHE_NTT_H
#define FHE_NTT_H

#include <vector>
#include <cstdint>
#include <stdexcept>

namespace fhe_cpp {

typedef int64_t ModInt;

class NTT {
private:
    int N;
    ModInt q;
    ModInt psi;                     // 2N-th primitive root
    ModInt psi_inv;                 // Inverse of psi
    ModInt omega;                   // N-th root (psi^2)
    ModInt omega_inv;               // Inverse of omega
    ModInt N_inv;

    // Precomputed tables
    std::vector<ModInt> omega_powers;
    std::vector<ModInt> omega_inv_powers;

    // Tables for Negacyclic wrapper (psi^i)
    std::vector<ModInt> psi_powers;
    std::vector<ModInt> psi_inv_powers;

    // Helpers
    ModInt mod_add(ModInt a, ModInt b) const;
    ModInt mod_sub(ModInt a, ModInt b) const;
    ModInt mod_mul(ModInt a, ModInt b) const;
    ModInt mod_exp(ModInt base, ModInt exp) const;
    ModInt mod_inv(ModInt a) const;
    ModInt find_primitive_root();

    int bit_reverse(int x, int log_n) const;
    void bit_reverse_copy(std::vector<ModInt>& a) const;

public:
    NTT(int N, ModInt q);
    ~NTT() = default;

    // Core transforms (Cyclic)
    void ntt_core(std::vector<ModInt>& a, const std::vector<ModInt>& roots) const;

    // Wrapper transforms (Negacyclic X^N+1)
    void forward(std::vector<ModInt>& a) const;
    void inverse(std::vector<ModInt>& a) const;

    // High-level operations
    std::vector<ModInt> multiply(const std::vector<ModInt>& a,
                                  const std::vector<ModInt>& b) const;

    std::vector<ModInt> add(const std::vector<ModInt>& a,
                            const std::vector<ModInt>& b) const;

    std::vector<ModInt> subtract(const std::vector<ModInt>& a,
                                  const std::vector<ModInt>& b) const;

    std::vector<ModInt> scalar_mul(const std::vector<ModInt>& a,
                                    ModInt scalar) const;

    bool is_valid() const;
    int get_N() const { return N; }
    ModInt get_q() const { return q; }
};

} // namespace fhe_cpp

#endif // FHE_NTT_H