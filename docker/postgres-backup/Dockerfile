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

# Copy backup scripts
COPY docker/postgres-backup/backup-script.sh /usr/local/bin/backup-script.sh
COPY docker/postgres-backup/backup-watchdog.sh /usr/local/bin/backup-watchdog.sh
COPY docker/postgres-backup/entrypoint.sh /usr/local/bin/entrypoint.sh

# Make scripts executable and set ownership
RUN chmod +x /usr/local/bin/backup-script.sh \
             /usr/local/bin/backup-watchdog.sh \
             /usr/local/bin/entrypoint.sh \
             /usr/local/bin/health-check.sh \
             /usr/local/bin/http-server.sh && \
    chown backup:backup /usr/local/bin/backup-script.sh \
                        /usr/local/bin/backup-watchdog.sh \
                        /usr/local/bin/health-check.sh \
                        /usr/local/bin/http-server.sh

# Create health check script
RUN echo '#!/bin/bash' > /usr/local/bin/health-check.sh && \
    echo 'if [ -f /tmp/health/status ]; then' >> /usr/local/bin/health-check.sh && \
    echo '  cat /tmp/health/status' >> /usr/local/bin/health-check.sh && \
    echo '  exit 0' >> /usr/local/bin/health-check.sh && \
    echo 'else' >> /usr/local/bin/health-check.sh && \
    echo '  echo "Service starting..."' >> /usr/local/bin/health-check.sh && \
    echo '  exit 1' >> /usr/local/bin/health-check.sh && \
    echo 'fi' >> /usr/local/bin/health-check.sh

# Create simple HTTP server for health checks
RUN echo '#!/bin/bash' > /usr/local/bin/http-server.sh && \
    echo 'while true; do' >> /usr/local/bin/http-server.sh && \
    echo '  response="HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n$(/usr/local/bin/health-check.sh)"' >> /usr/local/bin/http-server.sh && \
    echo '  echo -e "$response" | nc -l -p 8080' >> /usr/local/bin/http-server.sh && \
    echo 'done' >> /usr/local/bin/http-server.sh

# Set working directory
WORKDIR /backups

# Expose health check port
EXPOSE 8080

# Set entrypoint (will run as root, but backup operations run as backup user)
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]