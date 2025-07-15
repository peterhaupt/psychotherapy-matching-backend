#!/bin/bash
# Backup Watchdog - Environment-aware monitoring for backup health
# Runs continuously in background, separate from cron system

# Get environment configuration
BACKUP_ENV="${BACKUP_ENV:-dev}"
WATCHDOG_LOG="/var/log/backup-watchdog.log"
CHECK_INTERVAL_SECONDS=300  # Check every 5 minutes
PID_FILE="/var/run/backup-watchdog.pid"

# Environment-specific configuration
case "$BACKUP_ENV" in
    "dev")
        BACKUP_DIR="/backups/postgres/dev"
        BACKUP_PREFIX="dev_backup"
        MAX_BACKUP_AGE_MINUTES=10  # Alert if backup older than 10 minutes (dev backs up every 5 min)
        ;;
    "test")
        BACKUP_DIR="/backups/postgres/test"
        BACKUP_PREFIX="test_backup"
        MAX_BACKUP_AGE_MINUTES=5   # Alert if backup older than 5 minutes (test backs up every 1 min)
        ;;
    "prod")
        BACKUP_DIR="/backups/postgres/hourly"
        BACKUP_PREFIX="backup"
        MAX_BACKUP_AGE_MINUTES=120 # Alert if backup older than 2 hours (prod backs up hourly)
        ;;
    *)
        echo "❌ ERROR: Unknown BACKUP_ENV: $BACKUP_ENV"
        exit 1
        ;;
esac

# Set proper PATH
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Function to log watchdog messages
log_watchdog() {
    local message="$1"
    local log_entry="[$(date '+%Y-%m-%d %H:%M:%S')] WATCHDOG[$BACKUP_ENV]: $message"
    echo "$log_entry" | tee -a "$WATCHDOG_LOG"
}

# Function to update health status
update_health_status() {
    local status="$1"
    echo "$status" > /tmp/health/status
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
    
    # Start cron daemon
    crond -b
    
    if check_cron_running; then
        log_watchdog "✅ Cron restarted successfully"
        update_health_status "Cron restarted - monitoring active"
        return 0
    else
        log_watchdog "❌ Failed to restart cron"
        update_health_status "ERROR: Failed to restart cron"
        return 1
    fi
}

# Function to check backup freshness
check_backup_freshness() {
    # Create reference file for comparison
    local reference_file="/tmp/watchdog-reference-$(date +%s)"
    touch -d "${MAX_BACKUP_AGE_MINUTES} minutes ago" "$reference_file"
    
    # Find any backup newer than reference
    local recent_backup=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -type f -newer "$reference_file" 2>/dev/null | head -1)
    
    # Cleanup reference file
    rm -f "$reference_file"
    
    if [ -n "$recent_backup" ]; then
        # Get backup age for logging
        local backup_timestamp=$(stat -c%Y "$recent_backup" 2>/dev/null || echo 0)
        local current_timestamp=$(date +%s)
        local backup_age_seconds=$(( current_timestamp - backup_timestamp ))
        local backup_age_minutes=$(( backup_age_seconds / 60 ))
        
        log_watchdog "✅ Recent backup found: $(basename "$recent_backup") (${backup_age_minutes} minutes old)"
        update_health_status "Backup system healthy - last backup ${backup_age_minutes} minutes ago"
        return 0
    else
        log_watchdog "⚠️ No recent backups found (older than ${MAX_BACKUP_AGE_MINUTES} minutes)"
        update_health_status "WARNING: No recent backups (>${MAX_BACKUP_AGE_MINUTES} min old)"
        return 1
    fi
}

# Function to check database connectivity
check_database_connectivity() {
    local db_host="${DB_HOST}"
    local db_port="${DB_PORT:-5432}"
    local db_user="${DB_USER}"
    local db_password="${DB_PASSWORD}"
    
    if [ -z "$db_host" ] || [ -z "$db_user" ]; then
        log_watchdog "⚠️ Database connection info not available for connectivity check"
        return 1
    fi
    
    if PGPASSWORD="$db_password" pg_isready -h "$db_host" -p "$db_port" -U "$db_user" >/dev/null 2>&1; then
        log_watchdog "✅ Database connectivity OK"
        return 0
    else
        log_watchdog "❌ Database not accessible"
        update_health_status "ERROR: Database not accessible"
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
log_watchdog "🐕 Backup watchdog starting for environment: $BACKUP_ENV"
log_watchdog "📍 PID: $$"
log_watchdog "⏰ Check interval: ${CHECK_INTERVAL_SECONDS} seconds ($(( CHECK_INTERVAL_SECONDS / 60 )) minutes)"
log_watchdog "📅 Max backup age: ${MAX_BACKUP_AGE_MINUTES} minutes"
log_watchdog "📂 Monitoring directory: $BACKUP_DIR"
log_watchdog "🏷️  Backup prefix: $BACKUP_PREFIX"

# Create PID file
create_pid_file

# Initialize health status
update_health_status "Watchdog starting..."

# Initial checks
if ! check_cron_running; then
    log_watchdog "⚠️ Cron not running at startup, starting it..."
    restart_cron
else
    log_watchdog "✅ Cron daemon running at startup"
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
    
    # Check database connectivity
    if check_database_connectivity; then
        # Only check backup freshness if database is accessible
        if ! check_backup_freshness; then
            log_watchdog "❌ Backup system appears to be failing"
            
            # Try to restart cron as a recovery measure
            restart_cron
            
            # Wait a bit longer after restart
            log_watchdog "⏳ Waiting extra time after cron restart..."
            sleep 60  # Wait 1 minute
        fi
    else
        log_watchdog "⚠️ Skipping backup freshness check due to database connectivity issues"
    fi
    
    # Check disk space (no 'local' keyword here - these are in the main script body)
    disk_usage=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//' 2>/dev/null || echo 0)
    disk_available=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}' 2>/dev/null || echo "Unknown")
    
    if [ "$disk_usage" -gt 90 ]; then
        log_watchdog "🚨 CRITICAL disk usage: ${disk_usage}% (${disk_available} available)"
        update_health_status "CRITICAL: Disk usage ${disk_usage}%"
    elif [ "$disk_usage" -gt 80 ]; then
        log_watchdog "⚠️ High disk usage: ${disk_usage}% (${disk_available} available)"
    else
        log_watchdog "💾 Disk usage: ${disk_usage}% (${disk_available} available)"
    fi
    
    # Count total backups based on environment (no 'local' keyword here)
    if [ "$BACKUP_ENV" = "prod" ]; then
        hourly_count=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f 2>/dev/null | wc -l)
        weekly_count=$(find "/backups/postgres/weekly" -name "weekly_backup_*.sql.gz" -type f 2>/dev/null | wc -l)
        manual_count=$(find "/backups/postgres/manual" -name "backup_*.sql.gz" -type f 2>/dev/null | wc -l)
        log_watchdog "📊 Backup inventory: $hourly_count hourly, $weekly_count weekly, $manual_count manual"
    else
        backup_count=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -type f 2>/dev/null | wc -l)
        log_watchdog "📊 Total ${BACKUP_ENV} backups: $backup_count"
    fi
    
    log_watchdog "😴 Sleeping for $(( CHECK_INTERVAL_SECONDS / 60 )) minutes..."
    
    # Sleep with ability to wake up on signals
    sleep $CHECK_INTERVAL_SECONDS &
    wait $!
done