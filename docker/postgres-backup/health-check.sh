#!/bin/bash
# Health check script for postgres-backup service
# Returns the current backup service status

if [ -f /tmp/health/status ]; then
    cat /tmp/health/status
    exit 0
else
    echo "Service starting..."
    exit 1
fi