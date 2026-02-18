"""
Polynomial Ring Operations
Implements efficient polynomial arithmetic in R_q = Z_q[X]/(X^N + 1)
"""

import numpy as np
from numpy.polynomial import polynomial as P

class PolynomialRing:
    def __init__(self, N, q):
        self.N = N
        self.q = q
        if N & (N - 1) != 0:
            raise ValueError("N must be a power of 2")

    def add(self, a, b):
        return (a + b) % self.q

    def sub(self, a, b):
        return (a - b) % self.q

    def mul_scalar(self, a, scalar):
        # Use object type to prevent overflow before modulo
        result = (a.astype(object) * scalar) % self.q
        return result.astype(np.int64)

    def mul(self, a, b):
        """
        Multiply two polynomials in R_q using arbitrary precision integers.
        """
        # CRITICAL FIX: Cast to 'object' to prevent 64-bit overflow
        # when multiplying large coefficients.
        a_big = a.astype(object)
        b_big = b.astype(object)

        # Standard convolution
        conv = np.convolve(a_big, b_big)

        # Negacyclic Reduction (X^N = -1)
        result = np.zeros(self.N, dtype=object)
        for i in range(len(conv)):
            if i < self.N:
                result[i] += conv[i]
            else:
                result[i - self.N] -= conv[i]

        # Apply modulo q and cast back to int64
        return (result % self.q).astype(np.int64)

    def neg(self, a):
        return (-a) % self.q

    def mod_center(self, a):
        result = a.copy()
        half_q = self.q // 2
        mask = result > half_q
        result[mask] -= self.q
        return result

    def random_uniform(self, size=None):
        if size is None: size = self.N
        return np.random.randint(0, self.q, size=size, dtype=np.int64)

    def random_ternary(self):
        return np.random.choice([-1, 0, 1], size=self.N).astype(np.int64)

    def random_bounded(self, bound):
        return np.random.randint(-bound, bound + 1, size=self.N, dtype=np.int64)

class DiscreteGaussian:
    def __init__(self, sigma, N):
        self.sigma = sigma
        self.N = N

    def sample(self):
        samples = np.random.normal(0, self.sigma, self.N)
        return np.round(samples).astype(np.int64)

    def sample_bounded(self, bound):
        samples = self.sample()
        return np.clip(samples, -bound, bound)