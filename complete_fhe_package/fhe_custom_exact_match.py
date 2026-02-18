"""
CUSTOM FHE SOLUTION - NO THIRD PARTY PACKAGES
Uses our own BFV implementation with NumPy optimization
"""

import sys
import time
import numpy as np

# Import our custom FHE library
sys.path.insert(0, '/home/claude')
from custom_fhe import BFVScheme

def print_progress(iteration, total, start_time, prefix='', suffix='', length=30):
    """progress bar helper"""
    if total == 0: return
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    elapsed = time.time() - start_time
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% [{elapsed:.2f}s] {suffix}')
    sys.stdout.flush()
    if iteration == total: print()


def string_to_ints(s, max_len):
    """Convert string to list of integers (one per character)"""
    bytes_data = s.encode('utf-8')
    # Pad or truncate to max_len
    if len(bytes_data) > max_len:
        bytes_data = bytes_data[:max_len]
    else:
        bytes_data = bytes_data + b'\x00' * (max_len - len(bytes_data))
    return [b for b in bytes_data]


def ints_to_string(ints):
    """Convert list of integers back to string"""
    chars = []
    for val in ints:
        if val == 0:
            break
        try:
            chars.append(chr(int(val)))
        except:
            chars.append('?')
    return ''.join(chars)


class CustomFHEClient:
    def __init__(self, fhe):
        self.fhe = fhe

    def encrypt_dataset(self, data):
        """
        Encrypt dataset using our custom FHE
        """
        print("\nEncrypting Dataset")
        start_time = time.time()
        
        encrypted_rows = []
        
        for i, row in enumerate(data):
            date_val = row['d']
            
            # 1. Encrypt Date
            pt_date = self.fhe.encode(date_val)
            enc_date = self.fhe.encrypt(pt_date)
            
            # 2. Encrypt Email (as batch)
            email_vals = string_to_ints(row['e'], 12)
            pt_email = self.fhe.encode(email_vals)
            enc_email = self.fhe.encrypt(pt_email)
            
            encrypted_rows.append({
                'date': enc_date,
                'email': enc_email
            })
            
            print_progress(i + 1, len(data), start_time, 
                          prefix='Encrypting', suffix=f'Row {i+1}')
        
        return encrypted_rows

    def encrypt_query(self, target_date):
        """Encrypt single target date for Exact Match"""
        pt = self.fhe.encode(target_date)
        return self.fhe.encrypt(pt)

    def decrypt_results(self, results):
        """Decrypt and check for exact matches (zeros)"""
        print("\nDecrypting Results")
        start_time = time.time()
        
        plain_results = []
        for i, (enc_email, enc_diff) in enumerate(results):
            # Decrypt the difference
            pt_diff = self.fhe.decrypt(enc_diff)
            diff_val = self.fhe.decode(pt_diff, num_values=1)
            
            # LOGIC: If difference is 0, the dates were identical
            if diff_val == 0:
                # Decrypt email
                pt_email = self.fhe.decrypt(enc_email)
                email_ints = self.fhe.decode(pt_email, num_values=12)
                email_str = ints_to_string(email_ints)
                plain_results.append(f"MATCH: {email_str}")
            else:
                plain_results.append("---")
            
            print_progress(i + 1, len(results), start_time,
                          prefix='Decrypting', suffix=f'Row {i+1}')
        
        return plain_results


class CustomFHEServer:
    def __init__(self, fhe):
        self.fhe = fhe

    def process_query(self, enc_data, enc_target_date):
        """
        Targeted Search: Compute (Data - Target)
        If result is 0, it's a match
        """
        print("\nProcessing Query (Homomorphic Subtraction)")
        start_time = time.time()
        
        results = []
        
        for i, row in enumerate(enc_data):
            enc_date = row['date']
            enc_email = row['email']
            
            # Homomorphic Subtraction
            # If dates are equal, diff will encrypt 0
            diff = self.fhe.sub(enc_date, enc_target_date)
            
            results.append((enc_email, diff))
            
            print_progress(i + 1, len(enc_data), start_time,
                          prefix='Processing', suffix=f'Row {i+1}')
        
        return results


def main():
    print("=" * 60)
    print("CUSTOM FHE IMPLEMENTATION (Pure Python + NumPy)")
    print("BFV Scheme - No Third Party FHE Libraries")
    print("=" * 60)
    
    # Initialize our custom FHE with optimized parameters
    print("\nInitializing Custom FHE...")
    fhe = BFVScheme(
        N=8192,          # Polynomial degree 
        t=65537,         # Plaintext modulus 
        q_bits=60,       # Ciphertext modulus size
        sigma=3.2        # Noise parameter
    )
    
    print("\nGenerating keys...")
    key_start = time.time()
    fhe.key_generation()
    fhe.generate_relin_key()
    print(f"Key generation completed in {time.time() - key_start:.2f}s")
    
    client = CustomFHEClient(fhe)
    server = CustomFHEServer(fhe)
    
    # Data
    data = [
        {"d": 20260205, "e": "spam@x.com"},
        {"d": 20260215, "e": "ad@spam.com"},
        {"d": 20260220, "e": "ceo@corp.net"},
        {"d": 20260222, "e": "hr@work.org"},
        {"d": 20260225, "e": "me@home.net"},  # <-- We will search for this one
        {"d": 20260228, "e": "vip@mail.com"},
        {"d": 20260301, "e": "old@mail.org"},
        {"d": 20260310, "e": "bad@news.net"}
    ]
    
    print(f"\nDataset: {len(data)} rows")
    
    # Client encrypts data
    total_start = time.time()
    enc_data = client.encrypt_dataset(data)
    
    # Client creates Exact Match query for Feb 25
    target_date = 20260225
    print(f"\nSearching for date: {target_date}")
    enc_target = client.encrypt_query(target_date)
    
    # Server processes (Blind Subtraction)
    results = server.process_query(enc_data, enc_target)
    
    # Client decrypts (Checks for 0s)
    final_results = client.decrypt_results(results)
    
    total_time = time.time() - total_start
    
    # Display
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"{'Row':<4} | {'Date':<10} | {'Result'}")
    print("-" * 50)
    for i, res in enumerate(final_results):
        print(f"{i:<4} | {data[i]['d']:<10} | {res}")
    
    print(f"\n{'='*60}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Performance: {len(data)/total_time:.2f} rows/sec")
    print(f"{'='*60}")
    print("\n Custom FHE implementation complete!")
    print(" No third-party FHE libraries used")
    print(" Pure Python + NumPy optimization")


if __name__ == "__main__":
    main()
