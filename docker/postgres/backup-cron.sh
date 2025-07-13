#!/bin/bash
# Backup script for Curavani production database - runs inside postgres container
# Fixed version with proper environment variable handling and error checking

# Set proper PATH for cron environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Backup configuration
BACKUP_DIR="/backups/postgres/hourly"
WEEKLY_DIR="/backups/postgres/weekly"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/backup.log"

# Database configuration - using environment variables directly
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"
DB_HOST="${POSTGRES_HOST}"
DB_PORT="${POSTGRES_PORT}"

# Validate required environment variables
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    log_message "❌ ERROR: Required environment variables POSTGRES_USER and POSTGRES_DB must be set"
    exit 1
fi

# Set defaults only for optional variables
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$WEEKLY_DIR"

# Function to log messages with proper formatting
log_message() {
    local message="$1"
    local log_entry="[$(date '+%Y-%m-%d %H:%M:%S')] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

# Function to check if PostgreSQL is ready
check_postgres_ready() {
    local retries=5
    local count=0
    
    while [ $count -lt $retries ]; do
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
            return 0
        fi
        count=$((count + 1))
        sleep 2
    done
    return 1
}

# Function to get database size for logging
get_db_size() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | tr -d ' \n' || echo "Unknown"
}

# Start backup process
log_message "Starting hourly backup for database: $DB_NAME"
log_message "Using PostgreSQL user: $DB_USER"

# Check if PostgreSQL is ready
if ! check_postgres_ready; then
    log_message "❌ ERROR: PostgreSQL is not ready or not accessible"
    exit 1
fi

# Get database size before backup
DB_SIZE=$(get_db_size)
log_message "📊 Database size: $DB_SIZE"

# Create backup filename
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Create the backup
log_message "📦 Creating backup: backup_$TIMESTAMP.sql.gz"

# Use pg_dump with proper error handling
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null | gzip > "$BACKUP_FILE"; then
    # Verify the backup file was created and is not empty
    if [ -s "$BACKUP_FILE" ]; then
        # Get backup file size
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_message "✅ Backup created successfully: backup_$TIMESTAMP.sql.gz (Size: $BACKUP_SIZE)"
        
        # Verify backup integrity by testing gunzip
        if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
            log_message "✅ Backup integrity verified"
        else
            log_message "⚠️  WARNING: Backup file may be corrupted"
        fi
    else
        log_message "❌ ERROR: Backup file is empty or was not created properly"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
else
    log_message "❌ ERROR: pg_dump command failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Cleanup old hourly backups (keep last 7 days = 168 hours)
log_message "🗑️  Cleaning up old hourly backups..."
DELETED_FILES=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -type f)
if [ -n "$DELETED_FILES" ]; then
    DELETED_COUNT=$(echo "$DELETED_FILES" | wc -l)
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -type f -delete
    log_message "🗑️  Cleaned up $DELETED_COUNT old hourly backup(s)"
else
    log_message "🗑️  No old hourly backups to clean up"
fi

# Create weekly backup on Sundays at midnight hour (00:xx)
CURRENT_DAY=$(date +%w)  # 0 = Sunday
CURRENT_HOUR=$(date +%H)

if [ "$CURRENT_DAY" -eq 0 ] && [ "$CURRENT_HOUR" -eq 0 ]; then
    WEEKLY_BACKUP="$WEEKLY_DIR/weekly_backup_$(date +%Y%m%d).sql.gz"
    if cp "$BACKUP_FILE" "$WEEKLY_BACKUP"; then
        log_message "📅 Created weekly backup: weekly_backup_$(date +%Y%m%d).sql.gz"
        
        # Cleanup old weekly backups (keep for 3 months = 90 days)
        DELETED_WEEKLY=$(find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -mtime +90 -type f)
        if [ -n "$DELETED_WEEKLY" ]; then
            DELETED_WEEKLY_COUNT=$(echo "$DELETED_WEEKLY" | wc -l)
            find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -mtime +90 -type f -delete
            log_message "🗑️  Cleaned up $DELETED_WEEKLY_COUNT old weekly backup(s)"
        fi
    else
        log_message "❌ ERROR: Failed to create weekly backup"
    fi
fi

# Check disk space and warn if running low
DISK_USAGE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAILABLE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}')

if [ "$DISK_USAGE" -gt 80 ]; then
    log_message "⚠️  WARNING: Disk usage is at ${DISK_USAGE}% (${DISK_AVAILABLE} available)"
elif [ "$DISK_USAGE" -gt 90 ]; then
    log_message "🚨 CRITICAL: Disk usage is at ${DISK_USAGE}% (${DISK_AVAILABLE} available)"
else
    log_message "💾 Disk usage: ${DISK_USAGE}% (${DISK_AVAILABLE} available)"
fi

# Count current backups
HOURLY_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f | wc -l)
WEEKLY_COUNT=$(find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -type f | wc -l)
log_message "📊 Backup inventory: $HOURLY_COUNT hourly, $WEEKLY_COUNT weekly"

# Rotate log file if it's too large (>10MB)
if [ -f "$LOG_FILE" ]; then
    # Check file size (different commands for different systems)
    LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
    if [ "$LOG_SIZE" -gt 10485760 ]; then
        # Keep last 100 lines of the current log
        tail -100 "$LOG_FILE" > "$LOG_FILE.tmp"
        mv "$LOG_FILE.tmp" "$LOG_FILE"
        log_message "📝 Log file rotated (was $(echo "scale=1; $LOG_SIZE/1024/1024" | bc 2>/dev/null || echo ">10")MB)"
    fi
fi

log_message "✅ Backup process completed successfully"

# Exit successfully
exit 0