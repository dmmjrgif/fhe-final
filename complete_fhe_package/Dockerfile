# Use Python 3.9 Slim (Linux)
FROM python:3.9-slim

# Install C++ Compiler (GCC) and Build Tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Working Directory
WORKDIR /app

# Copy Project Files
COPY . /app

# Install Python Dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests numpy psutil streamlit

# ⚡ COMPILE C++ EXTENSION ⚡
# This ensures the .so file is built for the CLOUD server, not your local Windows PC
RUN python setup.py build_ext --inplace

# Expose API Port
EXPOSE 8000

# Start the Server
CMD ["uvicorn", "server_api:app", "--host", "0.0.0.0", "--port", "8000"]