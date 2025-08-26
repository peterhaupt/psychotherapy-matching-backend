# Curavani Platform - Implementation Plan
## Four Independent Steps for Platform Enhancement

---

## Step 1: Default Salutation to "Frau" in Therapist Import

### Overview
When importing therapists from scraped JSON files, if the salutation field is missing or empty, default to "Frau" instead of failing the import.

### Technical Changes

#### File: `therapist_service/imports/therapist_importer.py`

**Method to modify:** `_map_therapist_data()`

**Current code section (around line 80-90):**
```python
# Required fields check
if not all([
    basic_info.get('first_name'),
    basic_info.get('last_name'),
    basic_info.get('salutation'),  # Currently required
    location.get('postal_code')
]):
    logger.warning("Missing required fields in therapist data")
    return None
```

**Change to:**
1. Remove `salutation` from required fields check
2. Add defaulting logic when mapping:

```python
# Map with salutation defaulting
mapped = {
    'anrede': basic_info.get('salutation') or 'Frau',  # Default to Frau
    'geschlecht': self._map_gender_from_salutation(basic_info.get('salutation') or 'Frau'),
    # ... rest of mapping
}
```

### Testing
- Test with JSON file missing salutation field
- Test with JSON file having empty string salutation
- Verify import succeeds and therapist created with "Frau" as anrede

### Notes
- This is a simple, isolated change
- No database migration needed
- No API changes needed

---

## Step 2: Replace Follow-up Phone Calls with Reminder Emails

### Overview
After FOLLOW_UP_THRESHOLD_DAYS (default 7), send reminder emails instead of scheduling phone calls for unanswered anfragen. Keep phone calls as fallback for therapists without email.

### Database Migration

**Add field to Therapeutenanfrage table:**
```sql
ALTER TABLE matching_service.therapeutenanfrage 
ADD COLUMN reminder_email_id INTEGER;

ALTER TABLE matching_service.therapeutenanfrage
ADD CONSTRAINT fk_reminder_email 
FOREIGN KEY (reminder_email_id) 
REFERENCES communication_service.emails(id);

CREATE INDEX idx_therapeutenanfrage_reminder_email 
ON matching_service.therapeutenanfrage(reminder_email_id);
```

### Code Changes

#### File: `matching_service/services.py`

**Method to modify:** `AnfrageService.schedule_follow_up_calls()`

**Current logic:**
1. Finds anfragen needing follow-up
2. Schedules phone calls for all

**New logic:**
1. Find anfragen needing follow-up
2. For each anfrage:
   - Check if therapist has email
   - If yes → send reminder email
   - If no → schedule phone call (existing logic)
   - Update reminder_email_id or phone_call_id accordingly

**Key changes in the method:**
```python
def schedule_follow_up_calls(db: Session) -> int:
    # Get follow-up configuration
    follow_up_config = config.get_follow_up_config()
    threshold_days = follow_up_config['threshold_days']
    
    # Find anfragen needing follow-up (modified query)
    anfragen = db.query(Therapeutenanfrage).filter(
        Therapeutenanfrage.gesendet_datum.isnot(None),
        Therapeutenanfrage.antwort_datum.is_(None),
        Therapeutenanfrage.phone_call_id.is_(None),
        Therapeutenanfrage.reminder_email_id.is_(None)  # NEW: Check no reminder sent
    ).all()
    
    # For each anfrage needing follow-up
    for anfrage in anfragen_needing_followup:
        therapist = TherapistService.get_therapist(anfrage.therapist_id)
        
        if therapist and therapist.get('email'):
            # Send reminder email
            email_id = send_reminder_email(anfrage, therapist)
            if email_id:
                anfrage.reminder_email_id = email_id
                db.commit()
        else:
            # Fallback to phone call
            call_id = CommunicationService.schedule_follow_up_call(...)
            if call_id:
                anfrage.phone_call_id = call_id
                db.commit()
```

**New helper method to add:**
```python
def send_reminder_email(anfrage: Therapeutenanfrage, therapist: dict) -> Optional[int]:
    """Send reminder email for unanswered anfrage."""
    # Get patient data for anfrage
    patient_ids = [ap.patient_id for ap in anfrage.anfrage_patients]
    patients = PatientService.get_patients(patient_ids)
    
    # Prepare patient data list
    patient_data = []
    for ap in anfrage.anfrage_patients:
        if ap.patient_id in patients:
            patient_data.append(patients[ap.patient_id])
    
    # Render reminder template
    # ... (similar to create_anfrage_email but with reminder template)
    
    # Send via communication service
    email_data = {
        'therapist_id': therapist['id'],
        'betreff': f"Erinnerung: Therapieanfrage - Ref: A{anfrage.id}",
        'inhalt_markdown': reminder_markdown,
        'empfaenger_email': therapist['email'],
        'status': 'In_Warteschlange'
    }
    
    response = requests.post(f"{comm_url}/api/emails", json=email_data)
    # ... return email_id
```

### Email Template

**New file:** `shared/templates/emails/anfrage_reminder.md`

```markdown
Sehr geehrte/r {{ therapist.anrede }} {{ therapist.titel }} {{ therapist.nachname }},

vor {{ days_since_sent }} Tagen haben wir Ihnen eine Anfrage für {{ patient_count }} Patient{% if patient_count > 1 %}en{% endif %} gesendet (Ref: A{{ anfrage_id }}).

Wir würden uns über eine Rückmeldung freuen, ob Sie Kapazitäten für diese Patienten haben.

## Übersicht der angefragten Patienten:

{% for patient in patients %}
### Patient {{ loop.index }}
- **Geschlecht:** {{ patient.geschlecht }}
- **Alter:** {{ patient.age }} Jahre
- **Krankenkasse:** {{ patient.krankenkasse }}
- **Symptome:** {{ patient.symptome | join(', ') }}
{% endfor %}

Falls Sie keine Kapazitäten haben, lassen Sie es uns bitte kurz wissen, damit wir die Suche für diese Patienten fortsetzen können.

Mit freundlichen Grüßen
Das Curavani Team
```

### Model Update

**File:** `matching_service/models/therapeutenanfrage.py`

Add field to model class:
```python
reminder_email_id = Column(
    Integer,
    index=True
)  # References communication_service.emails.id
```

### Testing
- Test with therapist having email → verify reminder email sent
- Test with therapist without email → verify phone call scheduled
- Test that duplicate reminders are not sent
- Test after 7 days threshold

---

## Step 3: Send Patient Success Email

### Overview
When a patient is accepted by a therapist and the platzsuche is manually marked as "erfolgreich", automatically send an email to the patient with therapist contact details and instructions.

### Database Migration

**Add field to Platzsuche table:**
```sql
ALTER TABLE matching_service.platzsuche 
ADD COLUMN verfuegbarer_therapeut_id INTEGER;

CREATE INDEX idx_platzsuche_verfuegbarer_therapeut 
ON matching_service.platzsuche(verfuegbarer_therapeut_id);
```

### Code Changes

#### File: `matching_service/models/platzsuche.py`

**Add field to model:**
```python
# After the existing fields
verfuegbarer_therapeut_id = Column(
    Integer,
    nullable=True,
    index=True
)  # References therapist_service.therapeuten.id
```

#### File: `matching_service/api/anfrage.py`

**1. In `AnfrageResponseResource.put()` method:**

When a patient is accepted, set the `verfuegbarer_therapeut_id`:

```python
# After the existing acceptance logic (around line 850)
for ap in anfrage.anfrage_patients:
    if ap.is_accepted():
        accepted_patients.append({
            "patient_id": ap.patient_id,
            "platzsuche_id": ap.platzsuche_id
        })
        
        # Mark search with available therapist
        search = db.query(Platzsuche).filter_by(id=ap.platzsuche_id).first()
        if search:
            search.verfuegbarer_therapeut_id = anfrage.therapist_id  # NEW
            
            # Existing logic for marking successful
            if search.status == SuchStatus.aktiv:
                search.mark_successful()
```

**2. In `PlatzsucheResource.put()` method:**

When status changes to "erfolgreich" and therapist is available, send email:

```python
# After status update logic (around line 140)
if args.get('status'):
    try:
        new_status = SuchStatus[args['status']]
        old_status = search.status
        search.status = new_status
        
        # NEW: Send patient success email when marked successful
        if new_status == SuchStatus.erfolgreich and search.verfuegbarer_therapeut_id:
            # Send success email to patient
            send_patient_success_email(db, search)
        
    except KeyError:
        # existing error handling
```

**3. Add new helper function in same file or services.py:**

```python
def send_patient_success_email(db: Session, search: Platzsuche) -> Optional[int]:
    """Send success email to patient with therapist details."""
    
    # Get patient data
    patient = PatientService.get_patient(search.patient_id)
    if not patient or not patient.get('email'):
        logger.warning(f"Cannot send success email - patient {search.patient_id} has no email")
        return None
    
    # Get therapist data
    therapist = TherapistService.get_therapist(search.verfuegbarer_therapeut_id)
    if not therapist:
        logger.error(f"Cannot send success email - therapist {search.verfuegbarer_therapeut_id} not found")
        return None
    
    # Prepare template context
    context = {
        'patient': patient,
        'therapist': therapist,
        'is_group_therapy': therapist.get('bevorzugt_gruppentherapie', False),
        'has_email': bool(therapist.get('email')),
        'has_phone': bool(therapist.get('telefon'))
    }
    
    # Format availability for email template
    if patient.get('zeitliche_verfuegbarkeit'):
        context['availability_formatted'] = format_availability_for_email(
            patient['zeitliche_verfuegbarkeit']
        )
    
    # Render template
    template_path = os.path.join(shared_path, 'templates', 'emails')
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template('patient_success.md')
    email_markdown = template.render(context)
    
    # Send email via communication service
    subject = "Therapieplatz gefunden!"
    
    email_data = {
        'patient_id': patient['id'],
        'betreff': subject,
        'inhalt_markdown': email_markdown,
        'empfaenger_email': patient.get('email'),
        'empfaenger_name': f"{patient.get('vorname', '')} {patient.get('nachname', '')}".strip(),
        'status': 'In_Warteschlange'
    }
    
    # Call communication service
    comm_url = config.get_service_url('communication', internal=True)
    response = requests.post(f"{comm_url}/api/emails", json=email_data)
    
    if response.ok:
        email_id = response.json().get('id')
        logger.info(f"Sent success email {email_id} to patient {patient['id']}")
        return email_id
    else:
        logger.error(f"Failed to send success email: {response.status_code}")
        return None
```

### Email Template

**New file:** `shared/templates/emails/patient_success.md`

```markdown
Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

ich habe einen freien {% if is_group_therapy %}Psychotherapieplatz in einer Gruppe{% else %}Psychotherapieplatz{% endif %} für Sie gefunden bei {{ therapist.titel }} {{ therapist.vorname }} {{ therapist.nachname }}.

Bitte führen Sie folgende Schritte durch:

1. {% if has_email %}Schicken Sie die unten von mir bereits vorformulierte E-Mail an den Therapeuten{% else %}Rufen Sie den Therapeuten an{% endif %}, um einen Termin für ein persönliches Erstgespräch zu vereinbaren.
2. {% if has_email %}Setzen Sie mich mit der E-Mail {{ footer.contact_email | default('info@curavani.com') }} dabei in Kopie.{% endif %}
3. Teilen Sie mir nach dem Erstgespräch mit, ob Sie mit dem Therapeuten einverstanden sind. Ohne eine Rückmeldung von Ihnen gehe ich davon aus, dass Sie mit dem Therapeuten einverstanden sind.
4. Der Therapeut gibt mir keine Informationen über den Therapieverlauf mit Ihnen. Wenn also irgendetwas nicht passt und Sie sich Unterstützung von mir wünschen, müssen Sie sich aktiv bei mir melden.

## Kontaktdaten des Therapeuten:

**{{ therapist.titel }} {{ therapist.vorname }} {{ therapist.nachname }}**  
{{ therapist.strasse }}  
{{ therapist.plz }} {{ therapist.ort }}  
{% if has_phone %}Telefon: {{ therapist.telefon }}  {% endif %}
{% if has_email %}E-Mail: {{ therapist.email }}{% endif %}

{% if has_email %}
---

## Bitte schicken Sie folgende E-Mail:

**Betreff:** {% if is_group_therapy %}Gruppentherapieplatz{% else %}Therapieplatz{% endif %} gemäß Absprache mit {{ footer.sender_name | default('Curavani') }}

Sehr geehrte{{ 'r Herr' if therapist.geschlecht == 'männlich' else ' Frau' }} {{ therapist.titel }} {{ therapist.nachname }},

wie mit {{ footer.sender_name_dative | default('Curavani') }} besprochen, möchte ich gerne {% if is_group_therapy %}an der Gruppentherapie bei Ihnen teilnehmen{% else %}einen Therapieplatz bei Ihnen in Anspruch nehmen{% endif %}. Für ein Erstgespräch bin ich wie folgt verfügbar:

{{ availability_formatted | default('Meine Verfügbarkeit bespreche ich gerne persönlich mit Ihnen.') }}

Schlagen Sie gerne in dieser Zeit einen Termin für ein Erstgespräch vor. Ich werde zum Termin mein Versicherungskärtchen mitbringen. Wenn Sie vorab noch weitere Informationen benötigen, lassen Sie mich dies gerne wissen. Ich freue mich darauf Sie kennenzulernen.

Mit freundlichen Grüßen

{{ patient.vorname }} {{ patient.nachname }}  
Telefon: {{ patient.telefon }}

---
{% else %}
## Bitte rufen Sie während der folgenden Zeiten an:

{% if therapist.telefonische_erreichbarkeit %}
{{ format_phone_availability(therapist.telefonische_erreichbarkeit) }}
{% else %}
Telefonische Erreichbarkeit nicht angegeben. Bitte versuchen Sie es zu üblichen Geschäftszeiten.
{% endif %}
{% endif %}

Wenn Sie noch Fragen haben, melden Sie sich jederzeit gerne.

Mit freundlichen Grüßen

{{ footer.sender_name | default('Ihr Curavani Team') }}

{{ footer.phone | default('Telefon: +49 151 46359691') }}  
{{ footer.email | default('E-Mail: info@curavani.com') }}

{{ footer.address | default('Jülicher Str. 72a\n52070 Aachen\nDeutschland') }}

{{ footer.company_info | default('Geschäftsführer: Peter Haupt\nHandelsregister: Amtsgericht Aachen, HRB 28791') }}
```

### Configuration

**Environment variables to add (optional - with defaults):**
```bash
# Email footer configuration
EMAIL_FOOTER_SENDER_NAME="Peter Haupt"
EMAIL_FOOTER_SENDER_NAME_DATIVE="Herrn Haupt"  # For German grammar
EMAIL_FOOTER_CONTACT_EMAIL="info@curavani.com"
EMAIL_FOOTER_PHONE="Telefon: +49 151 46359691"
EMAIL_FOOTER_ADDRESS="Jülicher Str. 72a\n52070 Aachen\nDeutschland"
EMAIL_FOOTER_COMPANY_INFO="Geschäftsführer: Peter Haupt\nHandelsregister: Amtsgericht Aachen, HRB 28791"
```

### Testing
- Create anfrage with patient acceptance
- Manually mark platzsuche as "erfolgreich"
- Verify email sent with correct content
- Test with therapist having/not having email
- Test with group therapy preference

### Edge Cases
- Patient has no email → log warning, no email sent
- Therapist not found → log error, no email sent
- Therapist has no email → template adjusts to show phone instructions
- Therapist has no phone → template only shows email

---

## Step 4: Modify Anfrage Email Content to Therapists

### Overview
Change the content of the initial email sent to therapists when creating therapeutenanfragen. The specific content changes will be defined during implementation.

### Files to Modify

#### File: `shared/templates/emails/psychotherapie_anfrage.md`

This is the main template for therapist anfrage emails. The current template includes:
- Greeting with therapist title/name
- List of patients with details
- Request for response
- Contact information

**Current structure to be modified:**
```markdown
Sehr geehrte/r {{ therapist.anrede }} {{ therapist.titel }} {{ therapist.nachname }},

[Introduction text - TO BE DEFINED]

## Angefragte Patienten:

{% for patient in patients %}
### Patient {{ loop.index }}
[Patient details - STRUCTURE MAY CHANGE]
{% endfor %}

[Closing text - TO BE DEFINED]

Mit freundlichen Grüßen
Das Curavani Team
```

### Implementation Notes
- No code changes required, only template modification
- Changes will be defined during implementation based on business requirements
- Test by creating new anfragen and reviewing generated emails

### Testing
- Create anfrage for therapist
- Review generated email content
- Verify all patient data displays correctly
- Check formatting and readability

---

## General Implementation Notes

### Order of Implementation
1. **Step 1** - Salutation fix (simplest, immediate benefit)
2. **Step 2** - Reminder emails (clear value, moderate complexity)
3. **Step 3** - Patient success email (most complex, requires DB migration)
4. **Step 4** - Email content changes (can be done anytime)

### Database Migrations
- Run migrations for Steps 2 and 3 before deploying code
- Use proper migration tool (Alembic) in production
- Test migrations on staging environment first

### Configuration Management
- Add new environment variables for email footer (Step 3)
- Ensure all services can access shared templates
- Update Docker volumes if needed for template access

### Testing Strategy
- Test each step independently
- Use staging environment for integration testing
- Monitor email delivery in communication service logs
- Verify no disruption to existing functionality

### Rollback Plan
- Each step can be rolled back independently
- Database migrations should include rollback scripts
- Keep backups of original templates
- Monitor for issues after each deployment

### Dependencies
- Jinja2 for template rendering (already installed)
- No new Python packages required
- Communication service API must be accessible
- Patient and Therapist services must be running

### Monitoring
- Check logs for email sending failures
- Monitor reminder email scheduling
- Track patient success email delivery
- Review therapist response rates after changes