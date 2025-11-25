# Dockerfile for Cloud Functions Gen 2 (Python)
# This is only needed if using container image instead of standard runtime

FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY main.py .

# Cloud Functions Gen 2 expects the function to be available
# The entry point is set in the function configuration
# No CMD needed - Cloud Functions handles the invocation

