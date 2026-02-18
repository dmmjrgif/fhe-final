# Use Python 3.9 Slim
FROM python:3.9-slim

# Install C++ Compiler, Build Tools AND CMake
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy files
COPY . /app

# Set Python Path
ENV PYTHONPATH="/app"

# Install Python Dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests numpy psutil streamlit

# ⚡ COMPILE C++ EXTENSION ⚡
RUN python setup_cpp.py build_ext --inplace

EXPOSE 8000

# Start the Server
CMD ["uvicorn", "server_api:app", "--host", "0.0.0.0", "--port", "8000"]