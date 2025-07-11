#!/bin/bash
# Hourly backup script for Curavani production database
# Add to cron: 0 * * * * /path/to/curavani_backend/scripts/backup-hourly.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f ".env.prod" ]; then
    source .env.prod
else
    echo "Error: .env.prod not found"
    exit 1
fi

BACKUP_DIR="./backups/postgres/hourly"
WEEKLY_DIR="./backups/postgres/weekly"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="./backups/backup.log"

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$WEEKLY_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start backup process
log_message "Starting hourly backup..."

# Check if production postgres is running
if docker ps | grep -q postgres-prod; then
    # Create backup
    if docker exec postgres-prod pg_dump -U ${DB_USER} ${DB_NAME} | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"; then
        # Get backup size
        BACKUP_SIZE=$(du -h "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz" | cut -f1)
        log_message "✅ Backup created successfully: backup_$TIMESTAMP.sql.gz (Size: $BACKUP_SIZE)"
        
        # Keep only last 7 days of hourly backups (168 hours)
        find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
        DELETED_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 | wc -l)
        if [ $DELETED_COUNT -gt 0 ]; then
            log_message "🗑️  Cleaned up $DELETED_COUNT old hourly backups"
        fi
        
        # Create weekly backup on Sundays at midnight hour
        if [ $(date +%w) -eq 0 ] && [ $(date +%H) -eq 00 ]; then
            cp "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz" "$WEEKLY_DIR/weekly_backup_$(date +%Y%m%d).sql.gz"
            log_message "📅 Created weekly backup: weekly_backup_$(date +%Y%m%d).sql.gz"
            
            # Keep weekly backups for 3 months (90 days)
            find "$WEEKLY_DIR" -name "weekly_backup_*.sql.gz" -mtime +90 -delete
        fi
        
        # Check disk space
        DISK_USAGE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
        if [ $DISK_USAGE -gt 80 ]; then
            log_message "⚠️  WARNING: Disk usage is at ${DISK_USAGE}%"
        fi
        
    else
        log_message "❌ ERROR: Backup failed!"
        exit 1
    fi
else
    log_message "⚠️  WARNING: postgres-prod container is not running, skipping backup"
fi

# Rotate log file if it's too large (>10MB)
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
    if [ $LOG_SIZE -gt 10485760 ]; then
        mv "$LOG_FILE" "$LOG_FILE.old"
        log_message "Log file rotated"
    fi
fi