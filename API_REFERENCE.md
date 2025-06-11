# API Reference - Psychotherapy Matching Platform

**Single Source of Truth for All API Integration**

Last Updated: December 2024

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
      "created_at": "2025-05-01T08:00:00",
      "updated_at": "2025-06-01T14:30:00"
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
  "created_at": "2025-05-01T08:00:00",
  "updated_at": "2025-06-01T14:30:00"
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
  "created_at": "2025-06-10T10:30:00",
  "updated_at": "2025-06-10T10:30:00"
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
    "funktionierender_therapieplatz_am": "2025-06-15"
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
  "updated_at": "2025-06-10T10:35:00"
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
      "created_date": "2025-06-07T10:00:00",
      "sent_date": "2025-06-07T10:30:00",
      "response_date": null,
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
  "created_date": "2025-06-07T10:00:00",
  "sent_date": "2025-06-07T10:30:00",
  "response_date": null,
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
- `status` (optional): Filter by email status
- `page` (optional): Page number
- `limit` (optional): Items per page

**Example Request:**
```bash
curl "http://localhost:8004/api/emails?status=Gesendet"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "therapist_id": 123,
      "betreff": "Therapieanfrage für mehrere Patienten",
      "empfaenger_email": "doctor@example.com",
      "empfaenger_name": "Dr. Schmidt",
      "absender_email": "info@boona.de",
      "absender_name": "Boona Team",
      "status": "Gesendet",
      "antwort_erhalten": false,
      "antwortdatum": null,
      "antwortinhalt": null,
      "nachverfolgung_erforderlich": false,
      "sent_at": "2025-06-08T10:30:00",
      "created_at": "2025-06-08T10:25:00",
      "updated_at": "2025-06-08T10:30:00"
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

**Example Response:** Same structure as single email in list response, plus `body_html` and `body_text` fields.

## POST /emails

**Description:** Create a new email.

**Required Fields:**
- `therapist_id` (integer)
- `betreff` (string)
- `body_html` (string)
- `body_text` (string)
- `empfaenger_email` (string)
- `empfaenger_name` (string)

**Example Request:**
```bash
curl -X POST "http://localhost:8004/api/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "betreff": "Therapieanfrage für mehrere Patienten",
    "body_html": "<html><body><h1>Therapieanfrage</h1><p>Sehr geehrte/r Dr. Schmidt,</p><p>wir haben mehrere Patienten, die...</p></body></html>",
    "body_text": "Sehr geehrte/r Dr. Schmidt,\n\nwir haben mehrere Patienten, die...",
    "empfaenger_email": "doctor@example.com",
    "empfaenger_name": "Dr. Schmidt"
  }'
```

**Example Response:**
```json
{
  "id": 2,
  "therapist_id": 123,
  "betreff": "Therapieanfrage für mehrere Patienten",
  "empfaenger_email": "doctor@example.com",
  "empfaenger_name": "Dr. Schmidt",
  "status": "In_Warteschlange",
  "created_at": "2025-06-10T12:00:00",
  "updated_at": "2025-06-10T12:00:00"
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
    "antwortdatum": "2025-06-09T14:00:00",
    "antwortinhalt": "Ich kann 2 Patienten aufnehmen.",
    "nachverfolgung_erforderlich": false
  }'
```

**Example Response:**
```json
{
  "id": 1,
  "antwort_erhalten": true,
  "antwortdatum": "2025-06-09T14:00:00",
  "antwortinhalt": "Ich kann 2 Patienten aufnehmen.",
  "nachverfolgung_erforderlich": false,
  "updated_at": "2025-06-10T12:05:00"
}
```

## GET /phone-calls

**Description:** Retrieve all phone calls with filtering.

**Query Parameters:**
- `therapist_id` (optional): Filter by therapist
- `status` (optional): Filter by call status
- `page` (optional): Page number
- `limit` (optional): Items per page

**Example Request:**
```bash
curl "http://localhost:8004/api/phone-calls?status=geplant"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "therapist_id": 123,
      "geplantes_datum": "2025-06-10",
      "geplante_zeit": "14:30",
      "dauer_minuten": 5,
      "status": "geplant",
      "tatsaechliches_datum": null,
      "tatsaechliche_zeit": null,
      "ergebnis": null,
      "notizen": "Follow-up für Bündel #456",
      "wiederholen_nach": null,
      "created_at": "2025-06-09T16:00:00",
      "updated_at": "2025-06-09T16:00:00"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 23
}
```

## POST /phone-calls

**Description:** Schedule a new phone call.

**Required Fields:**
- `therapist_id` (integer)
- `geplantes_datum` (string, YYYY-MM-DD)
- `geplante_zeit` (string, HH:MM)

**Example Request:**
```bash
curl -X POST "http://localhost:8004/api/phone-calls" \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "geplantes_datum": "2025-06-15",
    "geplante_zeit": "10:00",
    "dauer_minuten": 5,
    "notizen": "Follow-up für Bündel #45"
  }'
```

**Example Response:**
```json
{
  "id": 2,
  "therapist_id": 123,
  "geplantes_datum": "2025-06-15",
  "geplante_zeit": "10:00",
  "dauer_minuten": 5,
  "status": "geplant",
  "notizen": "Follow-up für Bündel #45",
  "created_at": "2025-06-10T12:30:00",
  "updated_at": "2025-06-10T12:30:00"
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

---

**Note:** This document represents the current API state as of December 2024. All field names are in German, and the structure is flat (no nested objects). Always use the exact field names and enum values specified in this document.
