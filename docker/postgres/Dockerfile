FROM postgres:16-alpine

# Install cron and bash
RUN apk add --no-cache dcron bash

# Create backup directory
RUN mkdir -p /backups/postgres/hourly /backups/postgres/weekly

# Copy backup script
COPY backup-cron.sh /usr/local/bin/backup-cron.sh
RUN chmod +x /usr/local/bin/backup-cron.sh

# Add cron job for hourly backups
RUN echo "0 * * * * /usr/local/bin/backup-cron.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/postgres

# Create custom entrypoint to start both postgres and cron
RUN echo '#!/bin/bash' > /custom-entrypoint.sh && \
    echo 'crond -b' >> /custom-entrypoint.sh && \
    echo 'exec docker-entrypoint.sh postgres' >> /custom-entrypoint.sh && \
    chmod +x /custom-entrypoint.sh

# Override entrypoint
ENTRYPOINT ["/custom-entrypoint.sh"]