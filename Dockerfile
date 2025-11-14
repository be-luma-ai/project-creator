# Dockerfile for Cloud Run

FROM python:3.10-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg for video compression)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port for Cloud Run
EXPOSE 8080

# Command to run the app
CMD ["uvicorn", "scripts.main:app", "--host", "0.0.0.0", "--port", "8080"]