
import numpy as np

# ---------------------------------------------------------
# 1.POLYNOMIAL ARITHMETIC 
# ---------------------------------------------------------
class DebugPolynomialRing:
    def __init__(self, N, q):
        self.N = N
        self.q = q

    def add(self, a, b):
        return (a + b) % self.q

    def mul(self, a, b):
        # Use Python 'object' to handle arbitrary precision integers automatically
        a_obj = np.array(a, dtype=object)
        b_obj = np.array(b, dtype=object)
        conv = np.convolve(a_obj, b_obj)

        result = np.zeros(self.N, dtype=object)
        for i in range(len(conv)):
            if i < self.N: result[i] += conv[i]
            else: result[i - self.N] -= conv[i]

        return (result % self.q).astype(np.int64)

    def mul_scalar(self, a, scalar):
        a_obj = np.array(a, dtype=object)
        return ((a_obj * scalar) % self.q).astype(np.int64)

    def random_uniform(self):
        return np.random.randint(0, self.q, size=self.N, dtype=np.int64)

    def random_ternary(self):
        return np.random.choice([-1, 0, 1], size=self.N).astype(np.int64)

    def sample_error(self):
        return np.random.randint(-3, 4, size=self.N, dtype=np.int64)

# ---------------------------------------------------------
# 2. BFV SCHEME WITH RELINEARIZATION
# ---------------------------------------------------------
class DebugBFV:
    def __init__(self, N=4096, t=256, q_bits=55):
        self.N = N
        self.t = t
        self.q = (1 << q_bits) - 1
        self.poly = DebugPolynomialRing(N, self.q)
        self.delta = self.q // self.t

        # Decomposition Base T (approx sqrt(q))
        # This splits one big multiply into two small ones to reduce noise
        self.T = 1 << (q_bits // 2)

    def keygen(self):
        s = self.poly.random_ternary()
        self.sk = s

        # Public Key (b, a)
        a = self.poly.random_uniform()
        e = self.poly.sample_error()
        # b = -(as + e)
        as_prod = self.poly.mul(a, s)
        b = (self.q - self.poly.add(as_prod, e)) % self.q
        self.pk = (b, a)

        # Relinearization Key (Two parts for decomposition)
        # Part 0: Encrypts s^2
        # Part 1: Encrypts T * s^2
        s2 = self.poly.mul(s, s)
        self.rlk = [
            self._encrypt_secret(s2),              # k0
            self._encrypt_secret(self.poly.mul_scalar(s2, self.T)) # k1
        ]

    def _encrypt_secret(self, message_poly):
        # Helper to encrypt a polynomial under the secret key (for RelinKey)
        a = self.poly.random_uniform()
        e = self.poly.sample_error()
        # val = -(as + e) + message
        as_prod = self.poly.mul(a, self.sk)
        val = self.poly.add(as_prod, e)
        b = (self.poly.add((self.q - val), message_poly)) % self.q
        return (b, a)

    def encrypt(self, val):
        m = np.zeros(self.N, dtype=np.int64)
        m[0] = val % self.t

        pk0, pk1 = self.pk
        u = self.poly.random_ternary()
        e1, e2 = self.poly.sample_error(), self.poly.sample_error()

        # c0 = pk0*u + e1 + delta*m
        c0 = self.poly.add(self.poly.mul(pk0, u), e1)
        c0 = self.poly.add(c0, self.poly.mul_scalar(m, self.delta))

        # c1 = pk1*u + e2
        c1 = self.poly.add(self.poly.mul(pk1, u), e2)
        return [c0, c1]

    def decrypt(self, ct):
        c0, c1 = ct[0], ct[1]
        # simple c0 + c1*s
        noisy = self.poly.add(c0, self.poly.mul(c1, self.sk))

        # Correct Scaling
        noisy_obj = noisy.astype(object)
        numerator = noisy_obj * self.t + (self.q // 2)
        scaled = numerator // self.q
        return (scaled.astype(np.int64) % self.t)[0]

    def multiply(self, ct1, ct2):
        # 1. Tensor Product
        c1_0, c1_1 = ct1
        c2_0, c2_1 = ct2

        def mul_scale(p1, p2):
            conv = np.convolve(p1.astype(object), p2.astype(object))
            res = np.zeros(self.N, dtype=object)
            for i in range(len(conv)):
                if i < self.N: res[i] += conv[i]
                else: res[i - self.N] -= conv[i]
            val = (res * self.t + (self.q // 2)) // self.q
            return (val % self.q).astype(np.int64)

        d0 = mul_scale(c1_0, c2_0)
        d1 = self.poly.add(mul_scale(c1_0, c2_1), mul_scale(c1_1, c2_0))
        d2 = mul_scale(c1_1, c2_1)

        return [d0, d1, d2] # Size 3 Ciphertext

    def relinearize(self, ct_size3):
        # Input: Size 3 [d0, d1, d2] -> Output: Size 2 [c0, c1]
        d0, d1, d2 = ct_size3

        # DECOMPOSITION
        # d2 = d2_0 + d2_1 * T
        d2_0 = d2 % self.T
        d2_1 = d2 // self.T

        # Apply Keys:
        # c0 = d0 + d2_0 * rlk[0][0] + d2_1 * rlk[1][0]
        # c1 = d1 + d2_0 * rlk[0][1] + d2_1 * rlk[1][1]

        term_0_0 = self.poly.mul(d2_0, self.rlk[0][0])
        term_1_0 = self.poly.mul(d2_1, self.rlk[1][0])

        term_0_1 = self.poly.mul(d2_0, self.rlk[0][1])
        term_1_1 = self.poly.mul(d2_1, self.rlk[1][1])

        c0 = self.poly.add(d0, self.poly.add(term_0_0, term_1_0))
        c1 = self.poly.add(d1, self.poly.add(term_0_1, term_1_1))

        return [c0, c1]

# ---------------------------------------------------------
# 3. RUN
# ---------------------------------------------------------
def main():
    print("="*60)
    print("DEBUG FHE FIXED RUN")
    print("="*60)
    fhe = DebugBFV()
    fhe.keygen()

    val1, val2 = 12, 8
    print(f"Encrypting {val1} and {val2}...")
    ct1, ct2 = fhe.encrypt(val1), fhe.encrypt(val2)

    print("Multiplying...")
    ct3 = fhe.multiply(ct1, ct2)

    print("Relinearizing (with Decomposition)...")
    ct2 = fhe.relinearize(ct3)

    print("Decrypting...")
    res = fhe.decrypt(ct2)

    print(f"Result: {res}")
    if res == 96: print(" SUCCESS!")
    else: print(f" FAILED. Got {res}.")

if __name__ == "__main__":
    main()
