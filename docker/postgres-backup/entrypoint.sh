#!/bin/bash
# Entrypoint script for postgres-backup containers
# Sets up environment-specific cron schedules and starts all services

set -e

# Get environment configuration
BACKUP_ENV="${BACKUP_ENV:-dev}"
LOG_FILE="/var/log/backup.log"

echo "🚀 Starting Curavani Backup Service for environment: $BACKUP_ENV"
echo "================================================================="

# Function to log startup messages
log_startup() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [STARTUP] $message" | tee -a "$LOG_FILE"
}

# Validate required environment variables
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ] || [ -z "$DB_HOST" ]; then
    log_startup "❌ ERROR: Required environment variables missing"
    log_startup "   Required: DB_USER, DB_NAME, DB_HOST"
    log_startup "   DB_USER: ${DB_USER:-<not set>}"
    log_startup "   DB_NAME: ${DB_NAME:-<not set>}"
    log_startup "   DB_HOST: ${DB_HOST:-<not set>}"
    exit 1
fi

# Set defaults for optional variables
export DB_PORT="${DB_PORT:-5432}"

log_startup "📊 Configuration:"
log_startup "   Environment: $BACKUP_ENV"
log_startup "   Database: $DB_NAME on $DB_HOST:$DB_PORT"
log_startup "   User: $DB_USER"

# Create log directories and set permissions (as root)
mkdir -p /var/log /var/run /tmp/health
touch "$LOG_FILE" /var/log/backup-watchdog.log

# Set proper ownership for backup user
chown -R backup:backup /backups /var/log /var/run /tmp/health

# Initialize health status
echo "Service starting..." > /tmp/health/status

# Environment-specific cron schedule setup
log_startup "⏰ Setting up cron schedule for $BACKUP_ENV environment..."

case "$BACKUP_ENV" in
    "dev")
        # Every 5 minutes for development
        CRON_SCHEDULE="*/5 * * * *"
        log_startup "   Schedule: Every 5 minutes"
        ;;
    "test")
        # Every 1 minute for testing
        CRON_SCHEDULE="* * * * *"
        log_startup "   Schedule: Every 1 minute"
        ;;
    "prod")
        # Every hour for production
        CRON_SCHEDULE="0 * * * *"
        log_startup "   Schedule: Every hour (at minute 0)"
        ;;
    *)
        log_startup "❌ ERROR: Unknown BACKUP_ENV: $BACKUP_ENV"
        exit 1
        ;;
esac

# Create crontab for root user (but run backup script as backup user)
log_startup "📝 Creating crontab with schedule: $CRON_SCHEDULE"

# Create wrapper script that preserves environment variables
cat > /tmp/backup-wrapper.sh << EOF
#!/bin/bash
export BACKUP_ENV="$BACKUP_ENV"
export DB_USER="$DB_USER"
export DB_PASSWORD="$DB_PASSWORD"
export DB_NAME="$DB_NAME"
export DB_HOST="$DB_HOST"
export DB_PORT="$DB_PORT"
exec /usr/local/bin/backup-script.sh
EOF
chmod +x /tmp/backup-wrapper.sh
chown backup:backup /tmp/backup-wrapper.sh

echo "$CRON_SCHEDULE su backup -c '/tmp/backup-wrapper.sh' >> $LOG_FILE 2>&1" > /tmp/backup-crontab

# Install crontab as root
crontab /tmp/backup-crontab
rm /tmp/backup-crontab

log_startup "✅ Crontab installed successfully"

# Start cron daemon
log_startup "⏰ Starting cron daemon..."
crond -b

# Wait a moment and verify cron started
sleep 2
if pgrep crond >/dev/null 2>&1; then
    log_startup "✅ Cron daemon started successfully"
else
    log_startup "❌ ERROR: Failed to start cron daemon"
    exit 1
fi

# Start backup watchdog in background AS ROOT (it needs to manage cron)
log_startup "🐕 Starting backup watchdog..."

# Create watchdog wrapper that preserves environment
cat > /tmp/watchdog-wrapper.sh << EOF
#!/bin/bash
export BACKUP_ENV="$BACKUP_ENV"
export DB_USER="$DB_USER"
export DB_PASSWORD="$DB_PASSWORD"
export DB_NAME="$DB_NAME"
export DB_HOST="$DB_HOST"
export DB_PORT="$DB_PORT"
exec /usr/local/bin/backup-watchdog.sh
EOF
chmod +x /tmp/watchdog-wrapper.sh

# Run watchdog as ROOT (not as backup user)
/tmp/watchdog-wrapper.sh &
WATCHDOG_PID=$!

# Wait a moment and verify watchdog started
sleep 2
if kill -0 $WATCHDOG_PID 2>/dev/null; then
    log_startup "✅ Backup watchdog started successfully (PID: $WATCHDOG_PID)"
else
    log_startup "❌ ERROR: Failed to start backup watchdog"
    exit 1
fi

# Start HTTP server for health checks in background AS ROOT (needs access to /tmp/health)
log_startup "🌐 Starting health check HTTP server on port 8080..."

# Create HTTP server wrapper
cat > /tmp/http-wrapper.sh << EOF
#!/bin/bash
exec /usr/local/bin/http-server.sh
EOF
chmod +x /tmp/http-wrapper.sh

# Run HTTP server as ROOT (not as backup user)
/tmp/http-wrapper.sh &
HTTP_PID=$!

# Wait a moment and verify HTTP server started
sleep 2
if kill -0 $HTTP_PID 2>/dev/null; then
    log_startup "✅ Health check server started successfully (PID: $HTTP_PID)"
else
    log_startup "❌ ERROR: Failed to start health check server"
    exit 1
fi

# Update health status
echo "Backup service ready - $BACKUP_ENV environment" > /tmp/health/status

log_startup "================================================================="
log_startup "✅ Backup service startup complete!"
log_startup "   Environment: $BACKUP_ENV"
log_startup "   Cron schedule: $CRON_SCHEDULE"
log_startup "   Health endpoint: http://container:8080/"
log_startup "   Log file: $LOG_FILE"
log_startup "================================================================="

# Function to handle shutdown signals
shutdown() {
    log_startup "🛑 Received shutdown signal"
    
    # Stop watchdog
    if kill -0 $WATCHDOG_PID 2>/dev/null; then
        log_startup "🐕 Stopping backup watchdog..."
        kill $WATCHDOG_PID
    fi
    
    # Stop HTTP server
    if kill -0 $HTTP_PID 2>/dev/null; then
        log_startup "🌐 Stopping health check server..."
        kill $HTTP_PID
    fi
    
    # Stop cron
    log_startup "⏰ Stopping cron daemon..."
    killall crond 2>/dev/null || true
    
    log_startup "✅ Backup service shutdown complete"
    exit 0
}

# Set up signal handlers
trap shutdown TERM INT

# Keep the container running and monitor child processes
log_startup "👁️  Monitoring child processes..."

while true; do
    # Check if cron is still running
    if ! pgrep crond >/dev/null 2>&1; then
        log_startup "❌ Cron daemon died, restarting..."
        crond -b
    fi
    
    # Check if watchdog is still running
    if ! kill -0 $WATCHDOG_PID 2>/dev/null; then
        log_startup "❌ Watchdog died, restarting..."
        /tmp/watchdog-wrapper.sh &
        WATCHDOG_PID=$!
    fi
    
    # Check if HTTP server is still running
    if ! kill -0 $HTTP_PID 2>/dev/null; then
        log_startup "❌ HTTP server died, restarting..."
        /tmp/http-wrapper.sh &
        HTTP_PID=$!
    fi
    
    # Sleep for 30 seconds before next check
    sleep 30
done