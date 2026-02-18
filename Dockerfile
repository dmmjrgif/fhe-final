# Use Python 3.9 Slim
FROM python:3.9-slim

# Install System Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Working Directory (Root)
WORKDIR /app

# Copy ALL files from your repo into /app
COPY complete_fhe_package /app

# --- ⬇️ THIS IS THE FIX ⬇️ ---
# Tell Docker to go INSIDE the subfolder where setup.py actually lives
WORKDIR /app/complete_fhe_package
# -----------------------------

# Install Python Dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests numpy psutil streamlit

# Compile the C++ Extension (Now it will find setup.py!)
RUN python setup.py build_ext --inplace

# Expose Port
EXPOSE 8000

# Start Server (This also needs to run from inside that folder)
CMD ["uvicorn", "server_api:app", "--host", "0.0.0.0", "--port", "8000"]