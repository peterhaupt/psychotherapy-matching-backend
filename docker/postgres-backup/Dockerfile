FROM alpine:3.18

# Install required packages
RUN apk add --no-cache \
    bash \
    dcron \
    postgresql-client \
    curl \
    bc \
    findutils \
    coreutils \
    netcat-openbsd

# Create backup user
RUN adduser -D -s /bin/bash backup

# Create backup directories
RUN mkdir -p /backups/postgres/dev \
             /backups/postgres/test \
             /backups/postgres/manual \
             /backups/postgres/hourly \
             /backups/postgres/weekly \
             /var/log \
             /var/run \
             /tmp/health

# Set proper permissions
RUN chown -R backup:backup /backups /var/log /var/run /tmp/health

# Copy all backup scripts
COPY docker/postgres-backup/backup-script.sh /usr/local/bin/backup-script.sh
COPY docker/postgres-backup/backup-watchdog.sh /usr/local/bin/backup-watchdog.sh
COPY docker/postgres-backup/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/postgres-backup/health-check.sh /usr/local/bin/health-check.sh
COPY docker/postgres-backup/http-server.sh /usr/local/bin/http-server.sh

# Make all scripts executable and set ownership
RUN chmod +x /usr/local/bin/*.sh && \
    chown backup:backup /usr/local/bin/backup-script.sh \
                        /usr/local/bin/backup-watchdog.sh \
                        /usr/local/bin/health-check.sh \
                        /usr/local/bin/http-server.sh

# Set working directory
WORKDIR /backups

# Expose health check port
EXPOSE 8080

# Set entrypoint (will run as root, but backup operations run as backup user)
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]