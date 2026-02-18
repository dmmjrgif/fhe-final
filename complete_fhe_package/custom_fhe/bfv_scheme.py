"""
BFV (Brakerski-Fan-Vercauteren) Encryption Scheme
FIXED: Correct Scaling (t/q) and Decomposition Logic.
"""

import numpy as np
from .polynomial import PolynomialRing, DiscreteGaussian
from .keys import PublicKey, SecretKey, RelinearizationKey
from .ciphertext import Ciphertext, Plaintext

class BFVScheme:
    def __init__(self, N=4096, t=4096, q_bits=60, sigma=3.2):
        # Increased default t to 4096 to handle larger products
        self.N = N
        self.t = t
        self.q = (1 << q_bits) - 1
        self.sigma = sigma
        self.poly_ring = PolynomialRing(N, self.q)
        self.gaussian = DiscreteGaussian(sigma, N)
        self.delta = self.q // self.t

        # Decomposition Base T (approx sqrt(q))
        # This splits the noise during relinearization
        self.T = 1 << (q_bits // 2)

        self.secret_key = None
        self.public_key = None
        self.relin_key = None
        self.n_slots = N // 2

        print(f"BFV Parameters: N={N}, t={t}, q≈2^{q_bits}")
        print(f"  Decomposition Base T≈2^{q_bits // 2}")

    def key_generation(self):
        s = self.poly_ring.random_ternary()
        self.secret_key = SecretKey(s)
        a = self.poly_ring.random_uniform()
        e = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
        # b = -(as + e)
        a_s = self.poly_ring.mul(a, s)
        a_s_e = self.poly_ring.add(a_s, e)
        b = self.poly_ring.neg(a_s_e)

        self.public_key = PublicKey(b, a)
        return self.secret_key, self.public_key

    def _encrypt_poly_internal(self, poly_msg):
        """Helper to encrypt a secret polynomial (used for RelinKey)"""
        s = self.secret_key.get_polynomial()
        a = self.poly_ring.random_uniform()
        e = self.gaussian.sample_bounded(bound=6 * int(self.sigma))

        # val = -(as + e) + message
        a_s = self.poly_ring.mul(a, s)
        noise = self.poly_ring.add(a_s, e)
        b = self.poly_ring.add(self.poly_ring.neg(noise), poly_msg)
        return (b, a)

    def generate_relin_key(self):
        """Generate Relinearization Key with Decomposition"""
        if self.secret_key is None: raise ValueError("Keys not generated")
        s = self.secret_key.get_polynomial()
        s_squared = self.poly_ring.mul(s, s)

        # Key 0: Encrypt(s^2)
        k0 = self._encrypt_poly_internal(s_squared)

        # Key 1: Encrypt(T * s^2)
        s_squared_T = self.poly_ring.mul_scalar(s_squared, self.T)
        k1 = self._encrypt_poly_internal(s_squared_T)

        self.relin_key = RelinearizationKey([k0, k1])
        return self.relin_key

    def encrypt(self, plaintext):
        if self.public_key is None: raise ValueError("No Public Key")
        m = plaintext.get_poly()
        pk0, pk1 = self.public_key.get_components()

        u = self.poly_ring.random_ternary()
        e1 = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
        e2 = self.gaussian.sample_bounded(bound=6 * int(self.sigma))

        # c0 = pk0*u + e1 + delta*m
        pk0_u = self.poly_ring.mul(pk0, u)
        c0 = self.poly_ring.add(pk0_u, e1)
        c0 = self.poly_ring.add(c0, self.poly_ring.mul_scalar(m, self.delta))

        # c1 = pk1*u + e2
        pk1_u = self.poly_ring.mul(pk1, u)
        c1 = self.poly_ring.add(pk1_u, e2)

        return Ciphertext([c0, c1], params={'N': self.N, 't': self.t, 'q': self.q})

    def decrypt(self, ciphertext):
        if self.secret_key is None: raise ValueError("No Secret Key")

        components = ciphertext.get_components()
        c0, c1 = components[:2]
        s = self.secret_key.get_polynomial()

        # noisy_m = c0 + c1*s
        c1_s = self.poly_ring.mul(c1, s)
        noisy_m = self.poly_ring.add(c0, c1_s)

        # Scale: round(noisy * t / q) using OBJECT math
        noisy_obj = noisy_m.astype(object)
        scaled = (noisy_obj * self.t + (self.q // 2)) // self.q

        m = scaled.astype(np.int64) % self.t
        return Plaintext(m, params={'N': self.N, 't': self.t, 'q': self.q})

    def multiply(self, ct1, ct2):
        """Homomorphic Multiplication with Correct Scaling (t/q)"""
        c1_0, c1_1 = ct1.get_components()
        c2_0, c2_1 = ct2.get_components()

        def mul_scale(p1, p2):
            # 1. Convolution (Object type)
            conv = np.convolve(p1.astype(object), p2.astype(object))
            res = np.zeros(self.N, dtype=object)
            for i in range(len(conv)):
                if i < self.N: res[i] += conv[i]
                else: res[i - self.N] -= conv[i]

            # 2. Scale: (val * t + q/2) // q
            val = (res * self.t + (self.q // 2)) // self.q
            return (val % self.q).astype(np.int64)

        d0 = mul_scale(c1_0, c2_0)
        d1 = self.poly_ring.add(mul_scale(c1_0, c2_1), mul_scale(c1_1, c2_0))
        d2 = mul_scale(c1_1, c2_1)

        return Ciphertext([d0, d1, d2], params=ct1.params)

    def relinearize(self, ciphertext):
        """Relinearization with Base Decomposition"""
        if ciphertext.size != 3: return ciphertext

        d0, d1, d2 = ciphertext.get_components()
        keys = self.relin_key.get_components()

        # Decompose d2 into d2_0 + d2_1 * T
        d2_0 = d2 % self.T
        d2_1 = d2 // self.T

        # c0 = d0 + d2_0*k0_b + d2_1*k1_b
        k0_b, k0_a = keys[0]
        k1_b, k1_a = keys[1]

        term0_0 = self.poly_ring.mul(d2_0, k0_b)
        term0_1 = self.poly_ring.mul(d2_1, k1_b)
        new_c0 = self.poly_ring.add(d0, self.poly_ring.add(term0_0, term0_1))

        # c1 = d1 + d2_0*k0_a + d2_1*k1_a
        term1_0 = self.poly_ring.mul(d2_0, k0_a)
        term1_1 = self.poly_ring.mul(d2_1, k1_a)
        new_c1 = self.poly_ring.add(d1, self.poly_ring.add(term1_0, term1_1))

        return Ciphertext([new_c0, new_c1], params=ciphertext.params)

    def encode(self, values):
        if isinstance(values, int): values = [values]
        poly = np.zeros(self.N, dtype=np.int64)
        values = np.array(values, dtype=np.int64)
        count = min(len(values), self.N)
        poly[:count] = values[:count] % self.t
        return Plaintext(poly, params={'N':self.N})

    def decode(self, pt):
        return int(self.poly_ring.mod_center(pt.get_poly())[0] % self.t)