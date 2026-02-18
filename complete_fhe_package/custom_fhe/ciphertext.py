"""
Plaintext and Ciphertext data structures
"""

import numpy as np


class Plaintext:
    """Plaintext polynomial representation"""
    
    def __init__(self, poly, params=None):
        """
        Args:
            poly: Polynomial coefficients as numpy array
            params: Optional parameters (N, t, q)
        """
        self.poly = poly
        self.params = params
    
    def get_poly(self):
        return self.poly
    
    def __repr__(self):
        return f"Plaintext(degree={len(self.poly)}, coeffs={self.poly[:4]}...)"


class Ciphertext:
    """Ciphertext representation (c0, c1) or (c0, c1, c2) for fresh/multiplied"""
    
    def __init__(self, components, params=None):
        """
        Args:
            components: List of polynomial components [c0, c1] or [c0, c1, c2]
            params: Optional parameters (N, t, q)
        """
        if not isinstance(components, list):
            raise ValueError("Components must be a list of polynomials")
        
        self.components = components
        self.params = params
        self.size = len(components)
    
    def get_components(self):
        return self.components
    
    def is_fresh(self):
        """Check if ciphertext is fresh (size 2) vs multiplied (size 3+)"""
        return self.size == 2
    
    def __repr__(self):
        return f"Ciphertext(size={self.size}, N={len(self.components[0])})"
    
    def copy(self):
        """Create a deep copy of the ciphertext"""
        new_components = [c.copy() for c in self.components]
        return Ciphertext(new_components, self.params)
    
    def __add__(self, other):
        """Addition placeholder - actual implementation in BFVScheme"""
        raise NotImplementedError("Use BFVScheme.add() for addition")
    
    def __sub__(self, other):
        """Subtraction placeholder - actual implementation in BFVScheme"""
        raise NotImplementedError("Use BFVScheme.sub() for subtraction")
    
    def __mul__(self, other):
        """Multiplication placeholder - actual implementation in BFVScheme"""
        raise NotImplementedError("Use BFVScheme.mul() for multiplication")
