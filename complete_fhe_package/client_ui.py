# client_ui.py
import streamlit as st
import requests
import pickle
import time
from example_accelerated import BFVSchemeAccelerated

# CONFIG
SERVER_URL = "http://localhost:8000/search"  # Change this to your Cloud URL later

st.title("🔒 Private Database Search")
st.write("Upload your encrypted data. The server will process it blindly.")

# 1. CLIENT INITIALIZATION (Local)
if 'fhe' not in st.session_state:
    st.session_state.fhe = BFVSchemeAccelerated(N=4096, t=33554432, q_bits=62)
    st.session_state.fhe.key_generation()

# 2. DATA GENERATION & ENCRYPTION
if st.button("Generate & Encrypt Dummy Data"):
    with st.spinner("Encrypting locally..."):
        # Generate dummy data similar to your benchmark script
        data = [{"id": i, "date": st.session_state.fhe.encrypt_int(20260201 + i)} for i in range(10)]
        target = [st.session_state.fhe.encrypt_int(20260205)]  # Looking for Feb 5th

        # Save to session
        st.session_state.enc_db = pickle.dumps(data)
        st.session_state.enc_query = pickle.dumps(target)
        st.success("Data Encrypted! Keys remain on this machine.")

# 3. UPLOAD TO SERVER
if 'enc_db' in st.session_state:
    st.write("---")
    st.write("### ☁️ Server Interaction")

    if st.button("Send to Secure Server"):
        files = {
            'db_file': st.session_state.enc_db,
            'query_file': st.session_state.enc_query
        }

        with st.spinner("Server is processing (Homomorphic Search)..."):
            response = requests.post(SERVER_URL, files=files)

        if response.status_code == 200:
            st.success("Results Received!")
            encrypted_results = pickle.loads(response.content)

            # 4. DECRYPTION (Happens Locally)
            st.write("### 🔓 Decrypted Results")
            for res in encrypted_results:
                # Decrypt logic (simplified)
                is_match = False
                for diff in res['diffs']:
                    val = st.session_state.fhe.decrypt_batch(diff, num=1)[0]
                    if val == 0: is_match = True

                if is_match:
                    st.write(f"✅ Match Found at Row ID: {res['id']}")
        else:
            st.error("Server Error")