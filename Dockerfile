# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Plex Collection Cleanup"
LABEL description="Docker container for scheduled/on-demand Plex collection cleanup"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and scheduler script
COPY plex_clean_collections.py .
COPY scheduler.sh .

# Make scheduler script executable
RUN chmod +x scheduler.sh

# Create logs directory
RUN mkdir -p /var/log && touch /var/log/plex-cleanup.log

# Set default environment variables for Docker
ENV PLEX_DRY_RUN=true
ENV PLEX_NO_CONFIRM=true
ENV PLEX_DEBUG=false
ENV PLEX_SCHEDULE="0 2 * * 0"
ENV PLEX_RUN_ONCE=false
ENV PLEX_DELETE_LABELS=""
ENV PLEX_DELETE_LABEL_PATTERNS=""

# Default command runs the scheduler (which can run once or schedule based on env vars)
CMD ["./scheduler.sh"]