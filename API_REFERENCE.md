# API Reference - Psychotherapy Matching Platform (BACKEND-ALIGNED VERSION)

**Single Source of Truth for All API Integration**

Last Updated: July 2025

## Overview

This document contains the complete API specification for all microservices. All field names use German terminology and flat structure (no nested objects).

**Base URLs:**
- Patient Service: `http://localhost:8001/api`
- Therapist Service: `http://localhost:8002/api`
- Matching Service: `http://localhost:8003/api`
- Communication Service: `http://localhost:8004/api`
- Geocoding Service: `http://localhost:8005/api`

**Authentication:** None (internal administrative interface)

## Dynamic Configuration

The following values are configurable via environment variables and will be reflected in error messages and validation:

- **MIN_ANFRAGE_SIZE**: Minimum patients per inquiry (default: 1)
- **MAX_ANFRAGE_SIZE**: Maximum patients per inquiry (default: 6) 
- **PLZ_MATCH_DIGITS**: PLZ prefix length for filtering (default: 2)
- **FOLLOW_UP_THRESHOLD_DAYS**: Days before follow-up needed (default: 7)
- **DEFAULT_PHONE_CALL_TIME**: Default time for phone calls (default: "12:00")

Error messages and validation will reflect the configured values, not hardcoded constants.

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
  - `psychotherapeutische_sprechstunde` = true
  - Once set, it never changes (even if checkboxes are later unchecked)
  
- **`letzter_kontakt`**: Automatically updated to today's date when:
  - An email is sent to the patient (status = "Gesendet")
  - The patient responds to an email (antwort_erhalten = true)
  - A phone call with the patient is completed (status = "abgeschlossen")

**Note:** Any attempt to set these fields via POST or PUT requests will be silently ignored.

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

### Preferred Diagnoses (bevorzugte_diagnosen)

**Format:** Always returns array, never null
```json
{
  "bevorzugte_diagnosen": ["F32", "F41", "F43"]
}
```

**Empty case:**
```json
{
  "bevorzugte_diagnosen": []
}
```

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
```
"offen"
"auf_der_Suche"
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
- Therapists: `psychotherapieverfahren` field
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
# Filter by status
curl "http://localhost:8001/api/patients?status=auf_der_Suche&page=1&limit=20"

# Search for patients
curl "http://localhost:8001/api/patients?search=mueller"

# Combine search and status filter
curl "http://localhost:8001/api/patients?search=anna&status=auf_der_Suche"
```

**Example Response (COMPLETE - ALL FIELDS):**
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
      "diagnose": "F32.1",
      "symptome": "Niedergeschlagenheit, Schlafstörungen, Antriebslosigkeit",
      "erfahrung_mit_psychotherapie": false,
      "letzte_sitzung_vorherige_psychotherapie": null,
      "vertraege_unterschrieben": true,
      "psychotherapeutische_sprechstunde": true,
      "startdatum": "2025-01-15",
      "erster_therapieplatz_am": null,
      "funktionierender_therapieplatz_am": null,
      "status": "auf_der_Suche",
      "empfehler_der_unterstuetzung": "Hausarzt",
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

## POST /patients

**Description:** Create a new patient.

**Required Fields:**
- `anrede` (string) - Must be one of: "Herr", "Frau"
- `geschlecht` (string) - Must be one of: "männlich", "weiblich", "divers", "keine_Angabe"
- `vorname` (string)
- `nachname` (string)

**All Optional Fields (COMPLETE LIST):**

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
- `diagnose` (string)
- `symptome` (string)
- `erfahrung_mit_psychotherapie` (boolean)
- `letzte_sitzung_vorherige_psychotherapie` (string, YYYY-MM-DD)

**Process Status:**
- `vertraege_unterschrieben` (boolean)
- `psychotherapeutische_sprechstunde` (boolean)
- ~~`startdatum`~~ **AUTOMATIC** - Set automatically when both checkboxes above are true
- `status` (string, see enum values)
- `empfehler_der_unterstuetzung` (string)
- `erster_therapieplatz_am` (string, YYYY-MM-DD)
- `funktionierender_therapieplatz_am` (string, YYYY-MM-DD)

**Availability:**
- `zeitliche_verfuegbarkeit` (object, see format above)
- `raeumliche_verfuegbarkeit` (object, see format above)
- `verkehrsmittel` (string)

**Preferences:**
- `offen_fuer_gruppentherapie` (boolean)
- `offen_fuer_diga` (boolean)
- ~~`letzter_kontakt`~~ **AUTOMATIC** - Updated via communication events

**Therapist Preferences:**
- `ausgeschlossene_therapeuten` (array of integers)
- `bevorzugtes_therapeutengeschlecht` (string, see enum)
- `bevorzugtes_therapieverfahren` (string, **SINGLE VALUE** - see enum)

**Example Request (Complete):**
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
    "diagnose": "F41.1",
    "symptome": "Angstgefühle, Panikattacken, Herzrasen",
    "erfahrung_mit_psychotherapie": true,
    "letzte_sitzung_vorherige_psychotherapie": "2021-08-15",
    "vertraege_unterschrieben": false,
    "psychotherapeutische_sprechstunde": false,
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
  "symptome": "Angstgefühle, Panikattacken, Herzrasen",
  "erfahrung_mit_psychotherapie": true,
  "letzte_sitzung_vorherige_psychotherapie": "2021-08-15",
  "bevorzugtes_therapieverfahren": "Verhaltenstherapie",
  "startdatum": null,
  "letzter_kontakt": null,
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
```

**Validation Error Examples:**
```json
{
  "message": "Invalid therapy method 'Psychoanalyse'. Valid values: egal, Verhaltenstherapie, tiefenpsychologisch_fundierte_Psychotherapie"
}
```

```json
{
  "message": "Invalid anrede 'Dr.'. Valid values: Herr, Frau"
}
```

```json
{
  "message": "Invalid geschlecht 'Männlich'. Valid values: männlich, weiblich, divers, keine_Angabe"
}
```

## PUT /patients/{id}

**Description:** Update an existing patient.

**Accepts all fields from POST request as optional parameters, except:**
- `startdatum` - Automatically managed
- `letzter_kontakt` - Automatically managed

**Example Request:**
```bash
curl -X PUT "http://localhost:8001/api/patients/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_Therapie",
    "funktionierender_therapieplatz_am": "2025-06-15",
    "bevorzugtes_therapieverfahren": "tiefenpsychologisch_fundierte_Psychotherapie"
  }'
```

**Example Response:**
```json
{
  "id": 1,
  "anrede": "Frau",
  "geschlecht": "weiblich",
  "vorname": "Anna",
  "nachname": "Müller",
  "status": "in_Therapie",
  "funktionierender_therapieplatz_am": "2025-06-15",
  "letzter_kontakt": "2025-06-18",
  "bevorzugtes_therapieverfahren": "tiefenpsychologisch_fundierte_Psychotherapie",
  "updated_at": "2025-06-18"
}
```

## DELETE /patients/{id}

**Description:** Delete a patient.

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
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Search Behavior:**
- Searches across `vorname`, `nachname` fields with case-insensitive partial matching
- For `psychotherapieverfahren`, checks if search term matches any part of the enum values
- Results include all therapists where ANY of the searched fields contain the search term

**Example Request:**
```bash
# Filter by status and availability
curl "http://localhost:8002/api/therapists?status=aktiv&potenziell_verfuegbar=true"

# Search for therapists
curl "http://localhost:8002/api/therapists?search=weber"

# Search for therapy method
curl "http://localhost:8002/api/therapists?search=verhaltens"

# Combine search and filters
curl "http://localhost:8002/api/therapists?search=schmidt&status=aktiv"
```

**Example Response (COMPLETE - ALL FIELDS):**
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

## POST /therapists

**Description:** Create a new therapist.

**Required Fields:**
- `anrede` (string) - Must be one of: "Herr", "Frau"
- `geschlecht` (string) - Must be one of: "männlich", "weiblich", "divers", "keine_Angabe"
- `vorname` (string)
- `nachname` (string)

**All Optional Fields (COMPLETE LIST):**

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
- `psychotherapieverfahren` (string, **SINGLE VALUE** - see enum, default: "egal")
- `zusatzqualifikationen` (string)
- `besondere_leistungsangebote` (string)

**Contact History:**
- `letzter_kontakt_email` (string, YYYY-MM-DD)
- `letzter_kontakt_telefon` (string, YYYY-MM-DD)
- `letztes_persoenliches_gespraech` (string, YYYY-MM-DD)

**Availability:**
- `potenziell_verfuegbar` (boolean)
- `potenziell_verfuegbar_notizen` (string)
- `ueber_curavani_informiert` (boolean)

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

**Example Response:**
```json
{
  "id": 5,
  "anrede": "Herr",
  "geschlecht": "männlich",
  "vorname": "Michael",
  "nachname": "Becker",
  "email": "m.becker@therapie.de",
  "psychotherapieverfahren": "tiefenpsychologisch_fundierte_Psychotherapie",
  "bevorzugte_diagnosen": ["F32", "F33"],
  "fremdsprachen": [],
  "telefonische_erreichbarkeit": {},
  "arbeitszeiten": {},
  "status": "aktiv",
  "potenziell_verfuegbar": true,
  "ueber_curavani_informiert": false,
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
```

**Validation Error Examples:**
```json
{
  "message": "Invalid therapy method 'Systemische Therapie'. Valid values: egal, Verhaltenstherapie, tiefenpsychologisch_fundierte_Psychotherapie"
}
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
    "psychotherapieverfahren": "Verhaltenstherapie"
  }'
```

## DELETE /therapists/{id}

**Description:** Delete a therapist.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8002/api/therapists/1"
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
      "aktive_anfragen": 3,
      "gesamt_anfragen": 8,
      "ausgeschlossene_therapeuten_anzahl": 2
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
    "diagnose": "F32.1",
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

**Patient Data Validation:**
Before creating a platzsuche, the patient must have the following required data:

**Required String Fields (non-empty):**
- `geschlecht`
- `diagnose`
- `symptome`
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

**Validation Error Response:**
```json
{
  "message": "Cannot create platzsuche: Patient field 'diagnose' is required and cannot be empty",
  "patient_id": 123
}
```

**Duplicate Error Response:**
```json
{
  "message": "Patient already has an active search",
  "search_id": 5
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

**Example Request (Update Status):**
```bash
curl -X PUT "http://localhost:8003/api/platzsuchen/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "pausiert",
    "notizen": "Patient temporarily unavailable"
  }'
```

**Example Request (Add Excluded Therapists):**
```bash
curl -X PUT "http://localhost:8003/api/platzsuchen/1" \
  -H "Content-Type: application/json" \
  -d '{
    "ausgeschlossene_therapeuten": [123, 456, 789]
  }'
```

**Success Response:**
```json
{
  "message": "Patient search updated successfully",
  "id": 1
}
```

**Invalid Status Transition Response:**
```json
{
  "message": "Invalid status transition from erfolgreich to aktiv"
}
```

**Invalid Status Value Response:**
```json
{
  "message": "Invalid status 'completed'. Valid values: ['aktiv', 'erfolgreich', 'pausiert', 'abgebrochen']"
}
```

## DELETE /platzsuchen/{id}

**Description:** Delete a patient search and all related records.

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

**Sorting Order (Email Priority):**
1. Available AND informed about Curavani WITH email
2. Available AND NOT informed about Curavani WITH email  
3. Not available AND informed about Curavani WITH email
4. Others WITH email (alphabetically by name)
5. Available AND informed about Curavani WITHOUT email
6. Available AND NOT informed about Curavani WITHOUT email
7. Not available AND informed about Curavani WITHOUT email
8. Others WITHOUT email (alphabetically by name)

**Note:** Therapists with email addresses are always prioritized over those without email addresses within each availability/information tier.

**Example Request:**
```bash
curl "http://localhost:8003/api/therapeuten-zur-auswahl?plz_prefix=52"
```

**Example Response:**
```json
{
  "plz_prefix": "52",
  "total": 15,
  "data": [
    {
      "id": 123,
      "anrede": "Frau",
      "geschlecht": "weiblich",
      "titel": "Dr. med.",
      "vorname": "Maria",
      "nachname": "Weber",
      "strasse": "Praxis Str. 12",
      "plz": "52062",
      "ort": "Aachen",
      "telefon": "+49 241 98765432",
      "email": "dr.weber@praxis.de",
      "potenziell_verfuegbar": true,
      "ueber_curavani_informiert": true,
      "naechster_kontakt_moeglich": null,
      "bevorzugte_diagnosen": ["F32", "F41"],
      "psychotherapieverfahren": "Verhaltenstherapie",
      "fremdsprachen": [],
      "telefonische_erreichbarkeit": {},
      "arbeitszeiten": {}
    }
  ]
}
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

**Example Response:**
```json
{
  "data": [
    {
      "id": 101,
      "therapist_id": 123,
      "therapeuten_name": "Dr. Max Mustermann",
      "erstellt_datum": "2025-06-07",
      "gesendet_datum": "2025-06-07",
      "antwort_datum": null,
      "tage_seit_versand": 2,
      "antworttyp": null,
      "anfragegroesse": 4,
      "angenommen_anzahl": 0,
      "abgelehnt_anzahl": 0,
      "keine_antwort_anzahl": 0,
      "nachverfolgung_erforderlich": false,
      "antwort_vollstaendig": false
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 150,
  "summary": {
    "total_anfragen": 150,
    "unsent_anfragen": 15,
    "pending_responses": 38,
    "needing_follow_up": 12
  }
}
```

## GET /therapeutenanfragen/{id}

**Description:** Get inquiry details with patient list.

**Example Request:**
```bash
curl "http://localhost:8003/api/therapeutenanfragen/101"
```

**Example Response:**
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
        "diagnose": "F32.1"
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

**Example Response:**
```json
{
  "message": "Created anfrage with 4 patients",
  "anfrage_id": 101,
  "therapist_id": 123,
  "anfragegroesse": 4,
  "patient_ids": [1, 5, 8, 12],
  "gesendet": true
}
```

**Error Response (Invalid PLZ):**
```json
{
  "message": "Invalid PLZ prefix. Must be exactly {PLZ_MATCH_DIGITS} digits."
}
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

**Behavior:**
- If therapist has an email address: Creates and sends email (existing behavior)
- If therapist has no email address: Creates phone call with `therapeutenanfrage_id` link for follow-up
- Phone calls are automatically scheduled using therapist's `telefonische_erreichbarkeit` or default time

**Response Fields:**
- `communication_type` (string): Either "email" or "phone_call" indicating how the anfrage was sent
- `email_id` (integer|null): ID of created email if sent via email, null if sent via phone call
- `phone_call_id` (integer|null): ID of created phone call if sent via phone call, null if sent via email
- `sent_date` (string): ISO datetime when the communication was initiated

**Error Response (Already Sent):**
```json
{
  "message": "Anfrage already sent",
  "sent_date": "2025-06-14T10:00:00"
}
```

**Error Response (Not Found):**
```json
{
  "message": "Anfrage 999 not found"
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

**Example Response:**
```json
{
  "message": "Anfrage response recorded successfully",
  "anfrage_id": 101,
  "response_type": "teilweise_Annahme",
  "angenommene_patienten": [
    {"patient_id": 1, "platzsuche_id": 10},
    {"patient_id": 8, "platzsuche_id": 23}
  ],
  "antwort_zusammenfassung": {
    "accepted": 2,
    "rejected": 2,
    "no_response": 0
  }
}
```

## DELETE /therapeutenanfragen/{id}

**Description:** Delete a therapeutenanfrage and all related records.

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

---

# Communication Service API

## GET /emails

**Description:** Retrieve all emails with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `patient_id` (optional): Filter by patient
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

**IMPORTANT:** Emails are ALWAYS created with status "Entwurf" (draft). The status field cannot be set via API. To send emails, you must update the status to "In_Warteschlange" after creation.

**Required Fields:**
- Either `therapist_id` (integer) OR `patient_id` (integer) - exactly one must be provided
- `betreff` (string)
- Either `inhalt_markdown` (string) OR `inhalt_html` (string)
- `empfaenger_email` (string)
- `empfaenger_name` (string)

**Optional Fields:**
- `inhalt_text` (string) - plain text version
- `absender_email` (string) - defaults to system email
- `absender_name` (string) - defaults to system name
- `add_legal_footer` (boolean) - defaults to true

**Validation Rules:**
- Cannot specify both `therapist_id` and `patient_id`
- Must specify at least one of `therapist_id` or `patient_id`
- Must provide either `inhalt_markdown` or `inhalt_html`

**Important Notes:**
1. **Always Draft**: All emails are created as drafts regardless of any status parameter
2. **Markdown Processing**: URLs in markdown content are automatically detected and converted to clickable links
3. **Legal Footer**: Added by default unless explicitly disabled

**Example Requests:**

### Create Email Draft
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "betreff": "Update zu Ihrer Therapieplatzsuche",
    "inhalt_markdown": "# Update\n\nSehr geehrter Herr Mustermann...",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "Max Mustermann"
  }'
```

**Example Response:**
```json
{
  "id": 3,
  "patient_id": 30,
  "therapist_id": null,
  "betreff": "Update zu Ihrer Therapieplatzsuche",
  "empfaenger_email": "patient@example.com",
  "empfaenger_name": "Max Mustermann",
  "status": "Entwurf",
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
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
- `patient_id` (optional): Filter by patient
- `therapeutenanfrage_id` (optional): Filter by therapeutenanfrage (NEW)
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
      "status": "geplant",
      "tatsaechliches_datum": null,
      "tatsaechliche_zeit": null,
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

## POST /phone-calls

**Description:** Schedule a new phone call. Must specify either `therapist_id` OR `patient_id`, not both.

**Required Fields:**
- Either `therapist_id` (integer) OR `patient_id` (integer) - exactly one must be provided

**Optional Fields:**
- `therapeutenanfrage_id` (integer) - Link to therapeutenanfrage (NEW)
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
- `therapeutenanfrage_id` (integer) - Link to therapeutenanfrage (NEW)
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

**Description:** Send a system notification email directly without database storage.

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
    "message": "Failed to import patient data: Invalid date format in row 15",
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

**Error Response:**
```json
{
  "status": "error",
  "error": "Geocoding failed"
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

**Example Response:**
```json
{
  "display_name": "Berlin, Deutschland",
  "address_components": {
    "city": "Berlin",
    "country": "Deutschland",
    "postcode": "10117"
  },
  "latitude": 52.5200,
  "longitude": 13.4050,
  "source": "nominatim",
  "status": "success"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Reverse geocoding failed"
}
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

**Calculation Hierarchy:**
1. **OSRM Routing**: Attempts to get precise route with travel time
2. **Haversine Distance**: Falls back to straight-line distance if routing fails
3. **PLZ Centroids**: Uses postal code centroids for German addresses if coordinates unavailable

**Example Requests:**
```bash
# Using addresses
curl "http://localhost:8005/api/calculate-distance?origin=Berlin&destination=Munich&travel_mode=car"

# Using coordinates
curl "http://localhost:8005/api/calculate-distance?origin_lat=52.5200&origin_lon=13.4050&destination_lat=48.1351&destination_lon=11.5820"

# With cache bypass
curl "http://localhost:8005/api/calculate-distance?origin=Berlin&destination=Munich&no_cache=true"
```

**Example Response (OSRM Success):**
```json
{
  "distance_km": 585.2,
  "status": "success",
  "source": "osrm",
  "travel_mode": "car",
  "route_available": true
}
```

**Example Response (Haversine Fallback):**
```json
{
  "distance_km": 504.3,
  "status": "partial",
  "source": "haversine",
  "travel_mode": "car",
  "route_available": false
}
```

**Example Response (PLZ Fallback):**
```json
{
  "distance_km": 510.1,
  "status": "success",
  "source": "plz_centroids",
  "travel_mode": "car",
  "route_available": false,
  "note": "Approximate distance based on postal code areas"
}
```

**Error Response:**
```json
{
  "distance_km": 0,
  "status": "error",
  "error": "Could not resolve coordinates"
}
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

**Example Response:**
```json
{
  "distance_km": 475.8,
  "status": "success",
  "source": "plz_centroids",
  "origin_centroid": {
    "latitude": 50.7753,
    "longitude": 6.0839
  },
  "destination_centroid": {
    "latitude": 52.5200,
    "longitude": 13.4050
  }
}
```

**Error Responses:**
```json
{
  "status": "error",
  "error": "Invalid origin PLZ format: ABC12"
}
```

```json
{
  "status": "error",
  "error": "One or both PLZ codes not found"
}
```

**PLZ Validation:**
- Must be exactly 5 digits
- Must be within valid German PLZ range (01001-99998)
- Both PLZ codes must exist in the centroids database

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

# Key Changes from Previous Version

## 🆕 **Latest Updates (December 2025)**

### ✅ **PUT /platzsuchen/{id} Endpoint:**
- Update patient search including status changes
- Supports status transitions with validation
- Can update notes and excluded therapists list
- Publishes status change events via Kafka

### Status Transition Rules:
- `aktiv` → `pausiert`, `erfolgreich`, `abgebrochen`
- `pausiert` → `aktiv`, `abgebrochen`
- `erfolgreich` → no transitions (terminal state)
- `abgebrochen` → no transitions (terminal state)

## 🆕 **Previous Updates (July 2025)**

### ✅ **DELETE Endpoints Added:**
- `DELETE /api/therapeutenanfragen/{id}` - Delete therapeutenanfrage and related records
- `DELETE /api/platzsuchen/{id}` - Actually delete record (not just cancel)

### 📞 **Phone Call Enhancements:**
- Added `therapeutenanfrage_id` field to phone calls
- Links phone calls to specific anfragen for follow-up tracking
- Updated all phone call endpoints to support anfrage linking

### ✅ **Patient Validation for Platzsuche:**
Enhanced validation when creating patient searches:
- Required string fields must be non-empty
- Required boolean fields must be explicitly set  
- Conditional validation for therapy experience
- Time availability must have at least one valid slot

### 📧 **Send Anfrage Endpoint:**
- New `POST /api/therapeutenanfragen/{id}/senden` endpoint
- Sends unsent anfragen via email
- Automatic email queuing and sending

### ⚙️ **Follow-up Configuration:**
- New environment variables for follow-up scheduling
- `FOLLOW_UP_THRESHOLD_DAYS` (default: 7)
- `DEFAULT_PHONE_CALL_TIME` (default: "12:00")
- Automatic daily scheduling at 09:00

## 🔍 **Search Functionality (Previous Update):**

### Patient Service:
- Added `search` query parameter to `GET /patients`
- Searches across `vorname`, `nachname`, and `email` fields
- Case-insensitive partial matching
- Can be combined with existing `status` filter

### Therapist Service:
- Added `search` query parameter to `GET /therapists`
- Searches across `vorname`, `nachname`, and `psychotherapieverfahren` fields
- Case-insensitive partial matching for text fields
- Special handling for enum field `psychotherapieverfahren`
- Can be combined with existing `status` and `potenziell_verfuegbar` filters

## 🆕 **Health Check Endpoints:**
- All services now expose `/health` endpoint
- Returns service name and health status

## 📧 **System Messages Endpoint:**
- New endpoint `POST /api/system-messages` in Communication Service
- Sends system notifications directly without database storage
- Used for error notifications and system alerts

## ⚠️ **Email Status Clarification:**
- **IMPORTANT:** The `status` field CANNOT be set when creating emails via API
- All emails are created with status "Entwurf" (draft)
- Previous documentation incorrectly suggested status could be set to queue emails

## 📞 **Phone Call Scheduling Clarification:**
- Automatic scheduling is simplified - just returns 10:00 or 14:00 slots
- Not the sophisticated availability-based scheduling suggested in old docs

## 🔧 **Model Updates (Previous):**

### 🆕 **Therapist psychotherapieverfahren Change:**
- Changed from JSONB array to single ENUM field
- Now uses same enum as patients: "egal", "Verhaltenstherapie", "tiefenpsychologisch_fundierte_Psychotherapie"
- Default value: "egal"
- Both patients and therapists now have single therapy method preference/offering

### ✂️ **Removed Fields (16 total):**

**Medical History fields removed:**
- psychotherapieerfahrung
- stationaere_behandlung
- berufliche_situation
- familienstand
- aktuelle_psychische_beschwerden
- beschwerden_seit
- bisherige_behandlungen
- relevante_koerperliche_erkrankungen
- aktuelle_medikation
- aktuelle_belastungsfaktoren
- unterstuetzungssysteme

**Therapy Goals fields removed:**
- anlass_fuer_die_therapiesuche
- erwartungen_an_die_therapie
- therapieziele
- fruehere_therapieerfahrungen

### 🔄 **Modified Fields:**

1. **`erfahrung_mit_psychotherapie`**: Changed from Text to Boolean (nullable, no default)
2. **`bevorzugtes_therapieverfahren`**: Changed from ARRAY to single ENUM field (default: "egal")

### ➕ **New Field:**

- **`letzte_sitzung_vorherige_psychotherapie`**: Date field for last session of previous psychotherapy

## 🆕 **Previous New Enums Added:**

1. **Anrede (Salutation)** - Required field with two values:
   - `"Herr"`
   - `"Frau"`

2. **Geschlecht (Gender)** - Required field with four values:
   - `"männlich"`
   - `"weiblich"`
   - `"divers"`
   - `"keine_Angabe"`

## ✅ **Previous Fixed Issues:**

1. **Patient Array Fields**: `bevorzugtes_therapieverfahren` now always returns array, never null (Migration 003)
2. **Therapist JSONB Fields**: All JSONB fields now return proper defaults instead of null (Migration 004 + API fixes):
   - Array fields (`fremdsprachen`, `bevorzugte_diagnosen`) → `[]`
   - Object fields (`telefonische_erreichbarkeit`, `arbeitszeiten`) → `{}`
3. **Date Format**: Using simple date format "2025-06-22" instead of ISO timestamps
4. **Time Format**: Using German day names with string arrays `["09:00-12:00"]`
5. **Field Names**: All German field names maintained consistently
6. **Response Structure**: Matches actual backend implementation

## 🚀 **Automatic Field Management:**

### Phase 1: Automatic startdatum
- `startdatum` is now automatically set when both `vertraege_unterschrieben` and `psychotherapeutische_sprechstunde` are true
- Cannot be manually set via API - any attempts are silently ignored
- Once set, it never changes

### Phase 2: Automatic letzter_kontakt  
- `letzter_kontakt` is automatically updated via Kafka events when communication occurs
- Updated when emails are sent, responses received, or phone calls completed
- Cannot be manually set via API - any attempts are silently ignored

### Phase 3: bevorzugtes_therapieverfahren Validation
- Now a single enum field (not array)
- Only accepts values: "egal", "Verhaltenstherapie", "tiefenpsychologisch_fundierte_Psychotherapie" 
- Returns 400 error with clear message for invalid values

### Phase 4: Anrede and Geschlecht Enums
- Both fields are now required for both patients and therapists
- Strict validation against allowed enum values
- Clear error messages in English when validation fails

### Phase 5: Follow-up Automation
- Daily automatic scheduling of follow-up phone calls at 09:00
- Configurable threshold days for follow-up requirement
- Automatic linking of phone calls to therapeutenanfragen

**Note:** This API reference now accurately reflects the backend implementation after all database migrations, automatic field management, and latest feature additions including DELETE endpoints, enhanced phone call tracking, patient validation, and the previously undocumented PUT /platzsuchen/{id} endpoint.