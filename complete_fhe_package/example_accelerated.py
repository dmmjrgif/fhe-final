"""
LIBRARY FILE: example_accelerated.py
Contains the C++ Wrapper Class. DO NOT OVERWRITE.
"""
import sys
import os
import numpy as np

# Ensure we can import the custom package
sys.path.append(os.getcwd())

try:
    from custom_fhe.bfv_scheme import BFVScheme
    from custom_fhe.ciphertext import Ciphertext
    import fhe_fast_mult  # The C++ module
    CPP_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Library not found. {e}")
    CPP_AVAILABLE = False
    exit(1)

class BFVSchemeAccelerated(BFVScheme):
    def __init__(self, N=4096, t=256, q_bits=62, sigma=3.2):
        super().__init__(N, t, q_bits, sigma)
        self.use_cpp = CPP_AVAILABLE

        if self.use_cpp:
            try:
                # Find NTT-friendly prime
                target_q = 1 << q_bits
                self.q = self._find_ntt_prime(target_q, N)

                # Update dependent parameters
                from custom_fhe.polynomial import PolynomialRing
                self.poly_ring = PolynomialRing(N, self.q)
                self.delta = self.q // self.t
                self.T = 1 << (self.q.bit_length() // 2)

                # Initialize C++
                self.cpp_mult = fhe_fast_mult.BFVMultiplier(N, self.q, self.t)
                print(f" Accelerator active (N={N}, q={self.q})")
            except Exception as e:
                print(f" Accelerator init failed: {e}")
                self.use_cpp = False

    def _find_ntt_prime(self, start_q, N):
        m = 2 * N
        q = (start_q // m) * m + 1
        def is_prime(n):
            if n % 2 == 0: return False
            for i in range(3, int(n**0.5) + 1, 2):
                if n % i == 0: return False
            return True
        while not is_prime(q):
            q += m
        return q

    def multiply(self, ct1, ct2):
        if self.use_cpp:
            c1_0, c1_1 = ct1.get_components()
            c2_0, c2_1 = ct2.get_components()
            d0, d1, d2 = self.cpp_mult.multiply_ciphertexts(
                np.array(c1_0, dtype=np.int64),
                np.array(c1_1, dtype=np.int64),
                np.array(c2_0, dtype=np.int64),
                np.array(c2_1, dtype=np.int64)
            )
            return Ciphertext([np.array(d0), np.array(d1), np.array(d2)], params=ct1.params)
        else:
            return super().multiply(ct1, ct2)

    def get_backend_info(self):
        return {
            'backend': 'C++ Multiplication / Python Relin' if self.use_cpp else 'Pure Python',
            'q': self.q
        }

# Helper class for the examples
class FastFHE_Custom:
    def __init__(self):
        self.t = 33554432  # 2^25
        self.N = 4096
        self.HE = BFVSchemeAccelerated(N=self.N, t=self.t, q_bits=62)
        self.HE.key_generation()
        self.HE.generate_relin_key()

    def encrypt_int(self, value):
        pt = self.HE.encode([value])
        return self.HE.encrypt(pt)

    def encrypt_batch(self, values):
        pt = self.HE.encode(values)
        return self.HE.encrypt(pt)

    def decrypt_batch(self, ctxt, num_values=None):
        pt = self.HE.decrypt(ctxt)
        poly = pt.get_poly()
        half_t = self.t // 2
        centered = np.where(poly > half_t, poly - self.t, poly)
        if num_values: return centered[:num_values].tolist()
        return centered.tolist()

    def homomorphic_sub(self, ct1, ct2):
        c1_0, c1_1 = ct1.get_components()
        c2_0, c2_1 = ct2.get_components()
        d0 = self.HE.poly_ring.sub(c1_0, c2_0)
        d1 = self.HE.poly_ring.sub(c1_1, c2_1)
        return Ciphertext([d0, d1], params=ct1.params)
