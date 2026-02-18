# server_api.py
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import pickle
import sys
import os

# Import your FHE Library
# Ensure 'example_accelerated.py' and 'custom_fhe' are in the same folder
from complete_fhe_package.example_accelerated import BFVSchemeAccelerated

app = FastAPI()

# Initialize FHE Context (Public Parameters Only)
# The server DOES NOT need keys, just N, t, q.
print("Initializing FHE Backend...")
SERVER_FHE = BFVSchemeAccelerated(N=4096, t=33554432, q_bits=62)


@app.get("/")
def home():
    return {"status": "FHE Server Online", "backend": "C++ Accelerated"}


@app.post("/search")
async def blind_search(
        db_file: UploadFile = File(...),
        query_file: UploadFile = File(...)
):
    """
    Receives: Encrypted Database + Encrypted Query
    Returns: Encrypted Search Results
    """
    # 1. Load the binary data (Pickled objects)
    encrypted_db = pickle.load(db_file.file)
    encrypted_query = pickle.load(query_file.file)

    print(f"Processing {len(encrypted_db)} rows...")

    # 2. Perform Blind Search (Homomorphic Subtraction)
    results = []
    for row in encrypted_db:
        # Assuming row is a dictionary {'data': ciphertext}
        # and query is a list of ciphertexts
        diffs = []
        for target in encrypted_query:
            # CALLING YOUR C++ ACCELERATED FUNCTION
            # Note: We assume your library supports direct subtraction like this
            # You might need to adapt this based on your exact object structure
            diff = SERVER_FHE.homomorphic_sub(row['date'], target)
            diffs.append(diff)
        results.append({'id': row['id'], 'diffs': diffs})

    # 3. Serialize and Return Results
    return pickle.dumps(results)