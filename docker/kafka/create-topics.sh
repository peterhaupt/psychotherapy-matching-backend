#!/bin/bash
# Script to create required Kafka topics

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
kafka-topics --bootstrap-server kafka:9092 --list
until [ $? -eq 0 ]; do
  sleep 5
  kafka-topics --bootstrap-server kafka:9092 --list
done

# Create topics with appropriate configurations
echo "Creating Kafka topics..."

# Event topics
kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic patient-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic therapist-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic matching-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic communication-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic geocoding-events --partitions 3 --replication-factor 1

# Command topics
kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic email-commands --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic geocoding-requests --partitions 3 --replication-factor 1

echo "Kafka topics created:"
kafka-topics --bootstrap-server kafka:9092 --list