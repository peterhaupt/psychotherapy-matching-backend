# API Reference - Psychotherapy Matching Platform

**Single Source of Truth for All API Integration**

Last Updated: June 2025

## Overview

This document contains the complete API specification for all microservices. All field names use German terminology and flat structure (no nested objects).

**Base URLs:**
- Patient Service: `http://localhost:8001/api`
- Therapist Service: `http://localhost:8002/api`
- Matching Service: `http://localhost:8003/api`
- Communication Service: `http://localhost:8004/api`
- Geocoding Service: `http://localhost:8005/api`

**Authentication:** None (internal administrative interface)

## Common Response Patterns

### Success Response
```json
{
  "id": 1,
  "vorname": "Anna",
  "nachname": "Müller",
  "created_at": "2025-06-10T10:00:00",
  "updated_at": "2025-06-10T10:00:00"
}
```

### Error Response
```json
{
  "message": "Validation error description"
}
```

### Pagination Response
```json
{
  "data": [...],
  "page": 1,
  "limit": 20,
  "total": 150
}
```

## Enum Values

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

# Patient Service API

## GET /patients

**Description:** Retrieve all patients with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by patient status
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
curl "http://localhost:8001/api/patients?status=auf_der_Suche&page=1&limit=20"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "anrede": "Frau",
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
      "vertraege_unterschrieben": true,
      "psychotherapeutische_sprechstunde": true,
      "startdatum": "2025-01-15",
      "erster_therapieplatz_am": null,
      "funktionierender_therapieplatz_am": null,
      "status": "auf_der_Suche",
      "empfehler_der_unterstuetzung": "Hausarzt",
      "zeitliche_verfuegbarkeit": {
        "monday": [{"start": "09:00", "end": "17:00"}],
        "tuesday": [{"start": "09:00", "end": "17:00"}]
      },
      "raeumliche_verfuegbarkeit": {
        "max_km": 30
      },
      "verkehrsmittel": "Auto",
      "offen_fuer_gruppentherapie": false,
      "offen_fuer_diga": false,
      "ausgeschlossene_therapeuten": [45, 67],
      "bevorzugtes_therapeutengeschlecht": "Weiblich",
      "letzter_kontakt": "2025-06-15",
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

**Example Response:**
```json
{
  "id": 1,
  "anrede": "Frau",
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
  "vertraege_unterschrieben": true,
  "psychotherapeutische_sprechstunde": true,
  "startdatum": "2025-01-15",
  "status": "auf_der_Suche",
  "zeitliche_verfuegbarkeit": {
    "monday": [{"start": "09:00", "end": "17:00"}]
  },
  "raeumliche_verfuegbarkeit": {
    "max_km": 30
  },
  "verkehrsmittel": "Auto",
  "offen_fuer_gruppentherapie": false,
  "bevorzugtes_therapeutengeschlecht": "Weiblich",
  "ausgeschlossene_therapeuten": [45, 67],
  "letzter_kontakt": "2025-06-15",
  "created_at": "2025-05-01",
  "updated_at": "2025-06-01"
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
      "date": "2025-06-15T10:30:00",
      "subject": "Update zu Ihrer Therapieplatzsuche",
      "status": "Gesendet",
      "response_received": false,
      "data": {
        "id": 45,
        "patient_id": 30,
        "betreff": "Update zu Ihrer Therapieplatzsuche",
        "empfaenger_email": "max.mustermann@email.com",
        "status": "Gesendet",
        "gesendet_am": "2025-06-15T10:30:00"
      }
    },
    {
      "type": "phone_call",
      "id": 12,
      "date": "2025-06-10 14:00",
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
- `vorname` (string)
- `nachname` (string)

**Example Request:**
```bash
curl -X POST "http://localhost:8001/api/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "anrede": "Herr",
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
    "vertraege_unterschrieben": false,
    "zeitliche_verfuegbarkeit": {
      "monday": [{"start": "18:00", "end": "20:00"}],
      "wednesday": [{"start": "18:00", "end": "20:00"}]
    },
    "raeumliche_verfuegbarkeit": {
      "max_km": 25
    },
    "verkehrsmittel": "ÖPNV",
    "bevorzugtes_therapeutengeschlecht": "Egal",
    "offen_fuer_gruppentherapie": true,
    "ausgeschlossene_therapeuten": []
  }'
```

**Example Response:**
```json
{
  "id": 4,
  "anrede": "Herr",
  "vorname": "Thomas",
  "nachname": "Schmidt",
  "strasse": "Berliner Str. 45",
  "plz": "80331",
  "ort": "München",
  "email": "thomas.schmidt@email.com",
  "telefon": "+49 89 87654321",
  "status": "offen",
  "created_at": "2025-06-10",
  "updated_at": "2025-06-10"
}
```

## PUT /patients/{id}

**Description:** Update an existing patient.

**Example Request:**
```bash
curl -X PUT "http://localhost:8001/api/patients/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_Therapie",
    "funktionierender_therapieplatz_am": "2025-06-15",
    "letzter_kontakt": "2025-06-18"
  }'
```

**Example Response:**
```json
{
  "id": 1,
  "vorname": "Anna",
  "nachname": "Müller",
  "status": "in_Therapie",
  "funktionierender_therapieplatz_am": "2025-06-15",
  "letzter_kontakt": "2025-06-18",
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
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example Request:**
```bash
curl "http://localhost:8002/api/therapists?status=aktiv&potenziell_verfuegbar=true"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "anrede": "Dr.",
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
      "geschlecht": "weiblich",
      "telefonische_erreichbarkeit": {
        "monday": [{"start": "09:00", "end": "12:00"}],
        "wednesday": [{"start": "14:00", "end": "16:00"}]
      },
      "fremdsprachen": ["Englisch", "Französisch"],
      "psychotherapieverfahren": ["Verhaltenstherapie", "Tiefenpsychologie"],
      "zusatzqualifikationen": "Traumatherapie, EMDR",
      "besondere_leistungsangebote": "Online-Therapie verfügbar",
      "letzter_kontakt_email": "2025-05-15",
      "letzter_kontakt_telefon": null,
      "letztes_persoenliches_gespraech": "2025-04-10",
      "potenziell_verfuegbar": true,
      "potenziell_verfuegbar_notizen": "Ab Juli 2025 verfügbar",
      "naechster_kontakt_moeglich": "2025-07-01",
      "bevorzugte_diagnosen": ["F32", "F41", "F43"],
      "alter_min": 18,
      "alter_max": 65,
      "geschlechtspraeferenz": "Egal",
      "arbeitszeiten": {
        "monday": [{"start": "08:00", "end": "18:00"}],
        "tuesday": [{"start": "08:00", "end": "18:00"}]
      },
      "bevorzugt_gruppentherapie": false,
      "status": "aktiv",
      "sperrgrund": null,
      "sperrdatum": null,
      "created_at": "2025-01-10T09:00:00",
      "updated_at": "2025-06-01T16:20:00"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 85
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
      "date": "2025-06-18T14:30:00",
      "subject": "Therapieanfrage für mehrere Patienten",
      "status": "Gesendet",
      "response_received": true,
      "data": {
        "id": 78,
        "therapist_id": 123,
        "betreff": "Therapieanfrage für mehrere Patienten",
        "empfaenger_email": "dr.weber@praxis.de",
        "status": "Gesendet",
        "gesendet_am": "2025-06-18T14:30:00",
        "antwort_erhalten": true,
        "antwortdatum": "2025-06-19T09:00:00"
      }
    },
    {
      "type": "phone_call",
      "id": 23,
      "date": "2025-06-15 10:00",
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
- `vorname` (string)
- `nachname` (string)

**Example Request:**
```bash
curl -X POST "http://localhost:8002/api/therapists" \
  -H "Content-Type: application/json" \
  -d '{
    "anrede": "Dr.",
    "titel": "Dr. phil.",
    "vorname": "Michael",
    "nachname": "Becker",
    "strasse": "Therapie Zentrum 5",
    "plz": "80331",
    "ort": "München",
    "telefon": "+49 89 11223344",
    "email": "m.becker@therapie.de",
    "kassensitz": true,
    "geschlecht": "männlich",
    "psychotherapieverfahren": ["Tiefenpsychologie"],
    "potenziell_verfuegbar": true,
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
  "vorname": "Michael",
  "nachname": "Becker",
  "email": "m.becker@therapie.de",
  "status": "aktiv",
  "potenziell_verfuegbar": true,
  "created_at": "2025-06-10T11:00:00",
  "updated_at": "2025-06-10T11:00:00"
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
    "naechster_kontakt_moeglich": "2025-09-01"
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
- `min_bundles` (optional): Minimum bundle count
- `max_bundles` (optional): Maximum bundle count

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
      "created_at": "2025-06-07T10:00:00",
      "gesamt_angeforderte_kontakte": 25,
      "aktive_buendel": 3,
      "gesamt_buendel": 8,
      "ausgeschlossene_therapeuten_anzahl": 2
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 45
}
```

## GET /platzsuchen/{id}

**Description:** Get patient search details with bundle history.

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
  "created_at": "2025-06-07T10:00:00",
  "ausgeschlossene_therapeuten": [45, 67],
  "gesamt_angeforderte_kontakte": 25,
  "aktive_buendel": 3,
  "gesamt_buendel": 8,
  "buendel_verlauf": [
    {
      "bundle_id": 101,
      "therapist_id": 123,
      "therapeuten_name": "Dr. Schmidt",
      "position": 2,
      "status": "pending",
      "outcome": null,
      "sent_date": "2025-06-07T10:30:00",
      "response_date": null
    }
  ]
}
```

## POST /platzsuchen

**Description:** Create a new patient search.

**Required Fields:**
- `patient_id` (integer)

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/platzsuchen" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 123,
    "notizen": "Patient urgently needs therapy"
  }'
```

**Example Response:**
```json
{
  "id": 1,
  "patient_id": 123,
  "status": "aktiv",
  "created_at": "2025-06-07T10:00:00",
  "message": "Patient search created successfully"
}
```

## POST /platzsuchen/{id}/kontaktanfrage

**Description:** Request additional contacts for a patient search.

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/platzsuchen/1/kontaktanfrage" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_count": 10,
    "notizen": "Patient still searching"
  }'
```

**Example Response:**
```json
{
  "message": "Requested 10 additional contacts",
  "previous_total": 15,
  "new_total": 25,
  "search_id": 1
}
```

## GET /therapeutenanfragen

**Description:** Get all bundles with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `versand_status` (optional): "gesendet" or "ungesendet"
- `antwort_status` (optional): "beantwortet" or "ausstehend"
- `nachverfolgung_erforderlich` (optional): boolean
- `min_size` (optional): minimum bundle size
- `max_size` (optional): maximum bundle size

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
      "erstellt_datum": "2025-06-07T10:00:00",
      "gesendet_datum": "2025-06-07T10:30:00",
      "antwort_datum": null,
      "tage_seit_versand": 2,
      "antworttyp": null,
      "buendelgroesse": 4,
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
    "total_bundles": 150,
    "unsent_bundles": 15,
    "pending_responses": 38,
    "needing_follow_up": 12
  }
}
```

## GET /therapeutenanfragen/{id}

**Description:** Get bundle details with patient list.

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
  "erstellt_datum": "2025-06-07T10:00:00",
  "gesendet_datum": "2025-06-07T10:30:00",
  "antwort_datum": null,
  "tage_seit_versand": 2,
  "antworttyp": null,
  "buendelgroesse": 4,
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
      "search_created_at": "2025-05-01T08:00:00",
      "wartezeit_tage": 37,
      "status": "pending",
      "antwortergebnis": null,
      "antwortnotizen": null
    }
  ],
  "nachverfolgung_erforderlich": false
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
  "message": "Bundle response recorded successfully",
  "bundle_id": 101,
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

## POST /buendel/erstellen

**Description:** Triggers bundle creation for all eligible therapists.

**Example Request:**
```bash
curl -X POST "http://localhost:8003/api/buendel/erstellen" \
  -H "Content-Type: application/json" \
  -d '{
    "sofort_senden": false,
    "testlauf": false
  }'
```

**Example Response:**
```json
{
  "message": "Created 5 bundles",
  "buendel_erstellt": 5,
  "buendel_gesendet": 0,
  "buendel_ids": [101, 102, 103, 104, 105]
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
- `page` (optional): Page number
- `limit` (optional): Items per page

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
      "gesendet_am": "2025-06-08T10:30:00",
      "created_at": "2025-06-08T10:25:00",
      "updated_at": "2025-06-08T10:30:00"
    },
    {
      "id": 2,
      "therapist_id": null,
      "patient_id": 30,
      "betreff": "Update zu Ihrer Therapieplatzsuche",
      "empfaenger_email": "patient@example.com",
      "empfaenger_name": "Max Mustermann",
      "absender_email": "info@curavani.de",
      "absender_name": "Curavani Team",
      "status": "Gesendet",
      "antwort_erhalten": false,
      "gesendet_am": "2025-06-15T10:30:00",
      "created_at": "2025-06-15T10:25:00",
      "updated_at": "2025-06-15T10:30:00"
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
- `status` (string) - Controls whether email is saved as draft or queued for sending
  - `"Entwurf"` - Save as draft (will NOT be sent)
  - `"In_Warteschlange"` - Queue for immediate sending (will be sent within 60 seconds)
  - Default: `"Entwurf"` (if not specified)
  - Any other value returns 400 error
- `add_legal_footer` (boolean) - defaults to true

**Validation Rules:**
- Cannot specify both `therapist_id` and `patient_id`
- Must specify at least one of `therapist_id` or `patient_id`
- Must provide either `inhalt_markdown` or `inhalt_html`
- Only `"Entwurf"` and `"In_Warteschlange"` can be set via API

**Important Notes:**
1. If no `status` is provided, emails default to `"Entwurf"` (draft) for safety
2. Only `"Entwurf"` and `"In_Warteschlange"` can be set by users
3. System-managed statuses (`"Wird_gesendet"`, `"Gesendet"`, `"Fehlgeschlagen"`) cannot be set via API

**Example Requests:**

### Save Email as Draft
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "status": "Entwurf",
    "betreff": "Draft: Update zu Ihrer Therapieplatzsuche",
    "inhalt_markdown": "# Entwurf\n\nDieser Text wird als Entwurf gespeichert...",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "Max Mustermann"
  }'
```

### Send Email Immediately
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "status": "In_Warteschlange",
    "betreff": "Therapieanfrage für mehrere Patienten",
    "inhalt_markdown": "# Therapieanfrage\n\nSehr geehrte/r Dr. Schmidt...",
    "empfaenger_email": "doctor@example.com",
    "empfaenger_name": "Dr. Schmidt"
  }'
```

### Email to Therapist (with Markdown)
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "betreff": "Therapieanfrage für mehrere Patienten",
    "inhalt_markdown": "# Therapieanfrage\n\nSehr geehrte/r Dr. Schmidt,\n\nwir haben mehrere Patienten, die...\n\n## Patientenliste\n\n- Patient 1: Anna Müller\n- Patient 2: Max Mustermann\n\n**Bitte antworten Sie innerhalb von 7 Tagen.**",
    "empfaenger_email": "doctor@example.com",
    "empfaenger_name": "Dr. Schmidt"
  }'
```

### Email to Patient (with HTML)
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "betreff": "Update zu Ihrer Therapieplatzsuche",
    "inhalt_html": "<p>Gute Nachrichten! Wir haben einen Therapieplatz für Sie gefunden...</p>",
    "inhalt_text": "Gute Nachrichten! Wir haben einen Therapieplatz für Sie gefunden...",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "Max Mustermann",
    "add_legal_footer": false
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
  "created_at": "2025-06-10T12:00:00",
  "updated_at": "2025-06-10T12:00:00"
}
```

**Error Responses:**
```json
// Missing recipient
{
  "message": "Either therapist_id or patient_id is required"
}

// Both recipients specified
{
  "message": "Cannot specify both therapist_id and patient_id"
}

// Missing body content
{
  "message": "Either inhalt_markdown or inhalt_html is required"
}

// Invalid status
{
  "message": "Invalid status. Only 'Entwurf' or 'In_Warteschlange' allowed"
}
```

### Email Status Flow

1. **Draft Flow:**
   - Frontend sends with `status: "Entwurf"` or omits status
   - Email saved with "Entwurf" status
   - Email remains in system but is NOT sent
   - Can be edited/updated later

2. **Send Flow:**
   - Frontend sends with `status: "In_Warteschlange"`
   - Email saved with "In_Warteschlange" status
   - Background worker picks it up within 60 seconds
   - Status automatically changes: `In_Warteschlange` → `Wird_gesendet` → `Gesendet` (or `Fehlgeschlagen`)
   - `gesendet_am` timestamp is set upon successful sending

### Frontend Implementation Recommendations

1. **Send Button:** Set `status: "In_Warteschlange"`
2. **Save Draft Button:** Set `status: "Entwurf"` or omit status field
3. **Status Display:** Show appropriate UI based on email status:
   - `"Entwurf"` - Show as draft, allow editing
   - `"In_Warteschlange"` - Show as pending/queued
   - `"Wird_gesendet"` - Show as sending
   - `"Gesendet"` - Show as sent with timestamp
   - `"Fehlgeschlagen"` - Show as failed, allow retry

## PUT /emails/{id}

**Description:** Update email response information.

**Example Request:**
```bash
curl -X PUT "http://localhost:8004/api/emails/1" \
  -H "Content-Type: application/json" \
  -d '{
    "antwort_erhalten": true,
    "antwortdatum": "2025-06-09T14:00:00",
    "antwortinhalt": "Ich kann 2 Patienten aufnehmen."
  }'
```

**Example Response:**
```json
{
  "id": 1,
  "antwort_erhalten": true,
  "antwortdatum": "2025-06-09T14:00:00",
  "antwortinhalt": "Ich kann 2 Patienten aufnehmen.",
  "updated_at": "2025-06-10T12:05:00"
}
```

## DELETE /emails/{id}

**Description:** Delete an email.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8004/api/emails/1"
```

**Example Response:**
```json
{
  "message": "Email deleted successfully"
}
```

**Error Responses:**
```json
// Email not found
{
  "message": "Email not found"
}
```

## GET /phone-calls

**Description:** Retrieve all phone calls with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `patient_id` (optional): Filter by patient
- `recipient_type` (optional): Filter by recipient type ("therapist" or "patient")
- `status` (optional): Filter by call status
- `geplantes_datum` (optional): Filter by scheduled date
- `page` (optional): Page number
- `limit` (optional): Items per page

**Example Request:**
```bash
# Get all phone calls for a specific patient
curl "http://localhost:8004/api/phone-calls?patient_id=30"

# Get all scheduled calls for therapists
curl "http://localhost:8004/api/phone-calls?recipient_type=therapist&status=geplant"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "therapist_id": 123,
      "patient_id": null,
      "geplantes_datum": "2025-06-10",
      "geplante_zeit": "14:30",
      "dauer_minuten": 5,
      "status": "geplant",
      "tatsaechliches_datum": null,
      "tatsaechliche_zeit": null,
      "ergebnis": null,
      "notizen": "Follow-up für Bündel #456",
      "created_at": "2025-06-09T16:00:00",
      "updated_at": "2025-06-09T16:00:00"
    },
    {
      "id": 2,
      "therapist_id": null,
      "patient_id": 30,
      "geplantes_datum": "2025-06-11",
      "geplante_zeit": "10:00",
      "dauer_minuten": 10,
      "status": "geplant",
      "notizen": "Status update call",
      "created_at": "2025-06-10T16:00:00",
      "updated_at": "2025-06-10T16:00:00"
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
  "geplantes_datum": "2025-06-10",
  "geplante_zeit": "14:30",
  "dauer_minuten": 5,
  "status": "geplant",
  "tatsaechliches_datum": null,
  "tatsaechliche_zeit": null,
  "ergebnis": null,
  "notizen": "Follow-up für Bündel #456",
  "created_at": "2025-06-09T16:00:00",
  "updated_at": "2025-06-09T16:00:00"
}
```

## POST /phone-calls

**Description:** Schedule a new phone call. Must specify either `therapist_id` OR `patient_id`, not both.

**Required Fields:**
- Either `therapist_id` (integer) OR `patient_id` (integer) - exactly one must be provided

**Optional Fields:**
- `geplantes_datum` (string, YYYY-MM-DD) - for therapists: auto-scheduled if not provided; for patients: defaults to tomorrow
- `geplante_zeit` (string, HH:MM) - for therapists: auto-scheduled based on availability; for patients: defaults to 10:00
- `dauer_minuten` (integer) - defaults to 5 for therapists, 10 for patients
- `status` (string) - defaults to "geplant"
- `notizen` (string)

**Validation Rules:**
- Cannot specify both `therapist_id` and `patient_id`
- Must specify at least one of `therapist_id` or `patient_id`
- For therapists: If date/time not provided, system finds next available slot based on therapist's phone availability

**Example Requests:**

### Phone Call to Therapist (with auto-scheduling)
```bash
curl -X POST "http://localhost:8004/api/phone-calls" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "dauer_minuten": 5,
    "notizen": "Follow-up für Bündel #45"
  }'
```

### Phone Call to Patient (with specific time)
```bash
curl -X POST "http://localhost:8004/api/phone-calls" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "geplantes_datum": "2025-06-15",
    "geplante_zeit": "14:00",
    "dauer_minuten": 10,
    "notizen": "Status update regarding therapy search"
  }'
```

**Example Response:**
```json
{
  "id": 3,
  "patient_id": 30,
  "therapist_id": null,
  "geplantes_datum": "2025-06-15",
  "geplante_zeit": "14:00",
  "dauer_minuten": 10,
  "status": "geplant",
  "notizen": "Status update regarding therapy search",
  "created_at": "2025-06-10T12:30:00",
  "updated_at": "2025-06-10T12:30:00"
}
```

**Error Responses:**
```json
// Missing recipient
{
  "message": "Either therapist_id or patient_id is required"
}

// Both recipients specified
{
  "message": "Cannot specify both therapist_id and patient_id"
}

// No available slots for therapist
{
  "message": "No available slots found for this therapist"
}
```

## PUT /phone-calls/{id}

**Description:** Update phone call status and outcome.

**Example Request:**
```bash
curl -X PUT "http://localhost:8004/api/phone-calls/1" \
  -H "Content-Type: application/json" \
  -d '{
    "tatsaechliches_datum": "2025-06-15",
    "tatsaechliche_zeit": "10:05",
    "status": "abgeschlossen",
    "ergebnis": "Therapeut interessiert an 1 Patient",
    "notizen": "Will sich nächste Woche melden"
  }'
```

**Example Response:**
```json
{
  "id": 1,
  "status": "abgeschlossen",
  "tatsaechliches_datum": "2025-06-15",
  "tatsaechliche_zeit": "10:05",
  "ergebnis": "Therapeut interessiert an 1 Patient",
  "notizen": "Will sich nächste Woche melden",
  "updated_at": "2025-06-15T10:06:00"
}
```

## DELETE /phone-calls/{id}

**Description:** Delete a phone call.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8004/api/phone-calls/1"
```

**Example Response:**
```json
{
  "message": "Phone call deleted successfully"
}
```

---

# Geocoding Service API

## GET /geocode

**Description:** Convert an address to coordinates.

**Query Parameters:**
- `address` (required): Address to geocode

**Example Request:**
```bash
curl "http://localhost:8005/api/geocode?address=Berlin,Germany"
```

**Example Response:**
```json
{
  "latitude": 52.5200,
  "longitude": 13.4050,
  "display_name": "Berlin, Deutschland"
}
```

## GET /reverse-geocode

**Description:** Convert coordinates to an address.

**Query Parameters:**
- `lat` (required): Latitude
- `lon` (required): Longitude

**Example Request:**
```bash
curl "http://localhost:8005/api/reverse-geocode?lat=52.5200&lon=13.4050"
```

**Example Response:**
```json
{
  "display_name": "Berlin, Deutschland",
  "address": {
    "city": "Berlin",
    "country": "Deutschland",
    "postcode": "10117"
  }
}
```

## GET /calculate-distance

**Description:** Calculate distance between two points.

**Query Parameters:**
- `origin` (required): Address or coordinates (origin_lat, origin_lon)
- `destination` (required): Address or coordinates (destination_lat, destination_lon)
- `travel_mode` (optional): "car" or "transit" (default: "car")
- `no_cache` (optional): Bypass cache (default: false)

**Example Request:**
```bash
curl "http://localhost:8005/api/calculate-distance?origin=Berlin,Germany&destination=Munich,Germany&travel_mode=car"
```

**Example Response:**
```json
{
  "distance_km": 585.2,
  "travel_time_minutes": 345.5
}
```

## POST /find-therapists

**Description:** Find therapists within a specified distance from a patient.

**Example Request:**
```bash
curl -X POST "http://localhost:8005/api/find-therapists" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Example Response:**
```json
{
  "therapists": [
    {
      "id": 1,
      "distance_km": 12.3,
      "travel_time_minutes": 25.8,
      "within_range": true
    }
  ]
}
```

---

# Error Handling

## Standard HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error
- **501 Not Implemented**: Feature not yet implemented (legacy endpoints)

## Error Response Format

```json
{
  "message": "Specific error description in German"
}
```

## Common Error Scenarios

### Validation Errors (400)
```json
{
  "message": "Vorname ist erforderlich"
}
```

### Not Found (404)
```json
{
  "message": "Patient with ID 999 not found"
}
```

### Server Error (500)
```json
{
  "message": "Database error: connection failed"
}
```

### Not Implemented (501)
```json
{
  "message": "Bundle system not yet implemented"
}
```

---

# Testing Quick Reference

## Complete CRUD Test for Patient

```bash
# 1. List patients
curl "http://localhost:8001/api/patients"

# 2. Create patient
curl -X POST "http://localhost:8001/api/patients" \
  -H "Content-Type: application/json" \
  -d '{"vorname": "Test", "nachname": "Patient"}'

# 3. Get created patient (assuming ID 1)
curl "http://localhost:8001/api/patients/1"

# 4. Update patient
curl -X PUT "http://localhost:8001/api/patients/1" \
  -H "Content-Type: application/json" \
  -d '{"status": "auf_der_Suche"}'

# 5. Delete patient
curl -X DELETE "http://localhost:8001/api/patients/1"
```

## Bundle Workflow Test

```bash
# 1. Create patient search
curl -X POST "http://localhost:8003/api/platzsuchen" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1}'

# 2. Create bundles
curl -X POST "http://localhost:8003/api/buendel/erstellen" \
  -H "Content-Type: application/json" \
  -d '{"testlauf": false}'

# 3. Check bundles
curl "http://localhost:8003/api/therapeutenanfragen"

# 4. Record response
curl -X PUT "http://localhost:8003/api/therapeutenanfragen/1/antwort" \
  -H "Content-Type: application/json" \
  -d '{"patient_responses": {"1": "angenommen"}}'
```

## Patient Communication Test with Markdown

```bash
# 1. Send email to patient with markdown
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "betreff": "Willkommen bei der Therapievermittlung",
    "inhalt_markdown": "# Willkommen!\n\n**Wir freuen uns, Sie zu unterstützen.**\n\n## Nächste Schritte:\n\n1. Wir suchen passende Therapeuten\n2. Sie erhalten regelmäßige Updates\n3. Bei Fragen sind wir für Sie da\n\n*Mit freundlichen Grüßen,*\nIhr Therapievermittlungsteam",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "John Doe"
  }'

# 2. Schedule phone call for patient
curl -X POST "http://localhost:8004/api/phone-calls" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "geplantes_datum": "2025-06-20",
    "geplante_zeit": "14:00",
    "notizen": "Follow-up call"
  }'

# 3. Get patient communication history
curl "http://localhost:8001/api/patients/30/communication"

# 4. Filter emails by recipient type
curl "http://localhost:8004/api/emails?recipient_type=patient"
```

## Therapist Communication Test with Markdown

```bash
# 1. Send email to therapist with markdown
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "betreff": "Therapieanfrage für mehrere Patienten",
    "inhalt_markdown": "# Therapieanfrage\n\nSehr geehrte/r Dr. Weber,\n\nWir haben mehrere Patienten, die zu Ihrem Profil passen:\n\n## Patientenliste\n\n| Name | Diagnose | Wartezeit |\n|------|----------|----------|\n| Anna Müller | F32.1 | 30 Tage |\n| Max Schmidt | F41.1 | 45 Tage |\n\n**Bitte antworten Sie innerhalb von 7 Tagen.**\n\n[Kontaktieren Sie uns](mailto:info@curavani.de) bei Fragen.",
    "empfaenger_email": "dr.weber@praxis.de",
    "empfaenger_name": "Dr. Maria Weber",
    "add_legal_footer": true
  }'

# 2. Schedule phone call for therapist (auto-scheduling)
curl -X POST "http://localhost:8004/api/phone-calls" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "notizen": "Follow-up für Bündel #101"
  }'

# 3. Get therapist communication history
curl "http://localhost:8002/api/therapists/123/communication"

# 4. Filter phone calls by recipient type
curl "http://localhost:8004/api/phone-calls?recipient_type=therapist&status=geplant"
```

## Phone Call CRUD Test

```bash
# 1. List phone calls
curl "http://localhost:8004/api/phone-calls"

# 2. Create phone call
curl -X POST "http://localhost:8004/api/phone-calls" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "geplantes_datum": "2025-06-20",
    "geplante_zeit": "14:00",
    "notizen": "Follow-up call"
  }'

# 3. Get phone call details (assuming ID 1)
curl "http://localhost:8004/api/phone-calls/1"

# 4. Update phone call
curl -X PUT "http://localhost:8004/api/phone-calls/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "abgeschlossen",
    "ergebnis": "Patient contacted successfully"
  }'

# 5. Delete phone call
curl -X DELETE "http://localhost:8004/api/phone-calls/1"
```

---

**Note:** This document represents the current API state as of June 2025. All field names are in German, and the structure is flat (no nested objects). Always use the exact field names and enum values specified in this document. 

**Important Updates:**
- The communication service now supports markdown email creation via the `inhalt_markdown` field
- Legal footer can be added automatically to emails (controlled by `add_legal_footer` parameter)
- Both emails and phone calls support therapist AND patient communications
- When creating emails or phone calls, you must specify exactly one recipient type (either `therapist_id` OR `patient_id`, never both)
- Removed fields: `nachverfolgung_erforderlich`, `nachverfolgung_notizen` from emails; `wiederholen_nach` from phone calls
- **Email status handling:** The `POST /emails` endpoint now properly supports the `status` field to control whether emails are saved as drafts (`"Entwurf"`) or queued for immediate sending (`"In_Warteschlange"`)