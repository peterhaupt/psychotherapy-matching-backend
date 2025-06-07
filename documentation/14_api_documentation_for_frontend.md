# Frontend API Documentation

## ⚠️ IMPORTANT: System in Transition
**Current State (as of implementation)**:
- ✅ Database: All tables use German field names
- ✅ Patient Service: Models and APIs use German field names
- ❌ Therapist Service: Models still use English field names
- ✅ Communication Service: Models and APIs now use German field names
- ✅ PlacementRequest: Removed from codebase, replaced with stub bundle system
- 🟡 Matching Service: Returns 501 (Not Implemented) for all endpoints

**This documentation shows the CURRENT API state after recent updates.**

## Base URLs
- Patient Service: `http://localhost:8001`
- Therapist Service: `http://localhost:8002` 
- Matching Service: `http://localhost:8003`
- Communication Service: `http://localhost:8004`
- Geocoding Service: `http://localhost:8005`

## Pagination

All list endpoints support pagination with the following query parameters:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | - | Page number (1-based) |
| `limit` | integer | 20 | 100 | Number of items per page |

Example: `GET /api/patients?page=2&limit=50`

## Important Enums (Current Values)

### PatientStatus
```javascript
const PatientStatus = {
  OPEN: "OPEN",
  SEARCHING: "SEARCHING",
  IN_THERAPY: "IN_THERAPY",
  THERAPY_COMPLETED: "THERAPY_COMPLETED",
  SEARCH_ABORTED: "SEARCH_ABORTED",
  THERAPY_ABORTED: "THERAPY_ABORTED"
}
```

### TherapistStatus  
```javascript
const TherapistStatus = {
  ACTIVE: "ACTIVE",
  BLOCKED: "BLOCKED",
  INACTIVE: "INACTIVE"
}
```

### EmailStatus
```javascript
const EmailStatus = {
  DRAFT: "DRAFT",
  QUEUED: "QUEUED",
  SENDING: "SENDING",
  SENT: "SENT",
  FAILED: "FAILED"
}
```

### PhoneCallStatus
```javascript
const PhoneCallStatus = {
  SCHEDULED: "scheduled",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELED: "canceled"
}
```

### TherapistGenderPreference
```javascript
const TherapistGenderPreference = {
  MALE: "MALE",
  FEMALE: "FEMALE",
  ANY: "ANY"
}
```

## Patient Service API ✅ WORKING

The Patient Service uses German field names in both database and models.

### GET /api/patients
Query parameters:
- `status` (optional): Filter by patient status
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

### POST /api/patients
Required fields:
```json
{
  "vorname": "string",
  "nachname": "string"
}
```

Optional fields (all German):
```json
{
  "anrede": "string",
  "strasse": "string",
  "plz": "string",
  "ort": "string",
  "email": "string",
  "telefon": "string",
  "hausarzt": "string",
  "krankenkasse": "string",
  "krankenversicherungsnummer": "string",
  "geburtsdatum": "YYYY-MM-DD",
  "diagnose": "string",
  "vertraege_unterschrieben": boolean,
  "psychotherapeutische_sprechstunde": boolean,
  "startdatum": "YYYY-MM-DD",
  "zeitliche_verfuegbarkeit": {
    "monday": [{"start": "09:00", "end": "17:00"}],
    "tuesday": [{"start": "09:00", "end": "17:00"}]
  },
  "raeumliche_verfuegbarkeit": {
    "max_km": 30
  },
  "verkehrsmittel": "Auto|ÖPNV",
  "offen_fuer_gruppentherapie": boolean,
  "offen_fuer_diga": boolean,
  "bevorzugtes_therapeutengeschlecht": "MALE|FEMALE|ANY",
  "ausgeschlossene_therapeuten": [1, 2, 3]
}
```

## Therapist Service API (⚠️ Model/DB Mismatch)

**IMPORTANT**: The database uses German field names but the model still uses English names. The API currently returns English field names.

### GET /api/therapists
Returns therapists with ENGLISH field names (current state).

### POST /api/therapists
Currently expects ENGLISH field names:
```json
{
  "vorname": "string",
  "nachname": "string",
  "potentially_available": boolean,
  "potentially_available_notes": "string"
}
```

**Note**: Fields like `potentially_available` will fail once models are updated to match the database's `potenziell_verfuegbar`.

## Matching Service API 🟡 Returns 501 - Not Implemented

### Current State
All matching service endpoints return 501 (Not Implemented) with a message explaining the bundle system is in development.

### GET /api/placement-requests
```json
{
  "message": "Bundle system not yet implemented",
  "data": [],
  "page": 1,
  "limit": 20,
  "total": 0
}
```
Status: 501

### POST /api/placement-requests  
### GET /api/placement-requests/{id}
### PUT /api/placement-requests/{id}
### DELETE /api/placement-requests/{id}

All return:
```json
{
  "message": "Bundle system not yet implemented"
}
```
Status: 501

## Communication Service API ✅ FULLY UPDATED

**IMPORTANT**: The Communication Service now uses German field names in both requests and responses.

### Email Endpoints

#### GET /api/emails
Returns emails with GERMAN field names:
```json
{
  "id": 1,
  "therapist_id": 123,
  "betreff": "Email subject",
  "empfaenger_email": "doctor@example.com",
  "empfaenger_name": "Dr. Schmidt",
  "absender_email": "info@boona.de",
  "absender_name": "Boona Team",
  "status": "SENT",
  "antwort_erhalten": false,
  "antwortdatum": null
}
```

#### POST /api/emails
Expects GERMAN field names:
```json
{
  "therapist_id": 123,
  "betreff": "Therapieanfrage",
  "body_html": "<html>...</html>",
  "body_text": "Plain text content",
  "empfaenger_email": "doctor@example.com",
  "empfaenger_name": "Dr. Schmidt"
}
```

Optional fields:
- `absender_email` (defaults to config EMAIL_SENDER)
- `absender_name` (defaults to config EMAIL_SENDER_NAME)

### Phone Call Endpoints

#### GET /api/phone-calls
Returns calls with GERMAN field names:
```json
{
  "id": 1,
  "therapist_id": 123,
  "geplantes_datum": "2025-06-10",
  "geplante_zeit": "14:30",
  "dauer_minuten": 5,
  "status": "scheduled"
}
```

#### POST /api/phone-calls
Expects GERMAN field names:
```json
{
  "therapist_id": 123,
  "geplantes_datum": "2025-06-10",
  "geplante_zeit": "14:30",
  "dauer_minuten": 5
}
```

Optional: If `geplantes_datum` and `geplante_zeit` are not provided, the system will automatically find the next available slot.

#### PUT /api/phone-calls/{id}
Update with GERMAN field names:
```json
{
  "tatsaechliches_datum": "2025-06-10",
  "tatsaechliche_zeit": "14:35",
  "status": "completed",
  "ergebnis": "Therapist interested in 2 patients",
  "notizen": "Follow-up email sent"
}
```

## Geocoding Service API ✅ WORKING

The Geocoding Service is unaffected by the German field name changes as it uses technical/English field names.

### GET /api/geocode
### GET /api/reverse-geocode  
### GET /api/calculate-distance
### POST /api/find-therapists

(Same as before - see original documentation)

## Common Error Responses

### Standard Error Formats

#### 400 Bad Request
```json
{
  "message": "Description of what went wrong"
}
```

#### 404 Not Found
```json
{
  "message": "Resource not found"
}
```

#### 501 Not Implemented (Matching Service)
```json
{
  "message": "Bundle system not yet implemented"
}
```

### Current Issues You May Encounter

#### 500 Internal Server Error - Database/Model Mismatch
```json
{
  "message": "Database error: (psycopg2.errors.UndefinedColumn) column \"potentially_available\" does not exist"
}
```
This occurs when models haven't been updated to match database field names.
**Note**: This should NOT occur in Communication Service anymore.

## Migration in Progress - What's Working

### Currently Working ✅
- Patient Service (fully migrated to German)
- Communication Service (fully migrated to German)
- Geocoding Service (unaffected)
- Basic GET operations on existing data
- Matching Service (returns 501 instead of crashing)

### Currently Broken ❌
- Creating new therapists with bundle preferences
- Any operation involving new therapist fields

### Partially Working ⚠️
- Therapist Service (reads work, writes may fail on new fields)

## Updated Field Name References

### Communication Service Fields (NOW IN USE) ✅
#### Email Fields:
- `subject` → `betreff` ✅
- `recipient_email` → `empfaenger_email` ✅
- `recipient_name` → `empfaenger_name` ✅
- `sender_email` → `absender_email` ✅
- `sender_name` → `absender_name` ✅
- `response_received` → `antwort_erhalten` ✅
- `response_date` → `antwortdatum` ✅
- `response_content` → `antwortinhalt` ✅
- `follow_up_required` → `nachverfolgung_erforderlich` ✅
- `follow_up_notes` → `nachverfolgung_notizen` ✅

#### Phone Call Fields:
- `scheduled_date` → `geplantes_datum` ✅
- `scheduled_time` → `geplante_zeit` ✅
- `duration_minutes` → `dauer_minuten` ✅
- `actual_date` → `tatsaechliches_datum` ✅
- `actual_time` → `tatsaechliche_zeit` ✅
- `outcome` → `ergebnis` ✅
- `notes` → `notizen` ✅
- `retry_after` → `wiederholen_nach` ✅

### Therapist Fields (PENDING UPDATE):
- `potentially_available` → `potenziell_verfuegbar` (pending)
- `potentially_available_notes` → `potenziell_verfuegbar_notizen` (pending)
- `next_contactable_date` → `naechster_kontakt_moeglich` (pending)
- (etc. - see documentation)

## Next Steps

The development team is working on:
1. ✅ PlacementRequest code removed (COMPLETE)
2. ✅ Communication models updated to German (COMPLETE)
3. 🔄 Updating therapist model to use German field names
4. 🔄 Implementing full bundle system (currently returns 501)
5. 🔄 Updating this documentation once all models are fixed

**Check back for updates or monitor the git repository for changes.**