# Frontend API Documentation

## ✅ SYSTEM UPDATE COMPLETE
**Current State (as of latest implementation)**:
- ✅ Database: All tables use German field names
- ✅ Patient Service: Models and APIs use German field names
- ✅ Therapist Service: Models and APIs use German field names
- ✅ Communication Service: Models and APIs use German field names
- ✅ PlacementRequest: Removed from codebase, replaced with stub bundle system
- 🟡 Matching Service: Returns 501 (Not Implemented) for all endpoints

**This documentation shows the CURRENT API state with all services fully updated.**

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
  ACTIVE: "aktiv",
  BLOCKED: "gesperrt",
  INACTIVE: "inaktiv"
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

## Therapist Service API ✅ WORKING

The Therapist Service uses German field names in database, models, and API.

### GET /api/therapists
Returns therapists with GERMAN field names.

Query parameters:
- `status` (optional): Filter by therapist status ("aktiv", "gesperrt", "inaktiv")
- `potenziell_verfuegbar` (optional): Filter by availability (boolean)
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

Response example:
```json
{
  "id": 1,
  "vorname": "Max",
  "nachname": "Mustermann",
  "potenziell_verfuegbar": true,
  "potenziell_verfuegbar_notizen": "Ab nächstem Monat",
  "naechster_kontakt_moeglich": "2025-06-15",
  "bevorzugte_diagnosen": ["F32", "F41"],
  "alter_min": 18,
  "alter_max": 65,
  "geschlechtspraeferenz": "Egal",
  "arbeitszeiten": {
    "monday": [{"start": "09:00", "end": "17:00"}]
  },
  "bevorzugt_gruppentherapie": false,
  "status": "aktiv"
}
```

### POST /api/therapists
Expects GERMAN field names:
```json
{
  "vorname": "string",
  "nachname": "string",
  "potenziell_verfuegbar": boolean,
  "potenziell_verfuegbar_notizen": "string",
  "naechster_kontakt_moeglich": "YYYY-MM-DD",
  "bevorzugte_diagnosen": ["F32", "F41"],
  "alter_min": 18,
  "alter_max": 65,
  "geschlechtspraeferenz": "Male|Female|Egal",
  "arbeitszeiten": {
    "monday": [{"start": "09:00", "end": "12:00"}]
  },
  "bevorzugt_gruppentherapie": boolean
}
```

### PUT /api/therapists/{id}
Same fields as POST, all fields are optional.

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

## Communication Service API ✅ FULLY WORKING

The Communication Service uses German field names in both requests and responses.

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
  "antwortdatum": null,
  "antwortinhalt": null,
  "nachverfolgung_erforderlich": false,
  "sent_at": "2025-06-08T10:30:00"
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

#### PUT /api/emails/{id}
Update email with GERMAN field names:
```json
{
  "antwort_erhalten": true,
  "antwortdatum": "2025-06-09T14:00:00",
  "antwortinhalt": "Ich kann 2 Patienten aufnehmen.",
  "nachverfolgung_erforderlich": false
}
```

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
  "status": "scheduled",
  "tatsaechliches_datum": null,
  "tatsaechliche_zeit": null,
  "ergebnis": null,
  "notizen": null
}
```

#### POST /api/phone-calls
Expects GERMAN field names:
```json
{
  "therapist_id": 123,
  "geplantes_datum": "2025-06-10",
  "geplante_zeit": "14:30",
  "dauer_minuten": 5,
  "notizen": "Follow-up für Bündel #456"
}
```

Optional: If `geplantes_datum` and `geplante_zeit` are not provided, the system will automatically find the next available slot based on therapist's `telefonische_erreichbarkeit`.

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

The Geocoding Service uses technical/English field names (unchanged).

### GET /api/geocode
Query parameters:
- `address` (required): Address to geocode

Response:
```json
{
  "latitude": 52.5200,
  "longitude": 13.4050,
  "display_name": "Berlin, Germany"
}
```

### GET /api/reverse-geocode  
Query parameters:
- `lat` (required): Latitude
- `lon` (required): Longitude

### GET /api/calculate-distance
Query parameters:
- `origin`: Address or coordinates (origin_lat, origin_lon)
- `destination`: Address or coordinates (destination_lat, destination_lon)
- `travel_mode`: "car" or "transit" (default: "car")
- `no_cache`: Bypass cache (default: false)

Response:
```json
{
  "distance_km": 123.45,
  "travel_time_minutes": 67.8
}
```

### POST /api/find-therapists
Request body:
```json
{
  "patient_address": "Berlin, Germany",
  "max_distance_km": 30,
  "travel_mode": "car",
  "therapists": [
    {
      "id": 1,
      "strasse": "Example Street 1",
      "plz": "10115",
      "ort": "Berlin"
    }
  ]
}
```

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

#### 500 Internal Server Error
```json
{
  "message": "Database error: [details]"
}
```

#### 501 Not Implemented (Matching Service)
```json
{
  "message": "Bundle system not yet implemented"
}
```

## Migration Complete - Everything Working ✅

### Currently Working
- ✅ Patient Service (fully migrated to German)
- ✅ Therapist Service (fully migrated to German)
- ✅ Communication Service (fully migrated to German)
- ✅ Geocoding Service (unaffected)
- ✅ Matching Service (returns 501 instead of crashing)

### Field Name Reference (All Services Now Using German)

#### Patient Fields:
All fields as documented above use German names.

#### Therapist Fields:
- `potentially_available` → `potenziell_verfuegbar` ✅
- `potentially_available_notes` → `potenziell_verfuegbar_notizen` ✅
- `next_contactable_date` → `naechster_kontakt_moeglich` ✅
- `preferred_diagnoses` → `bevorzugte_diagnosen` ✅
- `age_min` → `alter_min` ✅
- `age_max` → `alter_max` ✅
- `gender_preference` → `geschlechtspraeferenz` ✅
- `working_hours` → `arbeitszeiten` ✅
- `prefers_group_therapy` → `bevorzugt_gruppentherapie` ✅

#### Communication Fields:
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
- `scheduled_date` → `geplantes_datum` ✅
- `scheduled_time` → `geplante_zeit` ✅
- `duration_minutes` → `dauer_minuten` ✅
- `actual_date` → `tatsaechliches_datum` ✅
- `actual_time` → `tatsaechliche_zeit` ✅
- `outcome` → `ergebnis` ✅
- `notes` → `notizen` ✅
- `retry_after` → `wiederholen_nach` ✅

## Testing the APIs

### Test Patient Service
```bash
# Get all patients
curl http://localhost:8001/api/patients

# Create a patient
curl -X POST http://localhost:8001/api/patients \
  -H "Content-Type: application/json" \
  -d '{"vorname": "Test", "nachname": "Patient"}'
```

### Test Therapist Service
```bash
# Get all therapists
curl http://localhost:8002/api/therapists

# Create a therapist with bundle preferences
curl -X POST http://localhost:8002/api/therapists \
  -H "Content-Type: application/json" \
  -d '{
    "vorname": "Test",
    "nachname": "Therapist",
    "potenziell_verfuegbar": true,
    "bevorzugte_diagnosen": ["F32", "F41"],
    "alter_min": 18,
    "alter_max": 65
  }'
```

### Test Communication Service
```bash
# Get all emails
curl http://localhost:8004/api/emails

# Create an email
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 1,
    "betreff": "Test Email",
    "body_html": "<p>Test</p>",
    "body_text": "Test",
    "empfaenger_email": "test@example.com",
    "empfaenger_name": "Test Therapist"
  }'
```

## Next Steps

The development team is working on:
1. ✅ Database migration to German (COMPLETE)
2. ✅ All service models updated to German (COMPLETE)
3. ✅ All APIs using German field names (COMPLETE)
4. 🔄 Implementing full bundle system (in progress)

**All field name updates are complete. Frontend can now use German field names for all services.**