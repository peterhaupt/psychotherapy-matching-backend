# Email/Phone Call Preference Implementation Guide

## Overview

This document describes the implementation changes needed to prioritize therapists with email addresses and automatically create phone calls for therapists without email addresses when sending anfragen.

## Current vs. New Behavior

### Current Behavior
- **Therapist Selection**: 4-tier priority sorting (available+informed > available+not informed > not available+informed > others)
- **Anfrage Sending**: Fails with HTTP 500 error for therapists without email

### New Behavior
- **Therapist Selection**: 8-tier priority sorting - first all 4 tiers WITH email, then all 4 tiers WITHOUT email
- **Anfrage Sending**: Creates phone call immediately for therapists without email instead of failing

---

## 1. Integration Test Updates

### File: `tests/integration/test_matching_service_api.py`

Add the following test methods to the `TestMatchingServiceAPI` class:

```python
def test_therapeuten_zur_auswahl_email_priority(self):
    """Test that therapists with email are prioritized over those without."""
    # Create therapist WITH email - available and informed (highest priority)
    therapist_with_email = self.create_test_therapist(
        plz="52064",
        potenziell_verfuegbar=True,
        ueber_curavani_informiert=True,
        email="therapist.with.email@example.com",
        vorname="WithEmail",
        nachname="Therapist"
    )
    
    # Create therapist WITHOUT email - available and informed (should be lower priority)
    therapist_without_email = self.create_test_therapist(
        plz="52065", 
        potenziell_verfuegbar=True,
        ueber_curavani_informiert=True,
        email=None,  # No email
        vorname="WithoutEmail",
        nachname="Therapist"
    )
    
    # Get therapists for selection
    response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
    assert response.status_code == 200
    
    data = response.json()
    therapists = data['data']
    
    # Find positions of our therapists
    with_email_index = None
    without_email_index = None
    
    for i, t in enumerate(therapists):
        if t['id'] == therapist_with_email['id']:
            with_email_index = i
        elif t['id'] == therapist_without_email['id']:
            without_email_index = i
    
    # Verify both therapists are found
    assert with_email_index is not None, "Therapist with email not found"
    assert without_email_index is not None, "Therapist without email not found"
    
    # Therapist with email should come before therapist without email
    assert with_email_index < without_email_index, f"Email priority failed: with_email at {with_email_index}, without_email at {without_email_index}"
    
    # Cleanup
    self.safe_delete_therapist(therapist_with_email['id'])
    self.safe_delete_therapist(therapist_without_email['id'])

def test_send_anfrage_to_therapist_without_email(self):
    """Test that sending anfrage to therapist without email creates phone call."""
    # Create therapist WITHOUT email
    therapist = self.create_test_therapist(
        plz="52064",
        email=None,  # No email address
        telefon="+49 241 123456",
        telefonische_erreichbarkeit={
            "montag": ["10:00-12:00"],
            "mittwoch": ["14:00-16:00"]
        }
    )
    
    # Create patient for anfrage
    patient = self.create_test_patient(plz="52062")
    search_response = requests.post(
        f"{BASE_URL}/platzsuchen",
        json={"patient_id": patient['id']}
    )
    assert search_response.status_code == 201
    search = search_response.json()
    
    # Create anfrage
    anfrage_response = requests.post(
        f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
        json={
            "therapist_id": therapist['id'],
            "plz_prefix": "52",
            "sofort_senden": False
        }
    )
    
    if anfrage_response.status_code == 201:
        anfrage = anfrage_response.json()
        
        # Send the anfrage
        send_response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}/senden"
        )
        assert send_response.status_code == 200
        
        send_data = send_response.json()
        
        # Verify response structure for phone call
        assert send_data['communication_type'] == 'phone_call'
        assert send_data['email_id'] is None
        assert send_data['phone_call_id'] is not None
        assert 'sent_date' in send_data
        
        # Verify phone call was actually created in communication service
        phone_call_response = requests.get(
            f"http://localhost:8004/api/phone-calls?therapist_id={therapist['id']}&therapeutenanfrage_id={anfrage['anfrage_id']}"
        )
        assert phone_call_response.status_code == 200
        
        phone_calls = phone_call_response.json()['data']
        assert len(phone_calls) > 0, "Phone call was not created"
        
        phone_call = phone_calls[0]
        assert phone_call['therapist_id'] == therapist['id']
        assert phone_call['therapeutenanfrage_id'] == anfrage['anfrage_id']
        assert phone_call['status'] == 'geplant'
        
        # Cleanup anfrage
        try:
            requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}")
        except:
            pass
    
    # Cleanup
    self.safe_delete_platzsuche(search['id'])
    self.safe_delete_therapist(therapist['id'])
    self.safe_delete_patient(patient['id'])

def test_send_anfrage_to_therapist_with_email(self):
    """Test that sending anfrage to therapist with email still works normally."""
    # Create therapist WITH email
    therapist = self.create_test_therapist(
        plz="52064",
        email="therapist@example.com"
    )
    
    # Create patient for anfrage
    patient = self.create_test_patient(plz="52062")
    search_response = requests.post(
        f"{BASE_URL}/platzsuchen",
        json={"patient_id": patient['id']}
    )
    assert search_response.status_code == 201
    search = search_response.json()
    
    # Create anfrage
    anfrage_response = requests.post(
        f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
        json={
            "therapist_id": therapist['id'],
            "plz_prefix": "52",
            "sofort_senden": False
        }
    )
    
    if anfrage_response.status_code == 201:
        anfrage = anfrage_response.json()
        
        # Send the anfrage
        send_response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}/senden"
        )
        assert send_response.status_code == 200
        
        send_data = send_response.json()
        
        # Verify response structure for email
        assert send_data['communication_type'] == 'email'
        assert send_data['email_id'] is not None
        assert send_data['phone_call_id'] is None
        assert 'sent_date' in send_data
        
        # Cleanup anfrage
        try:
            requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}")
        except:
            pass
    
    # Cleanup
    self.safe_delete_platzsuche(search['id'])
    self.safe_delete_therapist(therapist['id'])
    self.safe_delete_patient(patient['id'])
```

---

## 2. Matching Service Code Changes

### File: `matching_service/algorithms/anfrage_creator.py`

#### Method: `get_therapists_for_selection()`

**Replace the existing sorting logic** (around line 120-140):

```python
# Sort according to business rules - EMAIL FIRST WITHIN EACH TIER
def sort_key(t):
    is_available = t.get('potenziell_verfuegbar', False)
    is_informed = t.get('ueber_curavani_informiert', False)
    has_email = bool(t.get('email'))  # NEW: Check if therapist has email
    
    # Priority order with email preference:
    # 1. Available AND informed WITH email (return 0)
    # 2. Available AND not informed WITH email (return 1)
    # 3. Not available AND informed WITH email (return 2)
    # 4. Others WITH email (return 3)
    # 5. Available AND informed WITHOUT email (return 4)
    # 6. Available AND not informed WITHOUT email (return 5)
    # 7. Not available AND informed WITHOUT email (return 6)
    # 8. Others WITHOUT email (return 7)
    
    base_priority = 0
    if is_available and is_informed:
        base_priority = 0
    elif is_available and not is_informed:
        base_priority = 1
    elif not is_available and is_informed:
        base_priority = 2
    else:
        base_priority = 3
    
    # Add 4 to priority if no email (pushes to second tier)
    if not has_email:
        base_priority += 4
    
    return (base_priority, t.get('nachname', ''), t.get('vorname', ''))
```

### File: `matching_service/services.py`

#### Method: `AnfrageService.send_anfrage()` 

**Replace the entire method** (around line 800-850):

```python
@staticmethod
def send_anfrage(
    db: Session,
    anfrage_id: int
) -> Dict[str, Any]:
    """Send an anfrage to the therapist via email or phone call.
    
    Args:
        db: Database session
        anfrage_id: ID of the anfrage
        
    Returns:
        Dictionary with sending result information
    """
    anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
    if not anfrage:
        logger.error(f"Anfrage {anfrage_id} not found")
        return {"success": False, "error": "Anfrage not found"}
    
    if anfrage.gesendet_datum:
        logger.warning(f"Anfrage {anfrage_id} already sent on {anfrage.gesendet_datum}")
        return {"success": False, "error": "Already sent", "sent_date": anfrage.gesendet_datum}
    
    # Get therapist data
    therapist = TherapistService.get_therapist(anfrage.therapist_id)
    if not therapist:
        logger.error(f"Therapist {anfrage.therapist_id} not found")
        return {"success": False, "error": "Therapist not found"}
    
    # Get patient data
    patient_ids = [ap.patient_id for ap in anfrage.anfrage_patients]
    patients = PatientService.get_patients(patient_ids)
    
    if len(patients) != anfrage.anfragegroesse:
        logger.error(f"Could not fetch all patients for anfrage {anfrage_id}")
        return {"success": False, "error": "Patient data incomplete"}
    
    # Create patient data list in anfrage order
    patient_data = []
    for ap in anfrage.anfrage_patients:
        if ap.patient_id in patients:
            patient_data.append(patients[ap.patient_id])
    
    # Check if therapist has email
    therapist_email = therapist.get('email')
    
    if therapist_email:
        # Send via email
        email_id = CommunicationService.create_anfrage_email(
            anfrage.therapist_id,
            patient_data,
            anfrage.id
        )
        
        if email_id:
            anfrage.mark_as_sent(email_id=email_id)
            db.commit()
            
            logger.info(f"Anfrage {anfrage_id} sent successfully via email {email_id}")
            return {
                "success": True,
                "communication_type": "email",
                "email_id": email_id,
                "phone_call_id": None,
                "sent_date": anfrage.gesendet_datum
            }
        else:
            logger.error(f"Failed to create email for anfrage {anfrage_id}")
            return {"success": False, "error": "Email creation failed"}
    
    else:
        # No email - create phone call instead
        phone_call_id = CommunicationService.schedule_follow_up_call(
            anfrage.therapist_id,
            anfrage.id
        )
        
        if phone_call_id:
            anfrage.mark_as_sent(phone_call_id=phone_call_id)
            db.commit()
            
            logger.info(f"Anfrage {anfrage_id} sent successfully via phone call {phone_call_id}")
            return {
                "success": True,
                "communication_type": "phone_call",
                "email_id": None,
                "phone_call_id": phone_call_id,
                "sent_date": anfrage.gesendet_datum
            }
        else:
            logger.error(f"Failed to schedule phone call for anfrage {anfrage_id}")
            return {"success": False, "error": "Phone call scheduling failed"}
```

### File: `matching_service/api/anfrage.py`

#### Method: `AnfrageSendResource.post()`

**Replace the method** (around line 650-700):

```python
def post(self, anfrage_id):
    """Send an anfrage via email or phone call."""
    try:
        with get_db_context() as db:
            anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
            
            if not anfrage:
                return {"message": f"Anfrage {anfrage_id} not found"}, 404
            
            if anfrage.gesendet_datum:
                return {
                    "message": "Anfrage already sent",
                    "sent_date": anfrage.gesendet_datum.isoformat()
                }, 400
            
            # Send the anfrage (handles both email and phone call)
            result = AnfrageService.send_anfrage(db, anfrage.id)
            
            if result["success"]:
                return {
                    "message": "Anfrage sent successfully",
                    "anfrage_id": anfrage.id,
                    "communication_type": result["communication_type"],
                    "email_id": result.get("email_id"),
                    "phone_call_id": result.get("phone_call_id"),
                    "sent_date": result["sent_date"].isoformat() if result["sent_date"] else None
                }, 200
            else:
                if result.get("error") == "Already sent":
                    return {
                        "message": "Anfrage already sent",
                        "sent_date": result["sent_date"].isoformat() if result.get("sent_date") else None
                    }, 400
                else:
                    return {"message": f"Failed to send anfrage: {result.get('error', 'Unknown error')}"}, 500
                    
    except Exception as e:
        logger.error(f"Error sending anfrage {anfrage_id}: {str(e)}", exc_info=True)
        return {"message": "Internal server error"}, 500
```

---

## 3. API Reference Updates

### File: `API_REFERENCE.md`

#### Update: `GET /therapeuten-zur-auswahl` Description

**Replace the existing sorting order section** (around line 1100):

```markdown
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
```

#### Update: `POST /therapeutenanfragen/{id}/senden` Response Examples

**Replace the existing response examples** (around line 1250):

```markdown
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
```

#### Add to Response Field Descriptions:

**Add after the existing response field list** (around line 1280):

```markdown
**Response Fields:**
- `communication_type` (string): Either "email" or "phone_call" indicating how the anfrage was sent
- `email_id` (integer|null): ID of created email if sent via email, null if sent via phone call
- `phone_call_id` (integer|null): ID of created phone call if sent via phone call, null if sent via email
- `sent_date` (string): ISO datetime when the communication was initiated
```

---

## Implementation Notes

### Database Schema
- No database changes required - all necessary fields already exist
- `therapeutenanfrage.phone_call_id` field already supports phone call linking
- `phone_call.therapeutenanfrage_id` field already supports anfrage linking

### Backwards Compatibility
- Existing email-based anfragen continue to work unchanged
- API consumers must handle the new response structure with both `email_id` and `phone_call_id` fields
- The `communication_type` field clearly indicates which method was used

### Error Handling
- Email creation failures still return errors as before
- Phone call scheduling failures return similar error structure
- Existing error responses remain unchanged for compatibility

### Follow-up Integration
- Phone calls created for anfragen are automatically linked via `therapeutenanfrage_id`
- Follow-up scheduling logic can identify and prioritize anfrage-related calls
- Existing follow-up automation continues to work for email-based anfragen

---

## Testing Checklist

- [ ] Integration tests pass for both email and phone call scenarios
- [ ] Therapist selection correctly prioritizes email-enabled therapists
- [ ] Anfrage sending creates appropriate communication method
- [ ] API responses include correct fields for both scenarios
- [ ] Phone calls are properly linked to anfragen
- [ ] Error handling works for both communication methods
- [ ] Backwards compatibility maintained for existing functionality