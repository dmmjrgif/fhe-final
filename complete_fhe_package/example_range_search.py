"""
REQUIRES: pip install psutil
"""
import sys
import os
import time
import random
import threading
import psutil

# Ensure we can import the library
sys.path.append(os.getcwd())
try:
    from example_accelerated import BFVSchemeAccelerated
except ImportError:
    print("ERROR: Could not import library. Ensure 'example_accelerated.py' is in this folder.")
    exit(1)

# ==========================================
# RESOURCE MONITOR (ADDED)
# ==========================================
class ResourceMonitor:
    def __init__(self, interval=0.01):
        self.interval = interval
        self.running = False
        self.peak_cpu = 0.0
        self.peak_ram = 0.0
        self.thread = None

    def start(self):
        self.running = True
        self.peak_cpu = 0.0
        self.peak_ram = 0.0
        # Reset current process CPU counter
        p = psutil.Process(os.getpid())
        p.cpu_percent(interval=None)

        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        return self.peak_cpu, self.peak_ram

    def _monitor_loop(self):
        p = psutil.Process(os.getpid())
        while self.running:
            try:
                # CPU percent since last call
                c = p.cpu_percent(interval=None)
                # RAM in MB
                m = p.memory_info().rss / (1024 * 1024)

                if c > self.peak_cpu: self.peak_cpu = c
                if m > self.peak_ram: self.peak_ram = m
            except:
                pass
            time.sleep(self.interval)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def string_to_ints(s, max_len=12):
    b = s.encode('utf-8')
    return [x for x in (b[:max_len] + b'\x00'*(max_len-len(b)))]

def ints_to_string(ints):
    chars = []
    for val in ints:
        if val == 0: break
        chars.append(chr(int(val)))
    return ''.join(chars)

class FastFHE_MultiMatch:
    def __init__(self):
        # LARGE T: 33 million (Safe for subtraction)
        self.t = 33554432
        self.N = 4096

        # Suppress internal prints
        self.HE = BFVSchemeAccelerated(N=self.N, t=self.t, q_bits=62)
        self.HE.key_generation()
        self.HE.generate_relin_key()

    def encrypt_int(self, val):
        pt = self.HE.encode([val])
        return self.HE.encrypt(pt)

    def encrypt_batch(self, values):
        pt = self.HE.encode(values)
        return self.HE.encrypt(pt)

    def decrypt_batch(self, ctxt, num=None):
        pt = self.HE.decrypt(ctxt)
        poly = pt.get_poly()
        half_t = self.t // 2
        import numpy as np
        centered = np.where(poly > half_t, poly - self.t, poly)
        if num: return centered[:num].tolist()
        return centered.tolist()

    def homomorphic_sub(self, ct1, ct2):
        c1_0, c1_1 = ct1.get_components()
        c2_0, c2_1 = ct2.get_components()
        d0 = self.HE.poly_ring.sub(c1_0, c2_0)
        d1 = self.HE.poly_ring.sub(c1_1, c2_1)
        from custom_fhe.ciphertext import Ciphertext
        return Ciphertext([d0, d1], params=ct1.params)

def generate_dataset(num_rows=28):
    data = []
    base_date = 20260201
    for i in range(num_rows):
        day_offset = random.randint(0, 27)
        date = base_date + day_offset
        email = f"user{i:02d}@mail.com"
        data.append({"d": date, "e": email})

    # Inject targets
    data[5] = {"d": 20260210, "e": "target1@ok.c"}
    data[15] = {"d": 20260211, "e": "target2@ok.c"}
    data[25] = {"d": 20260212, "e": "target3@ok.c"}
    return data

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    monitor = ResourceMonitor()
    metrics = {}

    print("=" * 70)
    print(" FHE: PRIVATE DATABASE SEARCH DEMO")
    print("=" * 70)
    print("SCENARIO:")
    print("1. CLIENT has private data (dates/emails).")
    print("2. SERVER has computing power but MUST NOT see the data.")
    print("3. Goal: Find emails for dates Feb 10-12 without revealing anything.")
    print("=" * 70)

    # --- STEP 1: CLIENT SETUP ---
    print("\n" + "-"*30)
    print(" [ CLIENT SIDE ] SETUP")
    print("-" * 30)
    print(" Generates Secret Key (kept safe) and Public Key (shared).")

    monitor.start()  # START MONITOR
    t_start = time.time()
    fhe = FastFHE_MultiMatch()
    t_init = time.time() - t_start
    cpu, ram = monitor.stop() # STOP MONITOR
    metrics['Init'] = (t_init, cpu, ram)

    print(f" Keys Generated ({t_init:.2f}s)")

    # --- STEP 2: CLIENT ENCRYPTION ---
    print("\n Client Encrypts Database (28 Rows) because of Feb.")
    data = generate_dataset(28)

    monitor.start()  # START MONITOR
    t_start = time.time()
    enc_data = []
    for row in data:
        enc_data.append({
            'date': fhe.encrypt_int(row['d']),
            'email': fhe.encrypt_batch(string_to_ints(row['e']))
        })
    t_encrypt_db = time.time() - t_start
    cpu, ram = monitor.stop() # STOP MONITOR
    metrics['Encrypt'] = (t_encrypt_db, cpu, ram)

    print(f" Database Encrypted. Sending to Server... ({t_encrypt_db:.2f}s)")

    # --- SERVER VIEW DEMO ---
    print("\n" + "!"*60)
    print("  [ SERVER SIDE ] WHAT DOES THE SERVER SEE?")
    print("!" * 60)
    print("The Server inspects Row and what it sees:")
    #print("Decoding Ciphertext without Secret Key:")

    # Peek at the raw polynomial of the first ciphertext
    raw_c0 = enc_data[5]['email'].get_components()[0][:5] # First 5 coeffs
    print(f"   RAW DATA: {raw_c0} ...")
    print("   INTERPRETATION: [  RANDOM NOISE  ]")
    print("   Does Server know the email? NO.")
    print("   Does Server know the date?  NO.")
    print("!" * 60)

    # --- STEP 3: QUERY GENERATION ---
    print("\n" + "-"*30)
    print(" [ CLIENT SIDE ] QUERY")
    print("-" * 30)
    start_d, end_d = 20260210, 20260212
    target_range = list(range(start_d, end_d + 1))
    print(f" Client wants emails for range: {start_d} to {end_d}")
    print(" Client Encrypts these 3 dates into a Search Token.")

    monitor.start()  # START MONITOR
    t_start = time.time()
    enc_targets = [fhe.encrypt_int(t) for t in target_range]
    t_encrypt_query = time.time() - t_start
    cpu, ram = monitor.stop() # STOP MONITOR
    metrics['Query'] = (t_encrypt_query, cpu, ram)

    print(f" Query Encrypted & Sent. ({t_encrypt_query:.2f}s)")

    # --- STEP 4: SERVER PROCESSING ---
    print("\n" + "-"*30)
    print("  [ SERVER SIDE ] PROCESSING")
    print("-" * 30)
    print(" Server performs Homomorphic Subtraction on all 28 rows.")
    print(" Logic: (Encrypted_Row_Date - Encrypted_Query_Date)")
    print(" Server DOES NOT decrypt. It operates blindly.")

    monitor.start()  # START MONITOR
    t_start = time.time()
    server_results = []

    for row in enc_data:
        row_diffs = []
        for target_enc in enc_targets:
            diff = fhe.homomorphic_sub(row['date'], target_enc)
            row_diffs.append(diff)
        server_results.append({'email': row['email'], 'diffs': row_diffs})

    t_process = time.time() - t_start
    cpu, ram = monitor.stop() # STOP MONITOR
    metrics['Search'] = (t_process, cpu, ram)

    print(f" Search Complete. Processing Time: {t_process:.4f}s ")
    print(" Server sends back encrypted results (still looks like noise).")

    # --- STEP 5: CLIENT DECRYPTION ---
    print("\n" + "-"*30)
    print(" [ CLIENT SIDE ] RESULT")
    print("-" * 30)
    print(" Client uses Secret Key to decrypt the results.")
    print(" If (Result == 0), it's a match. Otherwise, ignore.")

    monitor.start()  # START MONITOR
    t_start = time.time()
    matches = []
    for i, res in enumerate(server_results):
        is_match = False
        for diff_ct in res['diffs']:
            # Decrypt: Only Client can do this!
            val = fhe.decrypt_batch(diff_ct, num=1)[0]
            if val == 0:
                is_match = True
                break

        if is_match:
            email_ints = fhe.decrypt_batch(res['email'], num=12)
            matched_email = ints_to_string(email_ints)
            matches.append(f"Row {i:<2} | {data[i]['d']} | MATCH FOUND -> {matched_email}")

    t_decrypt = time.time() - t_start
    cpu, ram = monitor.stop() # STOP MONITOR
    metrics['Decrypt'] = (t_decrypt, cpu, ram)

    print("\nDecrypted Matches:")
    for m in matches:
        print(m)

    print(f"\nTotal Matches: {len(matches)}")
    print("=" * 70)

    # --- PERFORMANCE TABLE (ADDED) ---
    print("\n" + "=" * 70)
    print(f"{'STAGE':<15} | {'TIME (s)':<10} | {'PEAK CPU %':<12} | {'PEAK RAM (MB)':<15}")
    print("-" * 70)
    for stage, (t, c, r) in metrics.items():
        print(f"{stage:<15} | {t:<10.4f} | {c:<12.1f} | {r:<15.1f}")
    print("=" * 70)

if __name__ == "__main__":
    main()
