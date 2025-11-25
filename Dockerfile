# Stage 1: Base Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - ffmpeg is required by yt-dlp for processing video and audio
# - git and other build tools are good to have for some dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY service.py .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
# Use --host 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
