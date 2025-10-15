#!/bin/bash

# Plex Collection Cleanup Scheduler
# This script can either run once immediately or set up a cron schedule

set -e

# Default values
SCHEDULE="${PLEX_SCHEDULE:-0 2 * * 0}"  # Default: 2 AM every Sunday
RUN_ONCE="${PLEX_RUN_ONCE:-false}"
LOG_LEVEL="${PLEX_DEBUG:-false}"

echo "=== Plex Collection Cleanup ==="
echo "Run Once: $RUN_ONCE"
echo "Schedule: $SCHEDULE"
echo "Debug: $LOG_LEVEL"
echo "Dry Run: ${PLEX_DRY_RUN:-true}"
echo "==============================="

# Validate required environment variables
if [ -z "$PLEX_URL" ]; then
    echo "ERROR: PLEX_URL environment variable is required"
    exit 1
fi

if [ -z "$PLEX_TOKEN" ]; then
    echo "ERROR: PLEX_TOKEN environment variable is required"
    exit 1
fi

# If RUN_ONCE is true, run immediately and exit
if [ "$RUN_ONCE" = "true" ]; then
    echo "Running cleanup immediately..."
    cd /app && python plex_clean_collections.py
    echo "Cleanup completed!"
    exit 0
fi

# Install cron if not present
if ! command -v crontab >/dev/null 2>&1; then
    echo "Installing cron..."
    apt-get update && apt-get install -y cron
fi

# Create the cron command
CRON_CMD="cd /app && python plex_clean_collections.py"

# Add environment variables to the cron command
CRON_ENV="PLEX_URL='$PLEX_URL' PLEX_TOKEN='$PLEX_TOKEN' PLEX_DRY_RUN='${PLEX_DRY_RUN:-true}' PLEX_NO_CONFIRM='${PLEX_NO_CONFIRM:-true}' PLEX_DEBUG='${PLEX_DEBUG:-false}'"

# Create the full cron entry
CRON_ENTRY="$SCHEDULE $CRON_ENV $CRON_CMD >> /var/log/plex-cleanup.log 2>&1"

echo "Setting up cron job..."
echo "Cron entry: $CRON_ENTRY"

# Add the cron job
echo "$CRON_ENTRY" | crontab -

# Start cron service
echo "Starting cron service..."
service cron start

# Display current crontab
echo "Current crontab:"
crontab -l

# Create log file
touch /var/log/plex-cleanup.log
chmod 666 /var/log/plex-cleanup.log

echo "Scheduler setup complete!"
echo ""
echo "To run immediately (testing): docker-compose exec plex-clean-scheduled python plex_clean_collections.py"
echo "Log file: /var/log/plex-cleanup.log"
echo ""
echo "Cron schedule format: minute hour day_of_month month day_of_week"
echo "Examples:"
echo "  '0 2 * * 0'     - 2 AM every Sunday"
echo "  '0 3 * * 1'     - 3 AM every Monday"
echo "  '30 1 * * *'    - 1:30 AM every day"
echo "  '0 12 1 * *'    - 12 PM on the 1st of every month"
echo "  '*/15 * * * *'  - Every 15 minutes"

# Keep container running and monitor logs
echo ""
echo "Container is now running. Press Ctrl+C to stop."
echo "Monitoring log file..."

# Follow the log file
tail -f /var/log/plex-cleanup.log