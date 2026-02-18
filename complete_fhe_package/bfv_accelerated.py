"""
Enhanced BFV Scheme: C++ Accelerated Multiplication, Python Relinearization
"""
import numpy as np
from custom_fhe.bfv_scheme import BFVScheme as BaseBFVScheme
from custom_fhe.ciphertext import Ciphertext
from custom_fhe.polynomial import PolynomialRing

try:
    import fhe_fast_mult
    CPP_AVAILABLE = True
    print(" C++ multiplication backend detected")
except ImportError:
    CPP_AVAILABLE = False
    print(" C++ backend not available")

class BFVSchemeAccelerated(BaseBFVScheme):
    def __init__(self, N=4096, t=256, q_bits=55, sigma=3.2):
        # 1. Initialize Base Scheme
        super().__init__(N, t, q_bits, sigma)

        self.use_cpp = CPP_AVAILABLE

        if self.use_cpp:
            try:
                # Find an NTT-friendly prime (q = 1 mod 2N)
                # The C++ backend strictly requires this.
                target_q = 1 << q_bits
                self.q = self._find_ntt_prime(target_q, N)

                # 3. Update dependent parameters with new q
                self.poly_ring = PolynomialRing(N, self.q)
                self.delta = self.q // self.t
                self.T = 1 << (self.q.bit_length() // 2) # Update decomposition base

                # 4. Initialize C++ Multiplier
                self.cpp_mult = fhe_fast_mult.BFVMultiplier(N, self.q, self.t)
                print(f" Accelerator active (N={N}, q={self.q})")

            except Exception as e:
                print(f" Accelerator init failed: {e}")
                print("  Falling back to Pure Python (slow but working)")
                self.use_cpp = False

    def _find_ntt_prime(self, start_q, N):
        """Find a prime q satisfying q = 1 mod 2N"""
        m = 2 * N
        # Start search from start_q, ensuring alignment with m
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
        """
        Use C++ for the heavy O(N^2) Multiplication
        """
        if self.use_cpp:
            c1_0, c1_1 = ct1.get_components()
            c2_0, c2_1 = ct2.get_components()

            # Pass to C++ (Returns d0, d1, d2)
            d0, d1, d2 = self.cpp_mult.multiply_ciphertexts(
                np.array(c1_0, dtype=np.int64),
                np.array(c1_1, dtype=np.int64),
                np.array(c2_0, dtype=np.int64),
                np.array(c2_1, dtype=np.int64)
            )

            return Ciphertext(
                [np.array(d0, dtype=np.int64),
                 np.array(d1, dtype=np.int64),
                 np.array(d2, dtype=np.int64)],
                params=ct1.params
            )
        else:
            return super().multiply(ct1, ct2)

    def get_backend_info(self):
        # Always return 'q' to prevent KeyError in example script
        return {
            'backend': 'C++ Multiplication / Python Relin' if self.use_cpp else 'Pure Python',
            'q': self.q
        }
