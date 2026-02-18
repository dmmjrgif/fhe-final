"""
Enhanced BFV Scheme with C++ Accelerated Multiplication
Integrates NTT-based multiplication from C++ backend
"""

import numpy as np
from custom_fhe.bfv_scheme import BFVScheme as BaseBFVScheme
from custom_fhe.ciphertext import Ciphertext

try:
    import fhe_fast_mult
    CPP_AVAILABLE = True
    print("✓ C++ multiplication backend loaded successfully")
except ImportError:
    CPP_AVAILABLE = False
    print("⚠ C++ backend not available, using Python fallback")


class BFVSchemeAccelerated(BaseBFVScheme):
    """
    BFV scheme with C++ accelerated multiplication
    Falls back to Python implementation if C++ not available
    """
    
    def __init__(self, N=8192, t=65537, q_bits=60, sigma=3.2, use_cpp=True):
        """
        Initialize with option to use C++ acceleration
        
        Args:
            use_cpp: Use C++ backend if available (default: True)
        """
        super().__init__(N, t, q_bits, sigma)
        
        self.use_cpp = use_cpp and CPP_AVAILABLE
        
        if self.use_cpp:
            # Find NTT-friendly prime
            self.q_ntt = fhe_fast_mult.find_ntt_prime(N)
            
            # Initialize C++ multiplier
            try:
                self.cpp_mult = fhe_fast_mult.BFVMultiplier(N, self.q_ntt, t)
                self.cpp_ntt = fhe_fast_mult.NTT(N, self.q_ntt)
                
                # Update q to NTT-friendly value
                self.q = self.q_ntt
                self.poly_ring.q = self.q_ntt
                self.delta = self.q // self.t
                
                print(f"✓ C++ accelerated multiplication enabled")
                print(f"  N={N}, q={self.q_ntt}, t={t}")
                print(f"  Using NTT for O(N log N) multiplication")
            except Exception as e:
                print(f"⚠ C++ initialization failed: {e}")
                print(f"  Falling back to Python implementation")
                self.use_cpp = False
    
    def multiply(self, ct1, ct2):
        """
        Homomorphic multiplication with C++ acceleration
        
        Args:
            ct1, ct2: Ciphertext objects (must be size-2)
        
        Returns:
            Ciphertext object (size-3, needs relinearization)
        """
        if not ct1.is_fresh() or not ct2.is_fresh():
            raise ValueError("Can only multiply fresh ciphertexts (size 2)")
        
        # Use C++ backend if available
        if self.use_cpp:
            return self._multiply_cpp(ct1, ct2)
        else:
            # Fall back to Python implementation
            return super().multiply(ct1, ct2)
    
    def _multiply_cpp(self, ct1, ct2):
        """C++ accelerated multiplication"""
        c1_0, c1_1 = ct1.get_components()
        c2_0, c2_1 = ct2.get_components()
        
        # Convert to numpy arrays for C++ interface
        c1_0_np = np.array(c1_0, dtype=np.int64)
        c1_1_np = np.array(c1_1, dtype=np.int64)
        c2_0_np = np.array(c2_0, dtype=np.int64)
        c2_1_np = np.array(c2_1, dtype=np.int64)
        
        # Call C++ multiplication
        d0_np, d1_np, d2_np = self.cpp_mult.multiply_ciphertexts(
            c1_0_np, c1_1_np, c2_0_np, c2_1_np
        )
        
        # Convert back to Python lists
        d0 = d0_np.tolist() if hasattr(d0_np, 'tolist') else list(d0_np)
        d1 = d1_np.tolist() if hasattr(d1_np, 'tolist') else list(d1_np)
        d2 = d2_np.tolist() if hasattr(d2_np, 'tolist') else list(d2_np)
        
        return Ciphertext([d0, d1, d2], params=ct1.params)
    
    def poly_multiply(self, a, b):
        """
        Fast polynomial multiplication using C++ NTT
        Can be used by other operations that need polynomial multiplication
        """
        if self.use_cpp:
            a_np = np.array(a, dtype=np.int64)
            b_np = np.array(b, dtype=np.int64)
            result_np = self.cpp_ntt.multiply(a_np, b_np)
            return result_np.tolist() if hasattr(result_np, 'tolist') else list(result_np)
        else:
            return self.poly_ring.mul(a, b)
    
    def get_backend_info(self):
        """Get information about which backend is being used"""
        if self.use_cpp:
            return {
                'backend': 'C++ (NTT accelerated)',
                'multiplication': 'O(N log N) using Number Theoretic Transform',
                'q': self.q,
                'ntt_friendly': True
            }
        else:
            return {
                'backend': 'Python (NumPy)',
                'multiplication': 'O(N²) using convolution',
                'q': self.q,
                'ntt_friendly': False
            }


# Convenience function to create accelerated scheme
def create_fast_bfv(N=8192, t=65537, q_bits=60, sigma=3.2):
    """
    Create BFV scheme with C++ acceleration if available
    
    Returns:
        BFVSchemeAccelerated instance
    """
    return BFVSchemeAccelerated(N, t, q_bits, sigma, use_cpp=True)


# For backwards compatibility
BFVSchemeFast = BFVSchemeAccelerated
