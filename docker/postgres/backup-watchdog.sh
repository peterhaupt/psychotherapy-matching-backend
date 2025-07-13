#!/bin/bash
# Backup Watchdog - Independent process to monitor backup health and restart cron if needed
# Runs continuously in background, separate from cron system

BACKUP_DIR="/backups/postgres/hourly"
WATCHDOG_LOG="/var/log/backup-watchdog.log"
CHECK_INTERVAL_SECONDS=1800  # Check every 30 minutes
MAX_BACKUP_AGE_HOURS=2       # Alert if backup older than 2 hours
PID_FILE="/var/run/backup-watchdog.pid"

# Set proper PATH
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Function to log watchdog messages
log_watchdog() {
    local message="$1"
    local log_entry="[$(date '+%Y-%m-%d %H:%M:%S')] WATCHDOG: $message"
    echo "$log_entry" | tee -a "$WATCHDOG_LOG"
}

# Function to check if cron is running
check_cron_running() {
    if pgrep crond >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to restart cron system
restart_cron() {
    log_watchdog "🔄 Restarting cron system..."
    
    # Kill existing cron processes
    killall crond 2>/dev/null
    sleep 2
    
    # Reload crontab and restart cron
    crontab /etc/crontabs/postgres 2>/dev/null
    crond -b
    
    if check_cron_running; then
        log_watchdog "✅ Cron restarted successfully"
        return 0
    else
        log_watchdog "❌ Failed to restart cron"
        return 1
    fi
}

# Function to check backup freshness
check_backup_freshness() {
    # Create reference file for comparison (2 hours ago)
    local reference_file="/tmp/watchdog-reference-$(date +%s)"
    touch -d "${MAX_BACKUP_AGE_HOURS} hours ago" "$reference_file"
    
    # Find any backup newer than reference
    local recent_backup=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f -newer "$reference_file" 2>/dev/null | head -1)
    
    # Cleanup reference file
    rm -f "$reference_file"
    
    if [ -n "$recent_backup" ]; then
        # Get backup age for logging
        local backup_age_seconds=$(( $(date +%s) - $(stat -c%Y "$recent_backup" 2>/dev/null || echo 0) ))
        local backup_age_minutes=$(( backup_age_seconds / 60 ))
        log_watchdog "✅ Recent backup found: $(basename "$recent_backup") (${backup_age_minutes} minutes old)"
        return 0
    else
        log_watchdog "⚠️ No recent backups found (older than ${MAX_BACKUP_AGE_HOURS} hours)"
        return 1
    fi
}

# Function to create PID file
create_pid_file() {
    echo $$ > "$PID_FILE"
}

# Function to cleanup on exit
cleanup() {
    log_watchdog "🛑 Watchdog shutting down"
    rm -f "$PID_FILE"
    exit 0
}

# Setup signal handlers
trap cleanup TERM INT

# Start watchdog
log_watchdog "🐕 Backup watchdog starting..."
log_watchdog "📍 PID: $$"
log_watchdog "⏰ Check interval: ${CHECK_INTERVAL_SECONDS} seconds ($(( CHECK_INTERVAL_SECONDS / 60 )) minutes)"
log_watchdog "📅 Max backup age: ${MAX_BACKUP_AGE_HOURS} hours"
log_watchdog "📂 Monitoring directory: $BACKUP_DIR"

# Create PID file
create_pid_file

# Initial checks
if ! check_cron_running; then
    log_watchdog "⚠️ Cron not running at startup, starting it..."
    restart_cron
fi

# Main watchdog loop
while true; do
    log_watchdog "🔍 Starting backup health check..."
    
    # Check if cron is still running
    if ! check_cron_running; then
        log_watchdog "❌ Cron daemon is not running!"
        restart_cron
    else
        log_watchdog "✅ Cron daemon is running"
    fi
    
    # Check backup freshness
    if ! check_backup_freshness; then
        log_watchdog "❌ Backup system appears to be failing"
        
        # Try to restart cron as a recovery measure
        restart_cron
        
        # Wait a bit longer after restart
        log_watchdog "⏳ Waiting extra time after cron restart..."
        sleep 300  # Wait 5 minutes
    fi
    
    # Check disk space
    local disk_usage=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        log_watchdog "⚠️ High disk usage: ${disk_usage}%"
    fi
    
    # Count total backups
    local backup_count=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f | wc -l)
    log_watchdog "📊 Total backups in directory: $backup_count"
    
    log_watchdog "😴 Sleeping for $(( CHECK_INTERVAL_SECONDS / 60 )) minutes..."
    
    # Sleep with ability to wake up on signals
    sleep $CHECK_INTERVAL_SECONDS &
    wait $!
done