# Frontend API Documentation

## Base URLs
- Patient Service: `http://localhost:8001`
- Therapist Service: `http://localhost:8002`
- Matching Service: `http://localhost:8003`
- Communication Service: `http://localhost:8004`
- Geocoding Service: `http://localhost:8005`

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

### PlacementRequestStatus
```javascript
const PlacementRequestStatus = {
  OPEN: "offen",
  IN_PROGRESS: "in_bearbeitung",
  REJECTED: "abgelehnt",
  ACCEPTED: "angenommen"
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

## Therapist Service API

### GET /api/therapists
Query parameters:
- `status` (optional): Filter by therapist status

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
  "potentially_available": boolean,
  "potentially_available_notes": "string"
}
```

### GET /api/therapists/{id}
Returns therapist object

### PUT /api/therapists/{id}
Same fields as POST (all optional)

### DELETE /api/therapists/{id}
No body required

## Matching Service API

### GET /api/placement-requests
Query parameters:
- `patient_id` (optional): Filter by patient
- `therapist_id` (optional): Filter by therapist
- `status` (optional): Filter by status

### POST /api/placement-requests
Required fields:
```json
{
  "patient_id": integer,
  "therapist_id": integer
}
```

Optional fields:
```json
{
  "status": "offen|in_bearbeitung|abgelehnt|angenommen",
  "priority": integer,
  "notes": "string"
}
```

### GET /api/placement-requests/{id}
Returns placement request object

### PUT /api/placement-requests/{id}
Optional fields:
```json
{
  "status": "offen|in_bearbeitung|abgelehnt|angenommen",
  "response": "string",
  "response_date": "YYYY-MM-DD",
  "next_contact_after": "YYYY-MM-DD",
  "priority": integer,
  "notes": "string"
}
```

### DELETE /api/placement-requests/{id}
No body required

## Communication Service API

### Email Endpoints

#### GET /api/emails
Query parameters:
- `therapist_id` (optional): Filter by therapist
- `status` (optional): Filter by status
- `response_received` (optional): Filter by response status
- `batch_id` (optional): Filter by batch ID

#### POST /api/emails
Required fields:
```json
{
  "therapist_id": integer,
  "subject": "string",
  "body_html": "string",
  "recipient_email": "string",
  "recipient_name": "string"
}
```

Optional fields:
```json
{
  "body_text": "string",
  "sender_email": "string",
  "sender_name": "string",
  "status": "DRAFT|QUEUED|SENDING|SENT|FAILED",
  "placement_request_ids": [1, 2, 3],
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
  "response_received": boolean,
  "response_date": "YYYY-MM-DD",
  "response_content": "string",
  "follow_up_required": boolean,
  "follow_up_notes": "string"
}
```

### Phone Call Endpoints

#### GET /api/phone-calls
Query parameters:
- `therapist_id` (optional): Filter by therapist
- `status` (optional): Filter by status
- `scheduled_date` (optional): Filter by date

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
  "scheduled_date": "YYYY-MM-DD",
  "scheduled_time": "HH:MM",
  "duration_minutes": integer,
  "status": "scheduled|completed|failed|canceled",
  "notes": "string",
  "placement_request_ids": [1, 2, 3]
}
```

Note: If `scheduled_date` and `scheduled_time` are not provided, the system will automatically find the next available slot based on the therapist's availability.

#### GET /api/phone-calls/{id}
Returns phone call object

#### PUT /api/phone-calls/{id}
Optional fields:
```json
{
  "scheduled_date": "YYYY-MM-DD",
  "scheduled_time": "HH:MM",
  "duration_minutes": integer,
  "actual_date": "YYYY-MM-DD",
  "actual_time": "HH:MM",
  "status": "scheduled|completed|failed|canceled",
  "outcome": "string",
  "notes": "string",
  "retry_after": "YYYY-MM-DD"
}
```

#### DELETE /api/phone-calls/{id}
No body required

## Geocoding Service API

### GET /api/geocode
Query parameters:
- `address` (required): Address to geocode

Response:
```json
{
  "latitude": float,
  "longitude": float,
  "display_name": "string",
  "address_components": {},
  "source": "string",
  "status": "success|error"
}
```

### GET /api/reverse-geocode
Query parameters:
- `lat` (required): Latitude
- `lon` (required): Longitude

### GET /api/calculate-distance
Query parameters (origin can be address OR coordinates):
- `origin` (optional): Origin address
- `origin_lat` (optional): Origin latitude
- `origin_lon` (optional): Origin longitude

Query parameters (destination can be address OR coordinates):
- `destination` (optional): Destination address
- `destination_lat` (optional): Destination latitude
- `destination_lon` (optional): Destination longitude

Additional parameters:
- `travel_mode` (optional): "car" or "transit" (default: "car")
- `no_cache` (optional): Bypass cache (default: false)

Response:
```json
{
  "distance_km": float,
  "travel_time_minutes": float,
  "status": "success|partial|error",
  "source": "osrm|haversine|cache",
  "travel_mode": "car|transit",
  "route_available": boolean
}
```

### POST /api/find-therapists
Request body:
```json
{
  "patient_address": "string",
  "max_distance_km": float,
  "travel_mode": "car|transit",
  "therapists": [
    {
      "id": integer,
      "strasse": "string",
      "plz": "string",
      "ort": "string"
    }
  ]
}
```

Alternative using coordinates:
```json
{
  "patient_lat": float,
  "patient_lon": float,
  "max_distance_km": float,
  "travel_mode": "car|transit",
  "therapists": [...]
}
```

Response:
```json
{
  "status": "success",
  "count": integer,
  "therapists": [
    {
      "id": integer,
      "distance_km": float,
      "travel_time_minutes": float,
      "travel_mode": "string"
    }
  ]
}
```

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

1. **Date Format**: Always use ISO format `YYYY-MM-DD` for dates
2. **Time Format**: Always use 24-hour format `HH:MM` for times
3. **Boolean Values**: Use JavaScript `true`/`false` (not strings)
4. **Enum Values**: Always use the exact string values shown above
5. **Optional Fields**: Fields marked as optional can be omitted entirely from requests
6. **German Field Names**: Many field names are in German - refer to TERMINOLOGY.md for translations
7. **JSON Arrays**: For list fields like `ausgeschlossene_therapeuten`, always send as arrays even if empty
8. **Availability Structure**: The `zeitliche_verfuegbarkeit` and `telefonische_erreichbarkeit` fields use weekday names in English (lowercase) as keys