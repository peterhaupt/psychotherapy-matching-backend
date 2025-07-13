FROM postgres:16-alpine

# Install cron and bash
RUN apk add --no-cache dcron bash

# Create backup directory
RUN mkdir -p /backups/postgres/hourly /backups/postgres/weekly

# Copy backup scripts
COPY backup-cron.sh /usr/local/bin/backup-cron.sh
COPY backup-watchdog.sh /usr/local/bin/backup-watchdog.sh
RUN chmod +x /usr/local/bin/backup-cron.sh
RUN chmod +x /usr/local/bin/backup-watchdog.sh

# Add cron job for hourly backups
RUN echo "0 * * * * /usr/local/bin/backup-cron.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/postgres

# Create custom entrypoint to start postgres, cron, and watchdog
RUN echo '#!/bin/bash' > /custom-entrypoint.sh && \
    echo 'echo "🚀 Starting Curavani Postgres with backup system..."' >> /custom-entrypoint.sh && \
    echo '' >> /custom-entrypoint.sh && \
    echo '# Start cron daemon' >> /custom-entrypoint.sh && \
    echo 'echo "⏰ Starting cron daemon..."' >> /custom-entrypoint.sh && \
    echo 'crond -b' >> /custom-entrypoint.sh && \
    echo '' >> /custom-entrypoint.sh && \
    echo '# Start backup watchdog in background' >> /custom-entrypoint.sh && \
    echo 'echo "🐕 Starting backup watchdog..."' >> /custom-entrypoint.sh && \
    echo '/usr/local/bin/backup-watchdog.sh &' >> /custom-entrypoint.sh && \
    echo '' >> /custom-entrypoint.sh && \
    echo '# Start PostgreSQL (this will run in foreground)' >> /custom-entrypoint.sh && \
    echo 'echo "🗄️  Starting PostgreSQL..."' >> /custom-entrypoint.sh && \
    echo 'exec docker-entrypoint.sh postgres' >> /custom-entrypoint.sh && \
    chmod +x /custom-entrypoint.sh

# Override entrypoint
ENTRYPOINT ["/custom-entrypoint.sh"]