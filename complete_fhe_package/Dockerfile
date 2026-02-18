# Use Python 3.9 Slim
FROM python:3.9-slim

# Install C++ Compiler and Build Tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Working Directory
WORKDIR /app

# Copy ALL files from your GitHub repo into the /app folder
COPY .. /app

# Install Python Dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests numpy psutil streamlit

# ⚡ COMPILE C++ EXTENSION ⚡
# We use 'ls' first just to see where we are (helpful for debugging logs)
RUN python setup_cpp.py build_ext --inplace

# Expose API Port
EXPOSE 8000

# Start the Server
CMD ["uvicorn", "server_api:app", "--host", "0.0.0.0", "--port", "8000"]