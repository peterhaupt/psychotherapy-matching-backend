# Required Changes to Existing Implementation

This document outlines specific changes needed to the current codebase based on our revised requirements for the Communication Service. These changes focus on adapting the existing implementation to support email batching and phone call scheduling.

## 1. Changes to Therapist Service

### Therapist Model (`therapist_service/models/therapist.py`)

**Current Implementation**: 
- The Therapist model has a `telefonische_erreichbarkeit` field as a JSONB column but without a specified format.
- Model lacks fields for tracking potential availability.

**Required Changes**:
1. Add new fields to the Therapist model:
   ```python
   # Add to the existing Therapist model
   potentially_available = Column(Boolean, default=False)
   potentially_available_notes = Column(Text)
   ```

2. Add helper methods to parse the `telefonische_erreichbarkeit` JSONB field:
   ```python
   def get_available_slots(self, date=None):
       """Get available time slots for a given date."""
       # Implementation to parse JSON structure
       
   def is_available_at(self, date, time):
       """Check if therapist is available at a specific date and time."""
       # Implementation to check availability
   ```

3. Create a migration script to add these fields to the database.

## 2. Changes to Communication Service

### Email Model (`communication_service/models/email.py`)

**Current Implementation**:
- Email model tracks individual emails
- Uses `placement_request_ids` as a JSONB field to associate emails with requests

**Required Changes**:
1. Add new fields to the Email model:
   ```python
   # Add to existing Email model
   batch_id = Column(String(50))
   response_received = Column(Boolean, default=False)
   response_date = Column(DateTime)
   response_content = Column(Text)
   follow_up_required = Column(Boolean, default=False)
   follow_up_notes = Column(Text)
   ```

2. Replace JSONB `placement_request_ids` with a proper relationship.

3. Create an EmailBatch model and table to properly track email batches.

### Email Sending Logic (`communication_service/utils/email_sender.py`)

**Current Implementation**:
- `send_email` function sends individual emails
- `send_queued_emails` processes emails from the queue

**Required Changes**:
1. Enhance `send_queued_emails` to implement batching logic
2. Add functions to check therapist contact frequency
3. Implement batch email generation

## 3. New Components to Add

### Phone Call System

**Current Implementation**:
- No existing phone call functionality

**Required Additions**:
1. Create PhoneCall model
2. Create PhoneCallBatch model
3. Implement phone call scheduling algorithm
4. Implement rescheduling logic for failed calls

## 4. Kafka Event Handlers

### Event Consumers (`communication_service/events/consumers.py`)

**Current Implementation**:
- Basic structure for handling `match.created` events
- No handling for scheduling follow-up communications

**Required Changes**:
1. Enhance `handle_matching_event` to track email responses
2. Add scheduled task for processing emails without responses
3. Add scheduled task for executing batching

## 5. API Changes

### API Endpoints (`communication_service/api/emails.py`)

**Current Implementation**:
- Basic CRUD endpoints for emails

**Required Changes**:
1. Add endpoints for tracking email responses
2. Add endpoints for managing phone calls

## 6. Database Migration

A comprehensive migration script needs to be created (as outlined in `database_schema_updates.md`) to:

1. Add the new fields to the Therapist model
2. Create the phone_calls and phone_call_batches tables
3. Create the email_batches table 
4. Add new fields to the emails table
5. Set up appropriate relationships and constraints

## Implementation Strategy

The recommended implementation strategy is:

1. First, update the database schema through migrations
2. Update the Therapist model to include potential availability fields
3. Create the new models for phone calls and batching
4. Implement the email batching system
5. Implement the phone call scheduling algorithm
6. Add the new API endpoints
7. Enhance the Kafka event handlers

This approach ensures that the database structure is in place before updating the application logic, minimizing the risk of runtime errors.