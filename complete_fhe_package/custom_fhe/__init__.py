"""
Custom FHE Library - Pure Python Implementation
BFV (Brakerski-Fan-Vercauteren) Scheme
Optimized with NumPy for performance

Now with C++ Accelerated Multiplication!
"""

from .bfv_scheme import BFVScheme
from .ciphertext import Ciphertext, Plaintext
from .keys import PublicKey, SecretKey, RelinearizationKey, RotationKey

# Try to import accelerated version
try:
    from .bfv_accelerated import BFVSchemeAccelerated, create_fast_bfv
    __all_exports = [
        'BFVScheme',
        'BFVSchemeAccelerated',  # New!
        'create_fast_bfv',       # New!
        'Ciphertext',
        'Plaintext',
        'PublicKey',
        'SecretKey',
        'RelinearizationKey',
        'RotationKey'
    ]
except ImportError:
    # Accelerated version not available (C++ not built)
    __all_exports = [
        'BFVScheme',
        'Ciphertext',
        'Plaintext',
        'PublicKey',
        'SecretKey',
        'RelinearizationKey',
        'RotationKey'
    ]

__version__ = "2.0.0"  # Updated with C++ acceleration
__all__ = __all_exports
