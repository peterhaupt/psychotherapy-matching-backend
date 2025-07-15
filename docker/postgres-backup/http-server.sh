#!/bin/bash
# Simple HTTP server for health check endpoint
# Serves the backup service status on port 8080

while true; do
    # Get the health status
    if [ -f /tmp/health/status ]; then
        STATUS=$(cat /tmp/health/status)
        HTTP_CODE="200 OK"
    else
        STATUS="Service starting..."
        HTTP_CODE="503 Service Unavailable"
    fi
    
    # Create the HTTP response
    RESPONSE="HTTP/1.1 $HTTP_CODE\r\nContent-Type: text/plain\r\nContent-Length: ${#STATUS}\r\nConnection: close\r\n\r\n$STATUS"
    
    # Serve the response using netcat
    echo -e "$RESPONSE" | nc -l -p 8080
done