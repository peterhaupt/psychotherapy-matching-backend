# Curavani Platform - Implementation Plan
## Four Independent Steps for Platform Enhancement
### Updated: January 2025 - Step 3 Completed

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

### Status
⏳ **NOT IMPLEMENTED**

---

## Step 2: Replace Follow-up Phone Calls with Reminder Emails

### Overview
After FOLLOW_UP_THRESHOLD_DAYS (default 7), send reminder emails instead of scheduling phone calls for unanswered anfragen. Keep phone calls as fallback for therapists without email.

### Database Migration

**Migration file:** `migrations/alembic/versions/004_add_reminder_email.py`

```sql
ALTER TABLE matching_service.therapeutenanfrage 
ADD COLUMN reminder_email_id INTEGER;

CREATE INDEX idx_therapeutenanfrage_reminder_email 
ON matching_service.therapeutenanfrage(reminder_email_id);
```

### Code Changes

#### File: `matching_service/services.py`

**Method to modify:** `AnfrageService.schedule_follow_up_reminders()`

**Implementation:**
```python
def schedule_follow_up_reminders(db: Session) -> int:
    # Find anfragen needing follow-up
    anfragen = db.query(Therapeutenanfrage).filter(
        Therapeutenanfrage.gesendet_datum.isnot(None),
        Therapeutenanfrage.antwort_datum.is_(None),
        Therapeutenanfrage.phone_call_id.is_(None),
        Therapeutenanfrage.reminder_email_id.is_(None)
    ).all()
    
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

### Email Template

**File:** `shared/templates/emails/anfrage_reminder.md`

Template includes:
- Reference to original anfrage
- Days since sent
- Patient summary
- Call to action for response

### Model Update

**File:** `matching_service/models/therapeutenanfrage.py`

Add field:
```python
reminder_email_id = Column(Integer, index=True)
```

### Status
⏳ **NOT IMPLEMENTED** (Migration exists but code not updated)

---

## Step 3: Send Patient Success Email ✅ COMPLETED

### Overview
When a patient is accepted by a therapist and the platzsuche is manually marked as "erfolgreich", automatically send an email to the patient with therapist contact details and instructions.

### Implementation Summary
Implemented January 28, 2025 - Full functionality to send success emails to patients when their therapy search is successful.

### Database Migration

**Migration file:** `migrations/alembic/versions/005_vermittelter_therapeut.py`

```python
def upgrade():
    # Add vermittelter_therapeut_id to track assigned therapist
    op.add_column(
        'platzsuche',
        sa.Column('vermittelter_therapeut_id', sa.Integer(), nullable=True),
        schema='matching_service'
    )
    
    op.create_index(
        'ix_matching_service_platzsuche_vermittelter_therapeut_id',
        'platzsuche',
        ['vermittelter_therapeut_id'],
        schema='matching_service'
    )
```

### Model Updates

**File:** `matching_service/models/platzsuche.py`

#### Added Features:
1. **New field:** `vermittelter_therapeut_id` - tracks the therapist assigned to the patient
2. **Validation methods:**
   - `set_vermittelter_therapeut()` - Sets therapist with validation
   - `can_change_therapeut()` - Checks if therapist can be changed
   - `validate_therapist_change()` - SQLAlchemy validator preventing changes after success
   - `validate_status_transition()` - Ensures therapist is set before marking successful

3. **Business Rules Enforced:**
   - Cannot mark platzsuche as "erfolgreich" without `vermittelter_therapeut_id`
   - Cannot change `vermittelter_therapeut_id` once status is "erfolgreich"

### API Updates

**File:** `matching_service/api/anfrage.py`

#### 1. New Helper Functions:
- **`send_patient_success_email()`** - Main function to send success email
- **`format_availability_for_email()`** - Formats patient's time availability
- **`format_phone_availability()`** - Formats therapist's phone hours
- **`create_default_patient_success_message()`** - Fallback if template missing

#### 2. Updated Endpoints:

**`PlatzsucheResource.get()`:**
- Now includes `vermittelter_therapeut_id` in response

**`PlatzsucheResource.put()`:**
- Accepts `vermittelter_therapeut_id` parameter
- Validates that therapist can't be changed after success
- When status changes to "erfolgreich":
  - Validates `vermittelter_therapeut_id` is set
  - Sends success email to patient
  - Updates patient status to "in_Therapie" if email succeeds

**`PlatzsucheListResource.get()`:**
- Includes `vermittelter_therapeut_id` in list responses

**`AnfrageResponseResource.put()`:**
- When therapist accepts a patient:
  - Automatically sets `vermittelter_therapeut_id` in platzsuche
  - Adds system note documenting the assignment

### Email Template

**File:** `shared/templates/emails/patient_success.md`

#### Template Features:
- Gender-appropriate greetings for patient and therapist
- Clear step-by-step instructions
- Conditional content based on:
  - Group therapy vs. individual therapy
  - Therapist has email vs. only phone
- Pre-written email template for patient to send to therapist
- Phone contact instructions with availability
- Important reminders (insurance card, etc.)
- Uses "wir" (we) instead of "ich" (I) throughout
- Hardcoded values:
  - CC: info@curavani.com
  - Sender: "Ihr Curavani Team"
  - Company name: Curavani
- Legal footer added automatically by communication service

### Workflow

1. **Automatic Assignment:**
   - Therapist accepts patient via anfrage response → `vermittelter_therapeut_id` set automatically

2. **Manual Assignment:**
   - Admin can manually set `vermittelter_therapeut_id` via PUT `/api/platzsuchen/{id}`

3. **Success Trigger:**
   - Admin marks platzsuche as "erfolgreich" (requires `vermittelter_therapeut_id` to be set)
   - System sends success email to patient
   - If email sends successfully, patient status updates to "in_Therapie"

### Edge Case Handling

- **No patient email:** Log warning, no email sent, status still changes
- **Therapist not found:** Log error, no email sent
- **Template missing:** Uses fallback message
- **Email service error:** Log error but don't fail the status update
- **Patient status update fails:** Log error but operation continues

### Testing

**File:** `tests/integration/test_matching_service_api.py`

Added 7 comprehensive tests:
1. `test_update_platzsuche_with_vermittelter_therapeut` - Manual setting
2. `test_platzsuche_erfolgreich_requires_therapeut` - Validation
3. `test_platzsuche_cannot_change_therapeut_after_erfolgreich` - Immutability
4. `test_platzsuche_success_triggers_email` - Email trigger (commented to avoid bounces)
5. `test_platzsuche_response_includes_vermittelter_therapeut` - API response
6. `test_anfrage_response_sets_vermittelter_therapeut` - Auto-setting
7. `test_anfrage_acceptance_workflow` - Full workflow test

### Deployment Steps

1. **Run migration:**
   ```bash
   alembic upgrade head
   ```

2. **Deploy files:**
   - `matching_service/models/platzsuche.py`
   - `matching_service/api/anfrage.py`
   - `shared/templates/emails/patient_success.md`

3. **Restart service:**
   ```bash
   docker-compose restart matching-service
   ```

4. **Verify:**
   - Check migration applied: `SELECT * FROM information_schema.columns WHERE table_name='platzsuche' AND column_name='vermittelter_therapeut_id';`
   - Test API endpoints return new field
   - Test complete workflow in staging

### Status
✅ **COMPLETED** - January 28, 2025

---

## Step 4: Modify Anfrage Email Content to Therapists

### Overview
Change the content of the initial email sent to therapists when creating therapeutenanfragen.

### Files to Modify

#### File: `shared/templates/emails/psychotherapie_anfrage.md`

Current template structure that needs modification:
- Greeting with therapist title/name
- List of patients with details
- Request for response
- Contact information

### Implementation Notes
- No code changes required, only template modification
- Changes will be defined during implementation based on business requirements
- Test by creating new anfragen and reviewing generated emails

### Testing
- Create anfrage for therapist
- Review generated email content
- Verify all patient data displays correctly
- Check formatting and readability

### Status
⏳ **NOT IMPLEMENTED** - Template content changes to be defined

---

## Overall Implementation Status

| Step | Description | Status | Notes |
|------|------------|--------|-------|
| 1 | Default Salutation "Frau" | ⏳ Not Started | Simple change, low risk |
| 2 | Reminder Emails | ⏳ Not Started | Migration exists, code needs update |
| 3 | Patient Success Email | ✅ **COMPLETED** | Fully implemented and tested |
| 4 | Anfrage Email Content | ⏳ Not Started | Template changes TBD |

### Completed Components (Step 3)
- ✅ Database migration (005_vermittelter_therapeut.py)
- ✅ Model updates (platzsuche.py)
- ✅ API endpoints (anfrage.py)
- ✅ Email template (patient_success.md)
- ✅ Integration tests (7 new tests)
- ✅ Business logic validation
- ✅ Error handling and edge cases

### Next Steps
1. Deploy Step 3 to staging environment
2. Test complete workflow with real data
3. Monitor email delivery and patient status updates
4. Plan implementation of remaining steps (1, 2, 4)

### Key Learnings from Step 3
- Email deduplication already in place helped avoid conflicts
- Conditional template content works well with Jinja2
- Separating email sending from status update prevents failures
- Comprehensive validation at model level ensures data integrity