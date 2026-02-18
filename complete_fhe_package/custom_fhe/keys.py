"""
Key structures for BFV encryption scheme
"""

import numpy as np


class PublicKey:
    """Public key for encryption"""
    
    def __init__(self, pk0, pk1):
        """
        Args:
            pk0: First component (polynomial)
            pk1: Second component (polynomial)
        """
        self.pk0 = pk0
        self.pk1 = pk1
    
    def get_components(self):
        return self.pk0, self.pk1


class SecretKey:
    """Secret key for decryption"""
    
    def __init__(self, s):
        """
        Args:
            s: Secret polynomial
        """
        self.s = s
    
    def get_polynomial(self):
        return self.s


class RelinearizationKey:
    """
    Relinearization key for reducing ciphertext size after multiplication
    """
    
    def __init__(self, evk_components):
        """
        Args:
            evk_components: List of evaluation key components
        """
        self.evk = evk_components
    
    def get_components(self):
        return self.evk


class RotationKey:
    """
    Rotation keys for rotating slots in SIMD batching
    """
    
    def __init__(self, rotation_keys_dict):
        """
        Args:
            rotation_keys_dict: Dictionary mapping rotation amounts to keys
        """
        self.keys = rotation_keys_dict
    
    def get_key(self, rotation):
        """Get key for specific rotation amount"""
        return self.keys.get(rotation, None)
    
    def has_rotation(self, rotation):
        """Check if rotation key exists"""
        return rotation in self.keys
