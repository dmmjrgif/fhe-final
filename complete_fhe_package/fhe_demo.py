import sys
import os
import numpy as np


sys.path.append(os.getcwd())

print(f"--- FHE ACCELERATION TEST ---")
print(f"Working Directory: {os.getcwd()}")

try:
    # 2. Import the C++ module you just built
    import fhe_fast_mult

    print(f"SUCCESS: C++ Backend Loaded!")
    print(f"   Module location: {fhe_fast_mult.__file__}")

    # 3. Setup BFV Parameters (N=4096 is standard)
    N = 4096
    # A specific prime that supports NTT for N=4096
    # q must be 1 mod 2N. (1152921504606846977 = 0x100000000060001)
    q = 1152921504606830593
    t = 65537  # Plaintext modulus

    print(f"\nInitializing BFV Scheme (N={N})...")
    multiplier = fhe_fast_mult.BFVMultiplier(N, q, t)

    # 4. Create dummy test data (representing polynomials)
    # In FHE, these would be encrypted ciphertexts
    print("\nRunning C++ Accelerated Multiplication...")
    c1_0 = np.full(N, 10, dtype=np.int64)  # Polynomial of all 10s
    c1_1 = np.full(N, 5, dtype=np.int64)  # Polynomial of all 5s
    c2_0 = np.full(N, 2, dtype=np.int64)  # Polynomial of all 2s
    c2_1 = np.full(N, 3, dtype=np.int64)  # Polynomial of all 3s

    # 5. Execute Multiplication
    # This calls the C++ code you just compiled
    d0, d1, d2 = multiplier.multiply_ciphertexts(c1_0, c1_1, c2_0, c2_1)

    print(" Multiplication finished!")
    print(f"   Result d0 first element: {d0[0]}")
    print("   (If you see numbers above, the math logic is running!)")

except ImportError as e:
    print(f"\n IMPORT ERROR: {e}")
    print("Troubleshooting: Make sure 'fhe_fast_mult.cp313-win_amd64.pyd' is in the same folder.")

except Exception as e:
    print(f"\n RUNTIME ERROR: {e}")
