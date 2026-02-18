"""
Test script for Custom FHE Library

"""

import sys
import numpy as np

sys.path.insert(0, '/home/claude')
from custom_fhe import BFVScheme

def test_basic_encryption():
    """Test basic encryption and decryption"""
    print("Testing basic encryption/decryption...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    
    # Test single value
    value = 42
    pt = fhe.encode(value)
    ct = fhe.encrypt(pt)
    decrypted = fhe.decrypt(ct)
    result = fhe.decode(decrypted)
    
    assert result == value, f"Expected {value}, got {result}"
    print(f" Single value: {value} -> encrypted -> {result}")


def test_batching():
    """Test SIMD batching"""
    print("\nTesting SIMD batching...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    
    values = [10, 20, 30, 40, 50]
    pt = fhe.encode(values)
    ct = fhe.encrypt(pt)
    decrypted = fhe.decrypt(ct)
    results = fhe.decode(decrypted, num_values=len(values))
    
    for i, (orig, res) in enumerate(zip(values, results)):
        assert orig == res, f"Position {i}: Expected {orig}, got {res}"
    
    print(f" Batch: {values} -> encrypted -> {list(results)}")


def test_addition():
    """Test homomorphic addition"""
    print("\nTesting homomorphic addition...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    
    a, b = 100, 200
    ct1 = fhe.encrypt(fhe.encode(a))
    ct2 = fhe.encrypt(fhe.encode(b))
    
    ct_sum = fhe.add(ct1, ct2)
    result = fhe.decode(fhe.decrypt(ct_sum))
    expected = a + b
    
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"Addition: {a} + {b} = {result}")


def test_subtraction():
    """Test homomorphic subtraction"""
    print("\nTesting homomorphic subtraction...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    
    a, b = 500, 200
    ct1 = fhe.encrypt(fhe.encode(a))
    ct2 = fhe.encrypt(fhe.encode(b))
    
    ct_diff = fhe.sub(ct1, ct2)
    result = fhe.decode(fhe.decrypt(ct_diff))
    expected = a - b
    
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"Subtraction: {a} - {b} = {result}")


def test_multiplication():
    """Test homomorphic multiplication"""
    print("\nTesting homomorphic multiplication...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    fhe.generate_relin_key()
    
    a, b = 12, 8
    ct1 = fhe.encrypt(fhe.encode(a))
    ct2 = fhe.encrypt(fhe.encode(b))
    
    ct_product = fhe.multiply(ct1, ct2)
    ct_product = fhe.relinearize(ct_product)
    result = fhe.decode(fhe.decrypt(ct_product))
    expected = a * b
    
    # Allow small error due to noise
    error = abs(result - expected)
    assert error <= 1, f"Expected {expected}, got {result} (error: {error})"
    print(f" Multiplication: {a} × {b} = {result} (expected: {expected})")


def test_multiple_operations():
    """Test chain of operations"""
    print("\nTesting multiple operations...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    
    # (10 + 20) - 5 = 25
    ct1 = fhe.encrypt(fhe.encode(10))
    ct2 = fhe.encrypt(fhe.encode(20))
    ct3 = fhe.encrypt(fhe.encode(5))
    
    ct_sum = fhe.add(ct1, ct2)
    ct_final = fhe.sub(ct_sum, ct3)
    
    result = fhe.decode(fhe.decrypt(ct_final))
    expected = 25
    
    assert result == expected, f"Expected {expected}, got {result}"
    print(f" Chain: (10 + 20) - 5 = {result}")


def test_exact_match():
    """Test exact match scenario (your use case)"""
    print("\nTesting exact match scenario...")
    
    fhe = BFVScheme(N=4096, t=65537, q_bits=50)
    fhe.key_generation()
    
    # Encrypt database values
    db_values = [20260205, 20260215, 20260225, 20260228]
    encrypted_db = [fhe.encrypt(fhe.encode(v)) for v in db_values]
    
    # Search for 20260225
    target = 20260225
    encrypted_target = fhe.encrypt(fhe.encode(target))
    
    # Compute differences
    matches = []
    for i, enc_val in enumerate(encrypted_db):
        diff_ct = fhe.sub(enc_val, encrypted_target)
        diff = fhe.decode(fhe.decrypt(diff_ct))
        
        if diff == 0:
            matches.append(i)
    
    expected_match = 2  # Index of 20260225
    assert expected_match in matches, f"Expected match at index {expected_match}"
    print(f" Exact match: Found target at index {matches[0]}")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("CUSTOM FHE LIBRARY - TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_basic_encryption,
        test_batching,
        test_addition,
        test_subtraction,
        test_multiplication,
        test_multiple_operations,
        test_exact_match
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f" {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n  Custom FHE library is working")
    else:
        print(f"\n  {failed} test(s) failed. Review errors.")


if __name__ == "__main__":
    run_all_tests()
