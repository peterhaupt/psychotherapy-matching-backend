# Database Schema Updates for Communication Service

This document describes the database schema changes required to implement the communication service's email batching and phone call scheduling functionality.

## Overview of Changes

The following updates to the database schema are needed:

1. **Therapist Model Updates**:
   - Add potentially available flag
   - Add field for notes about potential availability
   - Define JSON structure for telephone availability times

2. **New Tables**:
   - Phone Call table
   - Phone Call Batch table

3. **Updates to Existing Tables** (Future):
   - Add additional fields to Email table
   - Add relationship fields to Placement Request table

## Detailed Schema Changes

### 1. Therapist Table Updates

The `therapists` table requires the following new fields:

```sql
-- Add to the existing therapists table
ALTER TABLE therapist_service.therapists
ADD COLUMN potentially_available BOOLEAN DEFAULT FALSE,
ADD COLUMN potentially_available_notes TEXT;
```

The `telefonische_erreichbarkeit` field already exists as a JSONB column, but we need to establish a standard format for it:

```json
{
  "monday": [
    {"start": "09:00", "end": "12:00"},
    {"start": "14:00", "end": "16:30"}
  ],
  "wednesday": [
    {"start": "10:00", "end": "14:00"}
  ],
  "friday": [
    {"start": "08:30", "end": "11:30"}
  ]
}
```

This structure will be enforced at the application level, not the database level.

### 2. Phone Call Table

A new table for tracking scheduled and completed phone calls:

```sql
CREATE TABLE communication_service.phone_calls (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 5,
    actual_date DATE,
    actual_time TIME,
    status VARCHAR(50) DEFAULT 'scheduled',
    outcome TEXT,
    notes TEXT,
    retry_after DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_phone_calls_therapist_id ON communication_service.phone_calls(therapist_id);
CREATE INDEX idx_phone_calls_scheduled_date ON communication_service.phone_calls(scheduled_date);
CREATE INDEX idx_phone_calls_status ON communication_service.phone_calls(status);
```

### 3. Phone Call Batch Table

A table to connect phone calls to placement requests:

```sql
CREATE TABLE communication_service.phone_call_batches (
    id SERIAL PRIMARY KEY,
    phone_call_id INTEGER NOT NULL,
    placement_request_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 1,
    discussed BOOLEAN DEFAULT FALSE,
    outcome VARCHAR(50),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (phone_call_id, placement_request_id),
    FOREIGN KEY (phone_call_id) REFERENCES communication_service.phone_calls(id) ON DELETE CASCADE,
    FOREIGN KEY (placement_request_id) REFERENCES matching_service.placement_requests(id) ON DELETE CASCADE
);

CREATE INDEX idx_phone_call_batches_phone_call_id ON communication_service.phone_call_batches(phone_call_id);
CREATE INDEX idx_phone_call_batches_placement_request_id ON communication_service.phone_call_batches(placement_request_id);
```

## Migration Process

Two migration scripts have been created to implement these schema changes:

1. **6fbc92a7b7e9_add_potentially_available_fields_to_therapist.py**
   - Adds potentially_available and potentially_available_notes to the therapist table

2. **7bfc93a7c8e9_create_phone_call_tables.py**
   - Creates phone_calls and phone_call_batches tables

These migrations have been applied to the database using Alembic:

```bash
cd migrations
alembic upgrade 6fbc92a7b7e9
alembic upgrade 7bfc93a7c8e9
```

## Implementation Notes

### Phone Call Scheduling Logic

The phone call scheduling system uses the therapist's availability data to find suitable time slots:

1. The telefonische_erreichbarkeit field is parsed to extract day-based availability
2. Time slots are checked against existing scheduled calls to avoid conflicts
3. Calls are scheduled in 5-minute blocks
4. Priority is given to therapists flagged as "potentially available"

### Therapist Availability Helper Methods

The Therapist model has been extended with helper methods to make working with the availability JSON structure easier:

- `get_available_slots()`: Returns available time slots for a specific date or all slots
- `is_available_at()`: Checks if a therapist is available at a specific date and time

### Future Schema Changes

In the next phase, we will implement:

1. Email Batch table to better organize email communications
2. Updates to the Email model to track responses and follow-ups
3. Additional relationships between the email, phone call, and placement request models