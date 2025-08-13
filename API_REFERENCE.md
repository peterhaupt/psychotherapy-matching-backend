# API Reference - Psychotherapy Matching Platform

**Single Source of Truth for All API Integration**

Last Updated: August 2025

## Overview

This document contains the complete API specification for all microservices. All field names use German terminology and flat structure (no nested objects).

**Base URLs:**
- Patient Service: `http://localhost:8001/api`
- Therapist Service: `http://localhost:8002/api`
- Matching Service: `http://localhost:8003/api`
- Communication Service: `http://localhost:8004/api`
- Geocoding Service: `http://localhost:8005/api`

**Authentication:** None (internal administrative interface)

## Important Notes on German Enums

**All German enums in the system follow proper German grammar rules:**
- Nouns are capitalized (e.g., "Suche" in "auf_der_Suche")
- The system enforces exact capitalization - API calls must match exactly
- This affects `Patientenstatus`, `Therapeutgeschlechtspraeferenz`, and other enum values

## Dynamic Configuration

The following values are configurable via environment variables and will be reflected in error messages and validation:

- **MIN_ANFRAGE_SIZE**: Minimum patients per inquiry (default: 1)
- **MAX_ANFRAGE_SIZE**: Maximum patients per inquiry (default: 6) 
- **PLZ_MATCH_DIGITS**: PLZ prefix length for filtering (default: 2)
- **FOLLOW_UP_THRESHOLD_DAYS**: Days before follow-up needed (default: 7)
- **DEFAULT_PHONE_CALL_TIME**: Default time for phone calls (default: "12:00")

Error messages and validation will reflect the configured values, not hardcoded constants.

**Note:** All timeout values, check intervals, and batch sizes mentioned in this documentation are configurable via environment variables and the actual values may differ from examples based on deployment configuration.

## Common Response Patterns

### Success Response
```json
{
  "id": 1,
  "anrede": "Frau",
  "geschlecht": "weiblich",
  "vorname": "Anna",
  "nachname": "Müller",
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
```

### Error Response
```json
{
  "message": "Validation error description"
}
```

### Pagination Response (All List Endpoints)
```json
{
  "data": [...],
  "page": 1,
  "limit": 20,
  "total": 150
}
```

**Pagination Parameters (Available on ALL list endpoints):**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

## Automatically Managed Fields

The following fields are managed automatically by the backend and **cannot be set manually via API**:

### Patient Service
- **`startdatum`**: Automatically set to today's date when BOTH conditions are met:
  - `vertraege_unterschrieben` = true
  - `zahlung_eingegangen` = true (PHASE 2)
  - Once set, it never changes
  - Also triggers automatic status change from "offen" to "auf_der_Suche"
  
- **`letzter_kontakt`**: Automatically updated to today's date when:
  - An email is sent to the patient (status = "Gesendet")
  - The patient responds to an email (antwort_erhalten = true)
  - A phone call with the patient is completed (status = "abgeschlossen")

**Note:** Any attempt to set these fields via POST or PUT requests will be silently ignored.

## Valid Symptoms List (PHASE 2)

The `symptome` field must contain between 1 and 3 symptoms from this predefined list:

### HÄUFIGSTE ANLIEGEN (Top 5)
- "Depression / Niedergeschlagenheit"
- "Ängste / Panikattacken"
- "Burnout / Erschöpfung"
- "Schlafstörungen"
- "Stress / Überforderung"

### STIMMUNG & GEFÜHLE
- "Trauer / Verlust"
- "Reizbarkeit / Wutausbrüche"
- "Stimmungsschwankungen"
- "Innere Leere"
- "Einsamkeit"

### DENKEN & GRÜBELN
- "Sorgen / Grübeln"
- "Selbstzweifel"
- "Konzentrationsprobleme"
- "Negative Gedanken"
- "Entscheidungsschwierigkeiten"

### KÖRPER & GESUNDHEIT
- "Psychosomatische Beschwerden"
- "Chronische Schmerzen"
- "Essstörungen"
- "Suchtprobleme (Alkohol/Drogen)"
- "Sexuelle Probleme"

### BEZIEHUNGEN & SOZIALES
- "Beziehungsprobleme"
- "Familienkonflikte"
- "Sozialer Rückzug"
- "Mobbing"
- "Trennungsschmerz"

### BESONDERE BELASTUNGEN
- "Traumatische Erlebnisse"
- "Zwänge"
- "Selbstverletzung"
- "Suizidgedanken"
- "Identitätskrise"

## Complex Field Formats

### Time Availability (zeitliche_verfuegbarkeit)

**Backend Format (German days, string arrays):**
```json
{
  "zeitliche_verfuegbarkeit": {
    "montag": ["09:00-12:00", "14:00-18:00"],
    "dienstag": ["09:00-17:00"],
    "mittwoch": ["14:00-18:00"]
  }
}
```

### Phone Availability (telefonische_erreichbarkeit)

**Format:** Same as zeitliche_verfuegbarkeit
```json
{
  "telefonische_erreichbarkeit": {
    "montag": ["10:00-12:00", "14:00-16:00"],
    "mittwoch": ["14:00-16:00"]
  }
}
```

### Spatial Availability (raeumliche_verfuegbarkeit)

**Format:**
```json
{
  "raeumliche_verfuegbarkeit": {
    "max_km": 30
  }
}
```

### Work Hours (arbeitszeiten)

**Format:** Same as zeitliche_verfuegbarkeit
```json
{
  "arbeitszeiten": {
    "montag": ["08:00-18:00"],
    "dienstag": ["08:00-18:00"],
    "mittwoch": ["08:00-14:00"]
  }
}
```

### Excluded Therapists (ausgeschlossene_therapeuten)

**Simple Format (List of IDs):**
```json
{
  "ausgeschlossene_therapeuten": [45, 67, 123]
}
```

**Extended Format (With Metadata):**
```json
{
  "ausgeschlossene_therapeuten": [
    {
      "id": 45,
      "excluded_at": "2025-06-15",
      "reason": "Patient request"
    },
    {
      "id": 67,
      "excluded_at": "2025-06-10", 
      "reason": "Rejected: abgelehnt_nicht_geeignet"
    }
  ]
}
```

### Languages (fremdsprachen)

**Format:** Always returns array, never null
```json
{
  "fremdsprachen": ["Englisch", "Französisch", "Spanisch"]
}
```

**Empty case:**
```json
{
  "fremdsprachen": []
}
```

### Symptoms (symptome) - PHASE 2 CHANGED

**Format:** JSONB array containing 1-3 symptom strings
```json
{
  "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"]
}
```

**Validation:** 
- Must contain between 1 and 3 symptoms
- Each symptom must be from the predefined list (see Valid Symptoms List section)
- Cannot be null or empty

## Enum Values

### Anrede (Salutation)
```
"Herr"
"Frau"
```

### Geschlecht (Gender)
```
"männlich"
"weiblich"
"divers"
"keine_Angabe"
```

### Patient Status (patientenstatus)
**Note the capital 'S' in 'Suche':**
```
"offen"
"auf_der_Suche"  # Capital 'S' - German noun capitalization
"in_Therapie"
"Therapie_abgeschlossen"
"Suche_abgebrochen"
"Therapie_abgebrochen"
```

### Therapist Status (therapeutstatus)
```
"aktiv"
"gesperrt"
"inaktiv"
```

### Search Status (suchstatus)
```
"aktiv"
"erfolgreich"
"pausiert"
"abgebrochen"
```

### Email Status (emailstatus)
```
"Entwurf"
"In_Warteschlange"
"Wird_gesendet"
"Gesendet"
"Fehlgeschlagen"
```

### Phone Call Status (telefonanrufstatus)
```
"geplant"
"abgeschlossen"
"fehlgeschlagen"
"abgebrochen"
```

### Gender Preference (therapeutgeschlechtspraeferenz)
```
"Männlich"
"Weiblich"
"Egal"
```

### Therapy Procedures (therapieverfahren) - **SINGLE ENUM FIELD**
```
"egal"
"Verhaltenstherapie"
"tiefenpsychologisch_fundierte_Psychotherapie"
```
**Note:** This enum is used for BOTH:
- Patients: `bevorzugtes_therapieverfahren` field
- Therapists: `psychotherapieverfahren` field (PHASE 2: Changed from array to single value)
- Both fields are single enum values, not arrays
- Default for both is "egal"

### Response Type (antworttyp)
```
"vollstaendige_Annahme"
"teilweise_Annahme"
"vollstaendige_Ablehnung"
"keine_Antwort"
```

### Patient Outcomes (patientenergebnis)
```
"angenommen"
"abgelehnt_Kapazitaet"
"abgelehnt_nicht_geeignet"
"abgelehnt_sonstiges"
"nicht_erschienen"
"in_Sitzungen"
```

---

# Communication Service API

## GET /emails

**Description:** Retrieve all emails with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `patient_id` (optional): Filter by patient - **PHASE 2: Now supports patients**
- `recipient_type` (optional): Filter by recipient type ("therapist" or "patient")
- `status` (optional): Filter by email status
- `antwort_erhalten` (optional): Filter by response received (boolean)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
# Get all emails for a specific patient
curl "http://localhost:8004/api/emails?patient_id=30"

# Get all emails for therapists
curl "http://localhost:8004/api/emails?recipient_type=therapist&status=Gesendet"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "therapist_id": 123,
      "patient_id": null,
      "betreff": "Therapieanfrage für mehrere Patienten",
      "empfaenger_email": "doctor@example.com",
      "empfaenger_name": "Dr. Schmidt",
      "absender_email": "info@curavani.de",
      "absender_name": "Curavani Team",
      "status": "Gesendet",
      "antwort_erhalten": false,
      "antwortdatum": null,
      "antwortinhalt": null,
      "gesendet_am": "2025-06-08",
      "created_at": "2025-06-08",
      "updated_at": "2025-06-08"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 156
}
```

## GET /emails/{id}

**Description:** Retrieve a specific email by ID.

**Example Request:**
```bash
curl "http://localhost:8004/api/emails/1"
```

**Example Response:** Same structure as single email in list response, plus `inhalt_html` and `inhalt_text` fields.

## POST /emails

**Description:** Create a new email. Must specify either `therapist_id` OR `patient_id`, not both.

**Status Field Behavior:**
- Default status is "Entwurf" (draft) if not specified
- You CAN provide an initial status in the request (e.g., "In_Warteschlange" to queue immediately)
- The status field is optional and accepts any valid EmailStatus value

**Required Fields:**
- Either `therapist_id` (integer) OR `patient_id` (integer) - exactly one must be provided
- `betreff` (string)
- Either `inhalt_markdown` (string) OR `inhalt_html` (string)
- `empfaenger_email` (string)
- `empfaenger_name` (string)

**Optional Fields:**
- `status` (string) - Initial status (default: "Entwurf")
- `inhalt_text` (string) - plain text version
- `absender_email` (string) - defaults to system email
- `absender_name` (string) - defaults to system name
- `add_legal_footer` (boolean) - defaults to true

**Validation Rules:**
- Cannot specify both `therapist_id` and `patient_id`
- Must specify at least one of `therapist_id` or `patient_id`
- Must provide either `inhalt_markdown` or `inhalt_html`

**Validation Errors (400):**
```json
{
  "message": "Either therapist_id or patient_id is required"
}
```

```json
{
  "message": "Cannot specify both therapist_id and patient_id"
}
```

**Important Notes:**
1. **Status Control**: You can set initial status via the API
2. **Markdown Processing**: URLs in markdown content are automatically detected and converted to clickable links
3. **Legal Footer**: Added by default unless explicitly disabled

**Example Request (Patient Email with immediate queuing):**
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "betreff": "Update zu Ihrer Therapieplatzsuche",
    "inhalt_markdown": "# Update\n\nSehr geehrter Herr Mustermann...",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "Max Mustermann",
    "status": "In_Warteschlange"
  }'
```

## PUT /emails/{id}

**Description:** Update email response information.

**Example Request:**
```bash
curl -X PUT "http://localhost:8004/api/emails/1" \
  -H "Content-Type: application/json" \
  -d '{
    "antwort_erhalten": true,
    "antwortdatum": "2025-06-09",
    "antwortinhalt": "Ich kann 2 Patienten aufnehmen."
  }'
```

## DELETE /emails/{id}

**Description:** Delete an email.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8004/api/emails/1"
```

## GET /phone-calls

**Description:** Retrieve all phone calls with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `patient_id` (optional): Filter by patient - **PHASE 2: Now supports patients**
- `therapeutenanfrage_id` (optional): Filter by therapeutenanfrage - **PHASE 2 NEW**
- `recipient_type` (optional): Filter by recipient type ("therapist" or "patient")
- `status` (optional): Filter by call status
- `geplantes_datum` (optional): Filter by scheduled date
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "therapist_id": 123,
      "patient_id": null,
      "therapeutenanfrage_id": 456,
      "geplantes_datum": "2025-06-10",
      "geplante_zeit": "14:30",
      "dauer_minuten": 5,
      "tatsaechliches_datum": null,
      "tatsaechliche_zeit": null,
      "status": "geplant",
      "ergebnis": null,
      "notizen": "Follow-up für Anfrage #456",
      "created_at": "2025-06-09",
      "updated_at": "2025-06-09"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 23
}
```

## GET /phone-calls/{id}

**Description:** Retrieve a specific phone call by ID.

**Example Request:**
```bash
curl "http://localhost:8004/api/phone-calls/1"
```

**Example Response:**
```json
{
  "id": 1,
  "therapist_id": 123,
  "patient_id": null,
  "therapeutenanfrage_id": 456,
  "geplantes_datum": "2025-06-10",
  "geplante_zeit": "14:30",
  "dauer_minuten": 5,
  "tatsaechliches_datum": null,
  "tatsaechliche_zeit": null,
  "status": "geplant",
  "ergebnis": null,
  "notizen": "Follow-up für Anfrage #456",
  "created_at": "2025-06-09T10:30:00",
  "updated_at": "2025-06-09T10:30:00"
}
```

## POST /phone-calls

**Description:** Schedule a new phone call. Must specify either `therapist_id` OR `patient_id`, not both.

**Required Fields:**
- Either `therapist_id` (integer) OR `patient_id` (integer) - exactly one must be provided

**Optional Fields:**
- `therapeutenanfrage_id` (integer) - Link to therapeutenanfrage - **PHASE 2 NEW**
- `geplantes_datum` (string, YYYY-MM-DD) - defaults to tomorrow
- `geplante_zeit` (string, HH:MM) - for therapists: simple slot at 10:00 or 14:00; for patients: defaults to 10:00
- `dauer_minuten` (integer) - defaults to 5 for therapists, 10 for patients
- `status` (string) - defaults to "geplant"
- `notizen` (string)

**Note:** The automatic scheduling mentioned in some documentation is simplified. It just checks basic availability at 10:00 or 14:00.

**Example Response:**
```json
{
  "id": 3,
  "patient_id": 30,
  "therapist_id": null,
  "therapeutenanfrage_id": null,
  "geplantes_datum": "2025-06-15",
  "geplante_zeit": "14:00",
  "dauer_minuten": 10,
  "status": "geplant",
  "notizen": "Status update regarding therapy search",
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
```

## PUT /phone-calls/{id}

**Description:** Update phone call status and outcome.

**Optional Fields:**
- `therapeutenanfrage_id` (integer) - Link to therapeutenanfrage - **PHASE 2 NEW**
- `geplantes_datum` (string, YYYY-MM-DD)
- `geplante_zeit` (string, HH:MM)
- `dauer_minuten` (integer)
- `tatsaechliches_datum` (string, YYYY-MM-DD)
- `tatsaechliche_zeit` (string, HH:MM)
- `status` (string)
- `ergebnis` (string)
- `notizen` (string)

## DELETE /phone-calls/{id}

**Description:** Delete a phone call.

## POST /system-messages

**Description:** Send a system notification email directly without database storage. **PHASE 2 NEW**

**Required Fields:**
- `subject` (string): Email subject
- `message` (string): Message content (plain text)

**Optional Fields:**
- `sender_name` (string): Name of the sender (default: "Curavani System")

**Example Request:**
```bash
curl -X POST "http://localhost:8004/api/system-messages" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Import Error",
    "message": "Failed to import patient data: Invalid symptom in row 15",
    "sender_name": "Patient Import System"
  }'
```

**Example Response:**
```json
{
  "message": "System message sent successfully",
  "recipient": "admin@curavani.de"
}
```

---

# Geocoding Service API

## GET /geocode

**Description:** Convert an address to coordinates using Nominatim geocoding service.

**Query Parameters:**
- `address` (required): Address string to geocode

**Example Request:**
```bash
curl "http://localhost:8005/api/geocode?address=Berlin%2C%20Germany"
```

**Example Response:**
```json
{
  "latitude": 52.5200,
  "longitude": 13.4050,
  "display_name": "Berlin, Deutschland",
  "address_components": {
    "city": "Berlin",
    "country": "Deutschland",
    "postcode": "10117"
  },
  "source": "nominatim",
  "status": "success"
}
```

## GET /reverse-geocode

**Description:** Convert coordinates to an address using reverse geocoding.

**Query Parameters:**
- `lat` (required): Latitude coordinate (float)
- `lon` (required): Longitude coordinate (float)

**Example Request:**
```bash
curl "http://localhost:8005/api/reverse-geocode?lat=52.5200&lon=13.4050"
```

## GET /calculate-distance

**Description:** Calculate distance and travel time between two points using OSRM routing service with fallbacks.

**Query Parameters:**

**Origin (choose one):**
- `origin` (string): Origin address
- `origin_lat` + `origin_lon` (float): Origin coordinates

**Destination (choose one):**
- `destination` (string): Destination address  
- `destination_lat` + `destination_lon` (float): Destination coordinates

**Optional Parameters:**
- `travel_mode` (string): "car" or "transit" (default: "car")
- `no_cache` (boolean): Bypass cache for fresh calculation (default: false)
- `use_plz_fallback` (boolean): Use PLZ-based fallback for addresses (default: true)

**Example Requests:**
```bash
# Using addresses
curl "http://localhost:8005/api/calculate-distance?origin=Berlin&destination=Munich&travel_mode=car"

# Using coordinates
curl "http://localhost:8005/api/calculate-distance?origin_lat=52.5200&origin_lon=13.4050&destination_lat=48.1351&destination_lon=11.5820"
```

## GET /calculate-plz-distance

**Description:** Calculate straight-line distance between two German postal code centroids.

**Query Parameters:**
- `origin_plz` (required): Origin PLZ (5-digit German postal code)
- `destination_plz` (required): Destination PLZ (5-digit German postal code)

**Example Request:**
```bash
curl "http://localhost:8005/api/calculate-plz-distance?origin_plz=52062&destination_plz=10115"
```

---

# Error Response Formats

All endpoints follow consistent error response patterns:

### Validation Errors (400)
```json
{
  "message": "Specific validation error message"
}
```

### Not Found Errors (404)
```json
{
  "message": "Resource not found"
}
```

### Internal Server Errors (500)
```json
{
  "message": "Internal server error"
}
```

### Database Errors (500)
```json
{
  "message": "Database error: specific error details"
}
```

---

# Key Changes in Phase 2 (January 2025)

## 🔄 Patient Service Changes

### Removed Fields:
- **`diagnose`** - Completely removed from database and all endpoints
- **`psychotherapeutische_sprechstunde`** - PTV11 related field removed

### Changed Fields:
- **`symptome`** - Changed from TEXT to JSONB array
  - Must contain 1-3 symptoms from predefined list
  - Validation enforced at API level
  - Cannot be null or empty

### New Fields:
- **`zahlungsreferenz`** (String, max 8 chars) - Payment reference
- **`zahlung_eingegangen`** (Boolean) - Payment received flag

### Automatic Behaviors:
- When `zahlung_eingegangen` changes from false to true:
  - If `vertraege_unterschrieben` is also true:
    - `startdatum` automatically set to today
    - `status` automatically changes from "offen" to "auf_der_Suche"
    - Matching service notified to begin search

### New Endpoints:
- **`GET /api/patients/import-status`** - Monitor import system health
- **`PATCH /api/patients/{id}/last-contact`** - Update last contact date only

## 🔄 Therapist Service Changes

### Changed Fields:
- **`psychotherapieverfahren`** - Changed from JSONB array to single ENUM value
  - Now same as patient's `bevorzugtes_therapieverfahren`
  - Values: "egal", "Verhaltenstherapie", "tiefenpsychologisch_fundierte_Psychotherapie"

### New Fields:
- **`ueber_curavani_informiert`** (Boolean) - Whether therapist has been informed about Curavani

### New Query Parameters:
- **`plz_prefix`** - Filter therapists by PLZ prefix (e.g., "52")

### New Endpoints:
- **`GET /api/therapists/import-status`** - Monitor import system health

## 🔄 Matching Service Changes

### Platzsuche Creation:
- No longer requires `diagnose` field
- Requires `symptome` as JSONB array with 1-3 valid symptoms

### Therapeutenanfrage:
- Email templates updated to format symptoms as comma-separated list
- Removed diagnosis field from emails

### Therapist Selection:
- Email deduplication implemented
- Multiple therapists sharing same email are grouped
- Only practice owner is returned for selection

### New Endpoints:
- **`POST /api/platzsuchen/{id}/kontaktanfrage`** - Request additional contacts
- **`DELETE /api/platzsuchen/{id}`** - Delete patient search
- **`DELETE /api/therapeutenanfragen/{id}`** - Delete therapeutenanfrage

## 🔄 Communication Service Changes

### Phone Calls:
- New field **`therapeutenanfrage_id`** - Links calls to specific anfragen
- Can now be created for patients (not just therapists)
- New endpoint **`GET /api/phone-calls/{id}`** - Get individual phone call

### Emails:
- Can now be created for patients (not just therapists)
- Both `therapist_id` and `patient_id` supported
- Status field CAN be set on creation (not always draft)

### New Endpoint:
- **`POST /api/system-messages`** - Send system notifications without database storage

## 🔄 German Enum Capitalization

All German enums follow proper grammar rules with noun capitalization:
- `auf_der_Suche` (not `auf_der_suche`)
- `in_Therapie` (not `in_therapie`)
- API calls must use exact capitalization

---

# Implementation Notes

- All date fields use simple format: "YYYY-MM-DD"
- All time fields use 24-hour format: "HH:MM"
- German day names in lowercase: montag, dienstag, etc.
- JSONB fields return empty arrays/objects instead of null
- Pagination available on all list endpoints
- Search functionality uses case-insensitive partial matching
- Automatic field management cannot be overridden via API
- Configuration values (timeouts, intervals, batch sizes) are environment-variable driven

# Health Check Endpoints

## All Services

**Description:** Check service health status.

**Example Request:**
```bash
curl "http://localhost:8001/health"
```

**Example Response:**
```json
{
  "status": "healthy",
  "service": "patient-service"
}
```

## Import Health Check (Patient & Therapist Services)

**Description:** Check import system health status with detailed diagnostics.

**Example Request:**
```bash
curl "http://localhost:8001/health/import"
# or
curl "http://localhost:8002/health/import"
```

**Example Response (Healthy):**
```json
{
  "status": "healthy",
  "service": "patient-import-monitor",
  "details": {
    "monitor_running": true,
    "last_check": "2025-01-15T10:30:00",
    "files_processed_today": 5,
    "files_failed_today": 0,
    "issues": []
  }
}
```

**Example Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "service": "therapist-import-monitor",
  "details": {
    "monitor_running": true,
    "last_check": "2025-01-15T08:30:00",
    "files_processed_today": 3,
    "files_failed_today": 2,
    "last_error": "Invalid JSON in file 52062.json",
    "last_error_time": "2025-01-15T08:25:00",
    "issues": [
      "High failure rate: 66.7%",
      "Monitor inactive for too long"
    ]
  }
}
```

---

# Patient Service API

## GET /patients

**Description:** Retrieve all patients with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by patient status
- `search` (optional): Search across vorname, nachname, and email fields (case-insensitive partial match)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Search Behavior:**
- Searches across `vorname`, `nachname`, and `email` fields
- Case-insensitive partial matching
- Results include all patients where ANY of the searched fields contain the search term

**Example Request:**
```bash
# Filter by status (note capital S in auf_der_Suche)
curl "http://localhost:8001/api/patients?status=auf_der_Suche&page=1&limit=20"

# Search for patients
curl "http://localhost:8001/api/patients?search=mueller"

# Combine search and status filter
curl "http://localhost:8001/api/patients?search=anna&status=auf_der_Suche"
```

**Example Response (COMPLETE - ALL FIELDS - PHASE 2 UPDATED):**
```json
{
  "data": [
    {
      "id": 1,
      "anrede": "Frau",
      "geschlecht": "weiblich",
      "vorname": "Anna",
      "nachname": "Müller",
      "strasse": "Hauptstraße 123",
      "plz": "10115",
      "ort": "Berlin",
      "email": "anna.mueller@email.com",
      "telefon": "+49 30 12345678",
      "hausarzt": "Dr. Schmidt",
      "krankenkasse": "AOK",
      "krankenversicherungsnummer": "A123456789",
      "geburtsdatum": "1985-03-15",
      "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"],
      "erfahrung_mit_psychotherapie": false,
      "letzte_sitzung_vorherige_psychotherapie": null,
      "vertraege_unterschrieben": true,
      "startdatum": "2025-01-15",
      "erster_therapieplatz_am": null,
      "funktionierender_therapieplatz_am": null,
      "status": "auf_der_Suche",
      "empfehler_der_unterstuetzung": "Hausarzt",
      "zahlungsreferenz": "5d54d4db",
      "zahlung_eingegangen": true,
      "zeitliche_verfuegbarkeit": {
        "montag": ["09:00-17:00"],
        "dienstag": ["09:00-17:00"],
        "mittwoch": ["14:00-18:00"]
      },
      "raeumliche_verfuegbarkeit": {
        "max_km": 30
      },
      "verkehrsmittel": "Auto",
      "offen_fuer_gruppentherapie": false,
      "offen_fuer_diga": false,
      "letzter_kontakt": "2025-06-15",
      "ausgeschlossene_therapeuten": [45, 67],
      "bevorzugtes_therapeutengeschlecht": "Weiblich",
      "bevorzugtes_therapieverfahren": "Verhaltenstherapie",
      "created_at": "2025-05-01",
      "updated_at": "2025-06-01"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 45
}
```

## GET /patients/{id}

**Description:** Retrieve a specific patient by ID.

**Example Request:**
```bash
curl "http://localhost:8001/api/patients/1"
```

**Example Response:** Same structure as single patient in list response (all fields included).

## PATCH /patients/{id}/last-contact

**Description:** Update only the last contact date for a patient. Used by communication service to automatically update when emails or calls are sent.

**Request Body (Optional):**
```json
{
  "date": "2025-01-15"  // Optional, defaults to today if not provided
}
```

**Example Request:**
```bash
curl -X PATCH "http://localhost:8001/api/patients/1/last-contact" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-01-15"}'
```

**Example Response:**
```json
{
  "message": "Last contact updated",
  "letzter_kontakt": "2025-01-15"
}
```

## GET /patients/{id}/communication

**Description:** Get complete communication history for a patient (emails and phone calls).

**Example Request:**
```bash
curl "http://localhost:8001/api/patients/30/communication"
```

**Example Response:**
```json
{
  "patient_id": 30,
  "patient_name": "Max Mustermann",
  "last_contact": "2025-06-15",
  "total_emails": 3,
  "total_calls": 1,
  "communications": [
    {
      "type": "email",
      "id": 45,
      "date": "2025-06-15",
      "subject": "Update zu Ihrer Therapieplatzsuche",
      "status": "Gesendet",
      "response_received": false,
      "data": {
        "id": 45,
        "patient_id": 30,
        "betreff": "Update zu Ihrer Therapieplatzsuche",
        "empfaenger_email": "max.mustermann@email.com",
        "status": "Gesendet",
        "gesendet_am": "2025-06-15"
      }
    },
    {
      "type": "phone_call",
      "id": 12,
      "date": "2025-06-10",
      "status": "abgeschlossen",
      "outcome": "Patient informiert über Fortschritt",
      "data": {
        "id": 12,
        "patient_id": 30,
        "geplantes_datum": "2025-06-10",
        "geplante_zeit": "14:00",
        "status": "abgeschlossen"
      }
    }
  ]
}
```

## GET /patients/import-status

**Description:** Get the current status of the patient import system.

**Example Request:**
```bash
curl "http://localhost:8001/api/patients/import-status"
```

**Example Response:**
```json
{
  "running": true,
  "last_check": "2025-01-15T10:30:00",
  "files_processed_today": 12,
  "files_failed_today": 1,
  "last_error": "patient_123.json: Invalid symptom: 'Unknown'",
  "last_error_time": "2025-01-15T09:45:00",
  "total_processed": 1234,
  "total_failed": 23,
  "recent_imports": [
    {
      "file": "patient_456.json",
      "status": "success",
      "time": "2025-01-15T10:25:00"
    },
    {
      "file": "patient_123.json",
      "status": "failed",
      "error": "Invalid symptom: 'Unknown'",
      "time": "2025-01-15T09:45:00"
    }
  ]
}
```

## POST /patients

**Description:** Create a new patient.

**Required Fields:**
- `anrede` (string) - Must be one of: "Herr", "Frau"
- `geschlecht` (string) - Must be one of: "männlich", "weiblich", "divers", "keine_Angabe"
- `vorname` (string)
- `nachname` (string)

**All Optional Fields (COMPLETE LIST - PHASE 2 UPDATED):**

**Personal Information:**
- `strasse` (string) 
- `plz` (string)
- `ort` (string)
- `email` (string)
- `telefon` (string)

**Medical Information:**
- `hausarzt` (string)
- `krankenkasse` (string)
- `krankenversicherungsnummer` (string)
- `geburtsdatum` (string, YYYY-MM-DD)
- `symptome` (array of strings) - **PHASE 2: Must contain 1-3 symptoms from predefined list**
- `erfahrung_mit_psychotherapie` (boolean)
- `letzte_sitzung_vorherige_psychotherapie` (string, YYYY-MM-DD)

**Process Status:**
- `vertraege_unterschrieben` (boolean)
- `startdatum` **AUTOMATIC** - Set when both vertraege_unterschrieben and zahlung_eingegangen are true
- `status` (string, see enum values) - **AUTOMATIC** changes to "auf_der_Suche" when payment confirmed
- `empfehler_der_unterstuetzung` (string)
- `erster_therapieplatz_am` (string, YYYY-MM-DD)
- `funktionierender_therapieplatz_am` (string, YYYY-MM-DD)

**Payment Information - PHASE 2 NEW:**
- `zahlungsreferenz` (string, max 8 chars) - Payment reference
- `zahlung_eingegangen` (boolean) - Payment received flag

**Availability:**
- `zeitliche_verfuegbarkeit` (object, see format above)
- `raeumliche_verfuegbarkeit` (object, see format above)
- `verkehrsmittel` (string)

**Preferences:**
- `offen_fuer_gruppentherapie` (boolean)
- `offen_fuer_diga` (boolean)
- `letzter_kontakt` **AUTOMATIC** - Updated via communication events

**Therapist Preferences:**
- `ausgeschlossene_therapeuten` (array of integers)
- `bevorzugtes_therapeutengeschlecht` (string, see enum)
- `bevorzugtes_therapieverfahren` (string, **SINGLE VALUE** - see enum)

**Example Request (Complete - PHASE 2):**
```bash
curl -X POST "http://localhost:8001/api/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "anrede": "Herr",
    "geschlecht": "männlich",
    "vorname": "Thomas",
    "nachname": "Schmidt",
    "strasse": "Berliner Str. 45",
    "plz": "80331",
    "ort": "München",
    "email": "thomas.schmidt@email.com",
    "telefon": "+49 89 87654321",
    "hausarzt": "Dr. Weber",
    "krankenkasse": "TK",
    "geburtsdatum": "1978-11-22",
    "symptome": ["Ängste / Panikattacken", "Herzrasen"],
    "erfahrung_mit_psychotherapie": true,
    "letzte_sitzung_vorherige_psychotherapie": "2021-08-15",
    "vertraege_unterschrieben": false,
    "zahlungsreferenz": "ab3c45ef",
    "zahlung_eingegangen": false,
    "zeitliche_verfuegbarkeit": {
      "montag": ["18:00-20:00"],
      "mittwoch": ["18:00-20:00"],
      "freitag": ["14:00-18:00"]
    },
    "raeumliche_verfuegbarkeit": {
      "max_km": 25
    },
    "verkehrsmittel": "ÖPNV",
    "bevorzugtes_therapeutengeschlecht": "Egal",
    "bevorzugtes_therapieverfahren": "Verhaltenstherapie",
    "offen_fuer_gruppentherapie": true,
    "ausgeschlossene_therapeuten": []
  }'
```

**Note:** Do not include `startdatum` or `letzter_kontakt` in requests - they are managed automatically.

**Example Response:**
```json
{
  "id": 4,
  "anrede": "Herr",
  "geschlecht": "männlich",
  "vorname": "Thomas",
  "nachname": "Schmidt",
  "strasse": "Berliner Str. 45",
  "plz": "80331",
  "ort": "München",
  "email": "thomas.schmidt@email.com",
  "telefon": "+49 89 87654321",
  "status": "offen",
  "symptome": ["Ängste / Panikattacken", "Herzrasen"],
  "erfahrung_mit_psychotherapie": true,
  "letzte_sitzung_vorherige_psychotherapie": "2021-08-15",
  "bevorzugtes_therapieverfahren": "Verhaltenstherapie",
  "zahlungsreferenz": "ab3c45ef",
  "zahlung_eingegangen": false,
  "startdatum": null,
  "letzter_kontakt": null,
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
```

**Validation Error Examples:**
```json
{
  "message": "Between 1 and 3 symptoms must be selected"
}
```

```json
{
  "message": "Invalid symptom: 'Unknown symptom'. Must be from the predefined list"
}
```

```json
{
  "message": "Invalid therapy method 'Psychoanalyse'. Valid values: egal, Verhaltenstherapie, tiefenpsychologisch_fundierte_Psychotherapie"
}
```

## PUT /patients/{id}

**Description:** Update an existing patient.

**Accepts all fields from POST request as optional parameters, except:**
- `startdatum` - Automatically managed
- `letzter_kontakt` - Automatically managed

**Automatic Status Change (PHASE 2):**
When `zahlung_eingegangen` is changed from false to true:
- If `vertraege_unterschrieben` is also true:
  - `startdatum` is automatically set to today
  - `status` automatically changes from "offen" to "auf_der_Suche"
  - Matching service is notified to begin search

**Example Request:**
```bash
curl -X PUT "http://localhost:8001/api/patients/1" \
  -H "Content-Type: application/json" \
  -d '{
    "zahlung_eingegangen": true,
    "symptome": ["Burnout / Erschöpfung", "Stress / Überforderung", "Schlafstörungen"]
  }'
```

**Example Response (after payment confirmation):**
```json
{
  "id": 1,
  "anrede": "Frau",
  "geschlecht": "weiblich",
  "vorname": "Anna",
  "nachname": "Müller",
  "status": "auf_der_Suche",
  "zahlung_eingegangen": true,
  "startdatum": "2025-01-15",
  "symptome": ["Burnout / Erschöpfung", "Stress / Überforderung", "Schlafstörungen"],
  "letzter_kontakt": "2025-01-15",
  "updated_at": "2025-01-15"
}
```

## DELETE /patients/{id}

**Description:** Delete a patient.

**Note:** Patient deletion does not automatically clean up related records in other services. Administrative cleanup may be required for orphaned data.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8001/api/patients/1"
```

**Example Response:**
```json
{
  "message": "Patient deleted successfully"
}
```

**Example Request:**
```bash
curl -X DELETE "http://localhost:8001/api/patients/1"
```

**Example Response:**
```json
{
  "message": "Patient deleted successfully"
}
```

---

# Therapist Service API

## GET /therapists

**Description:** Retrieve all therapists with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by therapist status ("aktiv", "gesperrt", "inaktiv")
- `potenziell_verfuegbar` (optional): Filter by availability (boolean)
- `search` (optional): Search across vorname, nachname, and psychotherapieverfahren fields
- `plz_prefix` (optional): Filter by PLZ prefix (e.g., "52" for all PLZ starting with 52)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Search Behavior:**
- Searches across `vorname`, `nachname` fields with case-insensitive partial matching
- For `psychotherapieverfahren`, checks if search term matches any part of the enum values
  - Example: searching "verhaltens" will match therapists with "Verhaltenstherapie"
  - Example: searching "tiefen" will match "tiefenpsychologisch_fundierte_Psychotherapie"
- Results include all therapists where ANY of the searched fields contain the search term

**Example Request:**
```bash
# Filter by status and availability
curl "http://localhost:8002/api/therapists?status=aktiv&potenziell_verfuegbar=true"

# Filter by PLZ prefix
curl "http://localhost:8002/api/therapists?plz_prefix=52"

# Search for therapists
curl "http://localhost:8002/api/therapists?search=weber"

# Search for therapy method
curl "http://localhost:8002/api/therapists?search=verhaltens"

# Combine search and filters
curl "http://localhost:8002/api/therapists?search=schmidt&status=aktiv&plz_prefix=10"
```

**Example Response (COMPLETE - ALL FIELDS - PHASE 2 UPDATED):**
```json
{
  "data": [
    {
      "id": 1,
      "anrede": "Frau",
      "geschlecht": "weiblich",
      "titel": "Dr. med.",
      "vorname": "Maria",
      "nachname": "Weber",
      "strasse": "Praxis Str. 12",
      "plz": "10117",
      "ort": "Berlin",
      "telefon": "+49 30 98765432",
      "fax": "+49 30 98765433",
      "email": "dr.weber@praxis.de",
      "webseite": "https://www.praxis-weber.de",
      "kassensitz": true,
      "telefonische_erreichbarkeit": {
        "montag": ["09:00-12:00"],
        "mittwoch": ["14:00-16:00"]
      },
      "fremdsprachen": ["Englisch", "Französisch"],
      "psychotherapieverfahren": "Verhaltenstherapie",
      "zusatzqualifikationen": "Traumatherapie, EMDR",
      "besondere_leistungsangebote": "Online-Therapie verfügbar",
      "letzter_kontakt_email": "2025-05-15",
      "letzter_kontakt_telefon": null,
      "letztes_persoenliches_gespraech": "2025-04-10",
      "potenziell_verfuegbar": true,
      "potenziell_verfuegbar_notizen": "Ab Juli 2025 verfügbar",
      "ueber_curavani_informiert": true,
      "naechster_kontakt_moeglich": "2025-07-01",
      "bevorzugte_diagnosen": ["F32", "F41", "F43"],
      "alter_min": 18,
      "alter_max": 65,
      "geschlechtspraeferenz": "Egal",
      "arbeitszeiten": {
        "montag": ["08:00-18:00"],
        "dienstag": ["08:00-18:00"]
      },
      "bevorzugt_gruppentherapie": false,
      "status": "aktiv",
      "sperrgrund": null,
      "sperrdatum": null,
      "created_at": "2025-01-10",
      "updated_at": "2025-06-01"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 85
}
```

**Empty JSONB Fields Example:**
```json
{
  "id": 2,
  "anrede": "Herr",
  "geschlecht": "männlich",
  "vorname": "Max",
  "nachname": "Mustermann",
  "telefonische_erreichbarkeit": {},
  "fremdsprachen": [],
  "psychotherapieverfahren": "egal",
  "ueber_curavani_informiert": false,
  "bevorzugte_diagnosen": [],
  "arbeitszeiten": {}
}
```

## GET /therapists/{id}

**Description:** Retrieve a specific therapist by ID.

**Example Request:**
```bash
curl "http://localhost:8002/api/therapists/1"
```

**Example Response:** Same structure as single therapist in list response.

## GET /therapists/{id}/communication

**Description:** Get complete communication history for a therapist (emails and phone calls).

**Example Request:**
```bash
curl "http://localhost:8002/api/therapists/123/communication"
```

**Example Response:**
```json
{
  "therapist_id": 123,
  "therapist_name": "Dr. Maria Weber",
  "last_contact": "2025-06-18",
  "total_emails": 5,
  "total_calls": 2,
  "communications": [
    {
      "type": "email",
      "id": 78,
      "date": "2025-06-18",
      "subject": "Therapieanfrage für mehrere Patienten",
      "status": "Gesendet",
      "response_received": true,
      "data": {
        "id": 78,
        "therapist_id": 123,
        "betreff": "Therapieanfrage für mehrere Patienten",
        "empfaenger_email": "dr.weber@praxis.de",
        "status": "Gesendet",
        "gesendet_am": "2025-06-18",
        "antwort_erhalten": true,
        "antwortdatum": "2025-06-19"
      }
    },
    {
      "type": "phone_call",
      "id": 23,
      "date": "2025-06-15",
      "status": "abgeschlossen",
      "outcome": "Therapeut kann 2 Patienten aufnehmen",
      "data": {
        "id": 23,
        "therapist_id": 123,
        "geplantes_datum": "2025-06-15",
        "geplante_zeit": "10:00",
        "status": "abgeschlossen",
        "ergebnis": "Therapeut kann 2 Patienten aufnehmen"
      }
    }
  ]
}
```

## GET /therapists/import-status

**Description:** Get the current status of the therapist import system.

**Example Request:**
```bash
curl "http://localhost:8002/api/therapists/import-status"
```

**Example Response:**
```json
{
  "running": true,
  "last_check": "2025-01-15T10:30:00",
  "last_import_run": "2025-01-15T02:00:00",
  "next_import_run": "2025-01-16T02:00:00",
  "files_processed_today": 5,
  "therapists_processed_today": 450,
  "therapists_failed_today": 12,
  "last_error": null,
  "last_error_time": null,
  "total_files_processed": 150,
  "total_therapists_processed": 13500,
  "total_therapists_failed": 234,
  "recent_imports": [
    {
      "file": "20250115/52062.json",
      "therapist_count": 89,
      "success_count": 87,
      "failed_count": 2,
      "time": "2025-01-15T02:15:00"
    }
  ]
}
```

## POST /therapists

**Description:** Create a new therapist.

**Required Fields:**
- `anrede` (string) - Must be one of: "Herr", "Frau"
- `geschlecht` (string) - Must be one of: "männlich", "weiblich", "divers", "keine_Angabe"
- `vorname` (string)
- `nachname` (string)

**All Optional Fields (COMPLETE LIST - PHASE 2 UPDATED):**

**Personal Information:**
- `titel` (string)
- `strasse` (string)
- `plz` (string)
- `ort` (string)
- `telefon` (string)
- `fax` (string)
- `email` (string)
- `webseite` (string)

**Professional Information:**
- `kassensitz` (boolean)
- `telefonische_erreichbarkeit` (object, see format above)
- `fremdsprachen` (array of strings)
- `psychotherapieverfahren` (string, **PHASE 2: SINGLE VALUE** - see enum, default: "egal")
- `zusatzqualifikationen` (string)
- `besondere_leistungsangebote` (string)

**Contact History:**
- `letzter_kontakt_email` (string, YYYY-MM-DD)
- `letzter_kontakt_telefon` (string, YYYY-MM-DD)
- `letztes_persoenliches_gespraech` (string, YYYY-MM-DD)

**Availability:**
- `potenziell_verfuegbar` (boolean)
- `potenziell_verfuegbar_notizen` (string)
- `ueber_curavani_informiert` (boolean) - **PHASE 2 NEW**

**Inquiry System Fields:**
- `naechster_kontakt_moeglich` (string, YYYY-MM-DD)
- `bevorzugte_diagnosen` (array of strings)
- `alter_min` (integer)
- `alter_max` (integer)
- `geschlechtspraeferenz` (string)
- `arbeitszeiten` (object, see format above)
- `bevorzugt_gruppentherapie` (boolean)

**Status:**
- `status` (string, see enum values, default: "aktiv")
- `sperrgrund` (string)
- `sperrdatum` (string, YYYY-MM-DD)

**Example Request:**
```bash
curl -X POST "http://localhost:8002/api/therapists" \
  -H "Content-Type: application/json" \
  -d '{
    "anrede": "Herr",
    "geschlecht": "männlich",
    "titel": "Dr. phil.",
    "vorname": "Michael",
    "nachname": "Becker",
    "strasse": "Therapie Zentrum 5",
    "plz": "80331",
    "ort": "München",
    "telefon": "+49 89 11223344",
    "email": "m.becker@therapie.de",
    "kassensitz": true,
    "psychotherapieverfahren": "tiefenpsychologisch_fundierte_Psychotherapie",
    "potenziell_verfuegbar": true,
    "ueber_curavani_informiert": false,
    "bevorzugte_diagnosen": ["F32", "F33"],
    "alter_min": 25,
    "alter_max": 55,
    "geschlechtspraeferenz": "Egal",
    "bevorzugt_gruppentherapie": false
  }'
```

## PUT /therapists/{id}

**Description:** Update an existing therapist.

**Example Request:**
```bash
curl -X PUT "http://localhost:8002/api/therapists/1" \
  -H "Content-Type: application/json" \
  -d '{
    "potenziell_verfuegbar": false,
    "potenziell_verfuegbar_notizen": "Aktuell keine Kapazitäten",
    "naechster_kontakt_moeglich": "2025-09-01",
    "psychotherapieverfahren": "Verhaltenstherapie",
    "ueber_curavani_informiert": true
  }'
```

## DELETE /therapists/{id}

**Description:** Delete a therapist.

**Note:** Therapist deletion does not automatically clean up related records in other services. Administrative cleanup may be required for orphaned data.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8002/api/therapists/1"
```

**Example Response:**
```json
{
  "message": "Therapist deleted successfully"
}
```

---

# Matching Service API

## GET /platzsuchen

**Description:** Retrieve all patient searches with filtering.

**Query Parameters:**
- `status` (optional): Filter by search status ("aktiv", "erfolgreich", "pausiert", "abgebrochen")
- `patient_id` (optional): Filter by specific patient
- `min_anfragen` (optional): Minimum inquiry count
- `max_anfragen` (optional): Maximum inquiry count
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
curl "http://localhost:8003/api/platzsuchen?status=aktiv"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "patient_id": 123,
      "patienten_name": "Anna Müller",
      "status": "aktiv",
      "created_at": "2025-06-07",
      "updated_at": "2025-06-08",
      "aktive_anfragen": 3,
      "gesamt_anfragen": 8,
      "ausgeschlossene_therapeuten_anzahl": 2,
      "offen_fuer_gruppentherapie": false
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 45
}
```

## GET /platzsuchen/{id}

**Description:** Get patient search details with inquiry history.

**Example Request:**
```bash
curl "http://localhost:8003/api/platzsuchen/1"
```

**Example Response:**
```json
{
  "id": 1,
  "patient_id": 123,
  "patient": {
    "vorname": "Anna",
    "nachname": "Müller",
    "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"],
    "krankenkasse": "AOK"
  },
  "status": "aktiv",
  "created_at": "2025-06-07",
  "updated_at": "2025-06-08",
  "ausgeschlossene_therapeuten": [45, 67],
  "erfolgreiche_vermittlung_datum": null,
  "notizen": "Patient urgently needs therapy",
  "aktive_anfragen": 3,
  "gesamt_anfragen": 8,
  "anfrage_verlauf": [
    {
      "anfrage_id": 101,
      "therapist_id": 123,
      "therapeuten_name": "Dr. Schmidt",
      "position": 2,
      "status": "anstehend",
      "outcome": null,
      "sent_date": "2025-06-07",
      "response_date": null
    }
  ]
}
```

## POST /platzsuchen

**Description:** Create a new patient search with enhanced validation.

**Required Fields:**
- `patient_id` (integer)

**Optional Fields:**
- `notizen` (string) - Optional notes about the search

**Patient Data Validation (PHASE 2 UPDATED):**
Before creating a platzsuche, the patient must have the following required data:

**Required String Fields (non-empty):**
- `geschlecht`
- `symptome` - **PHASE 2: Must be JSONB array with 1-3 valid symptoms**
- `krankenkasse`
- `geburtsdatum`

**Required Boolean Fields (explicitly set):**
- `erfahrung_mit_psychotherapie`
- `offen_fuer_gruppentherapie`

**Required Complex Fields:**
- `zeitliche_verfuegbarkeit` - Must have at least one valid time slot

**Conditional Field:**
- `letzte_sitzung_vorherige_psychotherapie` - Required if `erfahrung_mit_psychotherapie` is true

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/platzsuchen" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 123,
    "notizen": "Patient urgently needs therapy"
  }'
```

**Success Response:**
```json
{
  "id": 1,
  "patient_id": 123,
  "status": "aktiv",
  "created_at": "2025-06-07",
  "message": "Patient search created successfully"
}
```

**Validation Error Response (PHASE 2):**
```json
{
  "message": "Cannot create platzsuche: Patient field 'symptome' is required and cannot be empty",
  "patient_id": 123
}
```

## PUT /platzsuchen/{id}

**Description:** Update a patient search (including status changes).

**Optional Fields:**
- `status` (string) - New status ("aktiv", "pausiert", "erfolgreich", "abgebrochen")
- `notizen` (string) - Notes to add or update
- `ausgeschlossene_therapeuten` (array of integers) - List of excluded therapist IDs

**Status Transition Rules:**
- `aktiv` → `pausiert`, `erfolgreich`, `abgebrochen`
- `pausiert` → `aktiv`, `abgebrochen`
- `erfolgreich` → (no transitions allowed - terminal state)
- `abgebrochen` → (no transitions allowed - terminal state)

**Example Request:**
```bash
curl -X PUT "http://localhost:8003/api/platzsuchen/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "pausiert",
    "notizen": "Patient temporarily unavailable"
  }'
```

## POST /platzsuchen/{id}/kontaktanfrage

**Description:** Request additional contacts for a patient search. Updates the total requested contact count.

**Request Body:**
```json
{
  "requested_count": 5,  // Required: Number of additional contacts to request (1-100)
  "notizen": "Patient urgently needs more options"  // Optional: Notes about the request
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/platzsuchen/1/kontaktanfrage" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_count": 3,
    "notizen": "Previous therapists declined"
  }'
```

**Example Response:**
```json
{
  "message": "Requested 3 additional contacts",
  "previous_total": 6,
  "new_total": 9,
  "search_id": 1
}
```

**Error Response (400):**
```json
{
  "message": "Can only request contacts for active searches. Current status: erfolgreich"
}
```

## DELETE /platzsuchen/{id}

**Description:** Delete a patient search and all related TherapeutAnfragePatient entries (cascade delete).

**Example Request:**
```bash
curl -X DELETE "http://localhost:8003/api/platzsuchen/1"
```

**Example Response:**
```json
{
  "message": "Patient search deleted successfully"
}
```

## GET /therapeuten-zur-auswahl

**Description:** Get therapists available for manual selection, filtered by PLZ prefix.

**Query Parameters:**
- `plz_prefix` (required): PLZ prefix with configurable digits (default: 2 digits, e.g., "52")

**Sorting Order (Email Priority with Deduplication):**
1. Practice owners only (one representative per email address)
2. Available AND informed about Curavani WITH email
3. Available AND NOT informed about Curavani WITH email  
4. Not available AND informed about Curavani WITH email
5. Others WITH email (alphabetically by name)
6. Available AND informed about Curavani WITHOUT email
7. Available AND NOT informed about Curavani WITHOUT email
8. Not available AND informed about Curavani WITHOUT email
9. Others WITHOUT email (alphabetically by name)

**Note:** Therapists with email addresses are always prioritized. Multiple therapists sharing the same email are deduplicated - only the practice owner is returned.

**Example Request:**
```bash
curl "http://localhost:8003/api/therapeuten-zur-auswahl?plz_prefix=52"
```

## GET /therapeutenanfragen

**Description:** Get all inquiries with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `versand_status` (optional): "gesendet" or "ungesendet"
- `antwort_status` (optional): "beantwortet" or "ausstehend"
- `nachverfolgung_erforderlich` (optional): boolean
- `min_size` (optional): minimum inquiry size
- `max_size` (optional): maximum inquiry size
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
curl "http://localhost:8003/api/therapeutenanfragen?versand_status=gesendet&antwort_status=ausstehend"
```

## GET /therapeutenanfragen/{id}

**Description:** Get inquiry details with patient list.

**Example Request:**
```bash
curl "http://localhost:8003/api/therapeutenanfragen/101"
```

**Example Response (PHASE 2 - symptome as array):**
```json
{
  "id": 101,
  "therapist_id": 123,
  "therapist": {
    "vorname": "Max",
    "nachname": "Mustermann",
    "email": "dr.mustermann@example.com"
  },
  "erstellt_datum": "2025-06-07",
  "gesendet_datum": "2025-06-07",
  "antwort_datum": null,
  "tage_seit_versand": 2,
  "antworttyp": null,
  "anfragegroesse": 4,
  "antwort_zusammenfassung": {
    "total_accepted": 0,
    "total_rejected": 0,
    "total_no_response": 0,
    "antwort_vollstaendig": false
  },
  "notizen": null,
  "email_id": 456,
  "phone_call_id": null,
  "patients": [
    {
      "position": 1,
      "patient_id": 1,
      "patient": {
        "vorname": "Anna",
        "nachname": "Schmidt",
        "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"]
      },
      "platzsuche_id": 10,
      "search_created_at": "2025-05-01",
      "wartezeit_tage": 37,
      "status": "anstehend",
      "antwortergebnis": null,
      "antwortnotizen": null
    }
  ],
  "nachverfolgung_erforderlich": false
}
```

## POST /therapeutenanfragen/erstellen-fuer-therapeut

**Description:** Create inquiry for manually selected therapist.

**Required Fields:**
- `therapist_id` (integer): ID of the selected therapist
- `plz_prefix` (string): PLZ prefix with configurable digits (default: 2 digits)

**Optional Fields:**
- `sofort_senden` (boolean): Send immediately if true (default: false)

**Algorithm:**
1. Filters patients by PLZ prefix
2. Applies ALL hard constraints (no scoring):
   - Distance within patient's max travel distance
   - Therapist not in patient's exclusion list
   - All patient preferences must match or be null
   - All therapist preferences must match or be null
3. Selects oldest patients first (by search creation date)
4. Creates inquiry with configurable size (1-6 patients by default)

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/therapeutenanfragen/erstellen-fuer-therapeut" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "plz_prefix": "52",
    "sofort_senden": true
  }'
```

## POST /therapeutenanfragen/{id}/senden

**Description:** Send an unsent anfrage via email or phone call.

**No request body required.**

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/therapeutenanfragen/101/senden"
```

**Success Response (Email):**
```json
{
  "message": "Anfrage sent successfully",
  "anfrage_id": 101,
  "communication_type": "email",
  "email_id": 456,
  "phone_call_id": null,
  "sent_date": "2025-06-15T14:30:00"
}
```

**Success Response (Phone Call):**
```json
{
  "message": "Anfrage sent successfully", 
  "anfrage_id": 101,
  "communication_type": "phone_call",
  "email_id": null,
  "phone_call_id": 789,
  "sent_date": "2025-06-15T14:30:00"
}
```

## PUT /therapeutenanfragen/{id}/antwort

**Description:** Record therapist response.

**Example Request:**
```bash
curl -X PUT "http://localhost:8003/api/therapeutenanfragen/101/antwort" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_responses": {
      "1": "angenommen",
      "5": "abgelehnt_Kapazitaet",
      "8": "angenommen",
      "12": "abgelehnt_nicht_geeignet"
    },
    "notizen": "Can take 2 patients starting next month"
  }'
```

## DELETE /therapeutenanfragen/{id}

**Description:** Delete a therapeutenanfrage and all related TherapeutAnfragePatient entries (cascade delete).

**Example Request:**
```bash
curl -X DELETE "http://localhost:8003/api/therapeutenanfragen/101"
```

**Example Response:**
```json
{
  "message": "Therapeutenanfrage deleted successfully"
}
```