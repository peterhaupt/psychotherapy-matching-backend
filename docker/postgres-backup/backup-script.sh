#!/bin/bash
# Environment-aware backup script for Curavani postgres databases
# Runs inside dedicated backup containers

# Set proper PATH for cron environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Get environment from BACKUP_ENV variable
BACKUP_ENV="${BACKUP_ENV:-dev}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/backup.log"

# Database configuration from environment variables
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
DB_NAME="${DB_NAME}"
DB_HOST="${DB_HOST}"
DB_PORT="${DB_PORT:-5432}"

# Environment-specific configuration
case "$BACKUP_ENV" in
    "dev")
        BACKUP_DIR="/backups/postgres/dev"
        BACKUP_PREFIX="dev_backup"
        RETENTION_DAYS=7
        ;;
    "test")
        BACKUP_DIR="/backups/postgres/test"
        BACKUP_PREFIX="test_backup"
        RETENTION_DAYS=7
        ;;
    "prod")
        BACKUP_DIR="/backups/postgres/hourly"
        WEEKLY_DIR="/backups/postgres/weekly"
        MANUAL_DIR="/backups/postgres/manual"
        BACKUP_PREFIX="backup"
        RETENTION_DAYS=7
        WEEKLY_RETENTION_DAYS=90
        ;;
    *)
        echo "❌ ERROR: Unknown BACKUP_ENV: $BACKUP_ENV"
        exit 1
        ;;
esac

# Validate required environment variables
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ] || [ -z "$DB_HOST" ]; then
    log_message "❌ ERROR: Required environment variables DB_USER, DB_NAME, and DB_HOST must be set"
    exit 1
fi

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"
if [ "$BACKUP_ENV" = "prod" ]; then
    mkdir -p "$WEEKLY_DIR" "$MANUAL_DIR"
fi

# Function to log messages with proper formatting
log_message() {
    local message="$1"
    local log_entry="[$(date '+%Y-%m-%d %H:%M:%S')] [$BACKUP_ENV] $message"
    echo "$log_entry" | tee -a "$LOG_FILE"
}

# Function to update health status
update_health_status() {
    local status="$1"
    echo "$status" > /tmp/health/status
}

# Function to check if PostgreSQL is ready
check_postgres_ready() {
    local retries=10
    local count=0
    
    while [ $count -lt $retries ]; do
        if PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
            return 0
        fi
        count=$((count + 1))
        sleep 2
    done
    return 1
}

# Function to get database size for logging
get_db_size() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | tr -d ' \n' || echo "Unknown"
}

# Start backup process
log_message "🚀 Starting backup for environment: $BACKUP_ENV"
log_message "📊 Database: $DB_NAME on $DB_HOST:$DB_PORT"
update_health_status "Backup starting..."

# Check if PostgreSQL is ready
if ! check_postgres_ready; then
    log_message "❌ ERROR: PostgreSQL is not ready or not accessible"
    update_health_status "ERROR: PostgreSQL not accessible"
    exit 1
fi

# Get database size before backup
DB_SIZE=$(get_db_size)
log_message "📊 Database size: $DB_SIZE"

# Create backup filename
BACKUP_FILE="$BACKUP_DIR/${BACKUP_PREFIX}_$TIMESTAMP.sql.gz"

# Create the backup
log_message "📦 Creating backup: ${BACKUP_PREFIX}_$TIMESTAMP.sql.gz"
update_health_status "Creating backup..."

# Use pg_dump with proper error handling
if PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null | gzip > "$BACKUP_FILE"; then
    # Verify the backup file was created and is not empty
    if [ -s "$BACKUP_FILE" ]; then
        # Get backup file size
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_message "✅ Backup created successfully: ${BACKUP_PREFIX}_$TIMESTAMP.sql.gz (Size: $BACKUP_SIZE)"
        
        # Verify backup integrity by testing gunzip
        if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
            log_message "✅ Backup integrity verified"
            update_health_status "Backup completed successfully at $(date)"
        else
            log_message "⚠️  WARNING: Backup file may be corrupted"
            update_health_status "WARNING: Backup may be corrupted"
        fi
    else
        log_message "❌ ERROR: Backup file is empty or was not created properly"
        rm -f "$BACKUP_FILE"
        update_health_status "ERROR: Backup file empty"
        exit 1
    fi
else
    log_message "❌ ERROR: pg_dump command failed"
    rm -f "$BACKUP_FILE"
    update_health_status "ERROR: pg_dump failed"
    exit 1
fi

# Environment-specific cleanup and special operations
case "$BACKUP_ENV" in
    "dev"|"test")
        # Cleanup old backups (keep for specified retention days)
        log_message "🗑️  Cleaning up old $BACKUP_ENV backups..."
        DELETED_FILES=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -mtime +$RETENTION_DAYS -type f)
        if [ -n "$DELETED_FILES" ]; then
            DELETED_COUNT=$(echo "$DELETED_FILES" | wc -l)
            find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -mtime +$RETENTION_DAYS -type f -delete
            log_message "🗑️  Cleaned up $DELETED_COUNT old backup(s)"
        else
            log_message "🗑️  No old backups to clean up"
        fi
        ;;
    "prod")
        # Production-specific operations
        
        # Cleanup old hourly backups
        log_message "🗑️  Cleaning up old hourly backups..."
        DELETED_FILES=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -type f)
        if [ -n "$DELETED_FILES" ]; then
            DELETED_COUNT=$(echo "$DELETED_FILES" | wc -l)
            find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -type f -delete
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
                
                # Cleanup old weekly backups
                DELETED_WEEKLY=$(find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -mtime +$WEEKLY_RETENTION_DAYS -type f)
                if [ -n "$DELETED_WEEKLY" ]; then
                    DELETED_WEEKLY_COUNT=$(echo "$DELETED_WEEKLY" | wc -l)
                    find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -mtime +$WEEKLY_RETENTION_DAYS -type f -delete
                    log_message "🗑️  Cleaned up $DELETED_WEEKLY_COUNT old weekly backup(s)"
                fi
            else
                log_message "❌ ERROR: Failed to create weekly backup"
            fi
        fi
        ;;
esac

# Check disk space and warn if running low
DISK_USAGE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAILABLE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}')

if [ "$DISK_USAGE" -gt 90 ]; then
    log_message "🚨 CRITICAL: Disk usage is at ${DISK_USAGE}% (${DISK_AVAILABLE} available)"
    update_health_status "CRITICAL: Low disk space (${DISK_USAGE}%)"
elif [ "$DISK_USAGE" -gt 80 ]; then
    log_message "⚠️  WARNING: Disk usage is at ${DISK_USAGE}% (${DISK_AVAILABLE} available)"
    update_health_status "WARNING: High disk usage (${DISK_USAGE}%)"
else
    log_message "💾 Disk usage: ${DISK_USAGE}% (${DISK_AVAILABLE} available)"
fi

# Count current backups
if [ "$BACKUP_ENV" = "prod" ]; then
    HOURLY_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f | wc -l)
    WEEKLY_COUNT=$(find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -type f | wc -l)
    MANUAL_COUNT=$(find "$MANUAL_DIR" -name "backup_*.sql.gz" -type f | wc -l)
    log_message "📊 Backup inventory: $HOURLY_COUNT hourly, $WEEKLY_COUNT weekly, $MANUAL_COUNT manual"
else
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -type f | wc -l)
    log_message "📊 Backup inventory: $BACKUP_COUNT ${BACKUP_ENV} backups"
fi

# Rotate log file if it's too large (>10MB)
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
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