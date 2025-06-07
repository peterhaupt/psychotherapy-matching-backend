# Frontend API Documentation (Updated for German Field Names)

## ⚠️ IMPORTANT: Database Schema Update in Progress
The system is transitioning to German field names throughout. This documentation reflects the TARGET state after model updates are complete.

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

## Important Enums (Use these exact values in API calls)

### PatientStatus
```javascript
const PatientStatus = {
  OPEN: "offen",
  SEARCHING: "auf der Suche",
  IN_THERAPY: "in Therapie",
  THERAPY_COMPLETED: "Therapie abgeschlossen",
  SEARCH_ABORTED: "Suche abgebrochen",
  THERAPY_ABORTED: "Therapie abgebrochen"
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
  MALE: "Männlich",
  FEMALE: "Weiblich",
  ANY: "Egal"
}
```

## Patient Service API

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

Optional fields:
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
  "bevorzugtes_therapeutengeschlecht": "Männlich|Weiblich|Egal",
  "ausgeschlossene_therapeuten": [1, 2, 3]
}
```

### GET /api/patients/{id}
Returns patient object

### PUT /api/patients/{id}
Same fields as POST (all optional)

### DELETE /api/patients/{id}
No body required

## Therapist Service API (with German field names)

### GET /api/therapists
Query parameters:
- `status` (optional): Filter by therapist status
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

### POST /api/therapists
Required fields:
```json
{
  "vorname": "string",
  "nachname": "string"
}
```

Optional fields:
```json
{
  "anrede": "string",
  "titel": "string",
  "strasse": "string",
  "plz": "string",
  "ort": "string",
  "telefon": "string",
  "fax": "string",
  "email": "string",
  "webseite": "string",
  "kassensitz": boolean,
  "geschlecht": "string",
  "telefonische_erreichbarkeit": {
    "monday": [{"start": "09:00", "end": "12:00"}],
    "wednesday": [{"start": "14:00", "end": "18:00"}]
  },
  "fremdsprachen": ["Englisch", "Französisch"],
  "psychotherapieverfahren": ["Verhaltenstherapie"],
  "zusatzqualifikationen": "string",
  "besondere_leistungsangebote": "string",
  "potenziell_verfuegbar": boolean,
  "potenziell_verfuegbar_notizen": "string",
  "naechster_kontakt_moeglich": "YYYY-MM-DD",
  "bevorzugte_diagnosen": ["F32", "F33"],
  "alter_min": integer,
  "alter_max": integer,
  "geschlechtspraeferenz": "Männlich|Weiblich|Egal",
  "arbeitszeiten": {
    "monday": [{"start": "09:00", "end": "17:00"}]
  },
  "bevorzugt_gruppentherapie": boolean
}
```

### GET /api/therapists/{id}
Returns therapist object

### PUT /api/therapists/{id}
Same fields as POST (all optional)

### DELETE /api/therapists/{id}
No body required

## Matching Service API (Bundle System)

### ⚠️ PlacementRequest endpoints are REMOVED
The old `/api/placement-requests` endpoints no longer exist.

### New Bundle System Endpoints (Coming Soon)

#### POST /api/platzsuchen
Create a new patient search:
```json
{
  "patient_id": integer,
  "notizen": "string"
}
```

#### GET /api/platzsuchen/{id}
Returns patient search details with bundle history

#### POST /api/therapeutenanfragen
Create a new therapist inquiry (bundle):
```json
{
  "therapist_id": integer,
  "patient_ids": [1, 2, 3, 4, 5],
  "notizen": "string"
}
```

#### PUT /api/therapeutenanfragen/{id}/antwort
Record therapist response:
```json
{
  "antworttyp": "vollstaendig_angenommen|teilweise_angenommen|abgelehnt",
  "angenommene_patienten": [1, 3],
  "abgelehnte_patienten": [2, 4, 5],
  "notizen": "string"
}
```

## Communication Service API (with German field names)

### Email Endpoints

#### GET /api/emails
Query parameters:
- `therapist_id` (optional): Filter by therapist
- `status` (optional): Filter by status
- `antwort_erhalten` (optional): Filter by response status
- `batch_id` (optional): Filter by batch ID
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

#### POST /api/emails
Required fields:
```json
{
  "therapist_id": integer,
  "betreff": "string",
  "body_html": "string",
  "empfaenger_email": "string",
  "empfaenger_name": "string"
}
```

Optional fields:
```json
{
  "body_text": "string",
  "absender_email": "string",
  "absender_name": "string",
  "status": "DRAFT|QUEUED|SENDING|SENT|FAILED",
  "therapeut_anfrage_patient_ids": [1, 2, 3],
  "batch_id": "string"
}
```

#### GET /api/emails/{id}
Returns email object

#### PUT /api/emails/{id}
Optional fields:
```json
{
  "status": "DRAFT|QUEUED|SENDING|SENT|FAILED",
  "antwort_erhalten": boolean,
  "antwortdatum": "YYYY-MM-DD",
  "antwortinhalt": "string",
  "nachverfolgung_erforderlich": boolean,
  "nachverfolgung_notizen": "string"
}
```

### Phone Call Endpoints (with German field names)

#### GET /api/phone-calls
Query parameters:
- `therapist_id` (optional): Filter by therapist
- `status` (optional): Filter by status
- `geplantes_datum` (optional): Filter by scheduled date
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

#### POST /api/phone-calls
Required fields:
```json
{
  "therapist_id": integer
}
```

Optional fields:
```json
{
  "geplantes_datum": "YYYY-MM-DD",
  "geplante_zeit": "HH:MM",
  "dauer_minuten": integer,
  "status": "scheduled|completed|failed|canceled",
  "notizen": "string",
  "therapeut_anfrage_patient_ids": [1, 2, 3]
}
```

Note: If `geplantes_datum` and `geplante_zeit` are not provided, the system will automatically find the next available slot based on the therapist's availability.

#### GET /api/phone-calls/{id}
Returns phone call object

#### PUT /api/phone-calls/{id}
Optional fields:
```json
{
  "geplantes_datum": "YYYY-MM-DD",
  "geplante_zeit": "HH:MM",
  "dauer_minuten": integer,
  "tatsaechliches_datum": "YYYY-MM-DD",
  "tatsaechliche_zeit": "HH:MM",
  "status": "scheduled|completed|failed|canceled",
  "ergebnis": "string",
  "notizen": "string",
  "wiederholen_nach": "YYYY-MM-DD"
}
```

#### DELETE /api/phone-calls/{id}
No body required

## Geocoding Service API (No Changes)

The Geocoding Service API remains unchanged as it uses technical/English field names.

### GET /api/geocode
### GET /api/reverse-geocode
### GET /api/calculate-distance
### POST /api/find-therapists

(Same as before - see original documentation)

## Common Error Responses

All endpoints may return these error formats:

### 400 Bad Request
```json
{
  "message": "Description of what went wrong"
}
```

### 404 Not Found
```json
{
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "message": "Database error: specific error message"
}
```

## Important Notes for Frontend Development

1. **Field Name Changes**: Many fields have been renamed to German. Update your frontend accordingly.
2. **PlacementRequest Removal**: All placement request endpoints are removed. Use the new bundle system.
3. **Date Format**: Always use ISO format `YYYY-MM-DD` for dates
4. **Time Format**: Always use 24-hour format `HH:MM` for times
5. **Boolean Values**: Use JavaScript `true`/`false` (not strings)
6. **Enum Values**: Always use the exact string values shown above
7. **Optional Fields**: Fields marked as optional can be omitted entirely from requests
8. **German Field Names**: Most field names are now in German - update your data models
9. **JSON Arrays**: For list fields like `ausgeschlossene_therapeuten`, always send as arrays even if empty
10. **Availability Structure**: The `zeitliche_verfuegbarkeit` and `telefonische_erreichbarkeit` fields use weekday names in English (lowercase) as keys

## Migration Guide

### Old Field → New Field Mappings

#### Therapist Fields:
- `potentially_available` → `potenziell_verfuegbar`
- `potentially_available_notes` → `potenziell_verfuegbar_notizen`
- `next_contactable_date` → `naechster_kontakt_moeglich`
- `preferred_diagnoses` → `bevorzugte_diagnosen`
- `age_min` → `alter_min`
- `age_max` → `alter_max`
- `gender_preference` → `geschlechtspraeferenz`
- `working_hours` → `arbeitszeiten`

#### Email Fields:
- `subject` → `betreff`
- `recipient_email` → `empfaenger_email`
- `recipient_name` → `empfaenger_name`
- `sender_email` → `absender_email`
- `sender_name` → `absender_name`
- `response_received` → `antwort_erhalten`
- `response_date` → `antwortdatum`
- `response_content` → `antwortinhalt`
- `follow_up_required` → `nachverfolgung_erforderlich`
- `follow_up_notes` → `nachverfolgung_notizen`

#### Phone Call Fields:
- `scheduled_date` → `geplantes_datum`
- `scheduled_time` → `geplante_zeit`
- `duration_minutes` → `dauer_minuten`
- `actual_date` → `tatsaechliches_datum`
- `actual_time` → `tatsaechliche_zeit`
- `outcome` → `ergebnis`
- `notes` → `notizen`
- `retry_after` → `wiederholen_nach`