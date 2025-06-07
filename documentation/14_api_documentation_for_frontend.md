# Frontend API Documentation

## ⚠️ IMPORTANT: System in Transition
**Current State (as of implementation)**:
- ✅ Database: All tables use German field names
- ❌ Models: Still use English field names (causing mismatches) - EXCEPT Matching Service
- ❌ APIs: Still return English field names - EXCEPT Matching Service
- ✅ PlacementRequest: Removed from codebase, replaced with stub bundle system
- 🟡 Matching Service: Returns 501 (Not Implemented) for all endpoints

**This documentation shows the CURRENT API state, not the target state.**

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

## Patient Service API

The Patient Service already uses German field names in both database and models.

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

## Matching Service API (🟡 Returns 501 - Not Implemented)

### Current State
All matching service endpoints return 501 (Not Implemented) with a message explaining the bundle system is in development. No database errors or crashes occur.

**All endpoints return proper error responses**:

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

### New Bundle System Endpoints (Planned - Not Yet Available)
The following endpoints are planned but not yet implemented:
- 🔄 POST /api/platzsuchen
- 🔄 GET /api/platzsuchen/{id}
- 🔄 POST /api/therapeutenanfragen
- 🔄 PUT /api/therapeutenanfragen/{id}/antwort

## Communication Service API (⚠️ Model/DB Mismatch)

**IMPORTANT**: The database uses German field names but models still use English names.

### Email Endpoints

#### GET /api/emails
Currently returns emails with ENGLISH field names:
```json
{
  "id": 1,
  "therapist_id": 123,
  "subject": "Email subject",
  "recipient_email": "doctor@example.com",
  "recipient_name": "Dr. Smith",
  "sender_email": "info@boona.de",
  "sender_name": "Boona Team",
  "status": "SENT",
  "response_received": false,
  "response_date": null
}
```

#### POST /api/emails
Currently expects ENGLISH field names:
```json
{
  "therapist_id": 123,
  "subject": "Therapieanfrage",
  "body_html": "<html>...</html>",
  "recipient_email": "doctor@example.com",
  "recipient_name": "Dr. Smith"
}
```

### Phone Call Endpoints

#### GET /api/phone-calls
Currently returns calls with ENGLISH field names:
```json
{
  "id": 1,
  "therapist_id": 123,
  "scheduled_date": "2025-06-10",
  "scheduled_time": "14:30",
  "duration_minutes": 5,
  "status": "scheduled"
}
```

#### POST /api/phone-calls
Currently expects ENGLISH field names:
```json
{
  "therapist_id": 123,
  "scheduled_date": "2025-06-10",
  "scheduled_time": "14:30"
}
```

## Geocoding Service API

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
**Note**: This does NOT occur in the Matching Service anymore.

## Migration in Progress - What's Working

### Currently Working ✅
- Patient Service (fully migrated to German)
- Geocoding Service (unaffected)
- Basic GET operations on existing data
- **Matching Service** (returns 501 instead of crashing)

### Currently Broken ❌
- Creating new therapists with bundle preferences
- Creating emails/calls with batch references
- Any operation involving removed batch tables

### Partially Working ⚠️
- Therapist Service (reads work, writes may fail on new fields)
- Communication Service (basic operations work, batch operations fail)

## Temporary Workarounds

### For Frontend Development
1. **Use Patient Service** as reference for German field implementation
2. **Matching Service** now safe to call - returns 501 status
3. **Test carefully** - some operations may work in GET but fail in POST/PUT
4. **Check logs** - database errors will show exact field name mismatches

### Field Name References

When models are updated, these mappings will apply:

#### Therapist Fields:
- `potentially_available` → `potenziell_verfuegbar`
- `potentially_available_notes` → `potenziell_verfuegbar_notizen`
- `next_contactable_date` → `naechster_kontakt_moeglich`
- (etc. - see documentation)

#### Communication Fields:
- `subject` → `betreff`
- `recipient_email` → `empfaenger_email`
- `scheduled_date` → `geplantes_datum`
- (etc. - see documentation)

## Next Steps

The development team is working on:
1. ✅ PlacementRequest code removed (COMPLETE)
2. 🔄 Updating therapist model to use German field names
3. 🔄 Updating communication models to use German field names  
4. 🔄 Implementing full bundle system (currently returns 501)
5. 🔄 Updating this documentation once models are fixed

**Check back for updates or monitor the git repository for changes.**