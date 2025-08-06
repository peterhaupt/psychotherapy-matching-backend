# Curavani System Implementation Plan - Final Version

## Overview
This document outlines the complete implementation plan for the Curavani patient registration system refactoring, including all frontend modifications, backend updates, and database schema changes.

---

## 1. SYMPTOM SELECTION SYSTEM

### Implementation Decision
- **Field Type:** JSONB array (not ENUM)
- **Rationale:** Flexibility for future changes without database migrations
- **Validation:** Application layer validation against symptom list

### Requirements
- **Selection Rules:**
  - Minimum: 1 symptom
  - Maximum: 3 symptoms
  - No free text field
  - No priority/severity indicators

### Symptom List (30 items)
```
HÄUFIGSTE ANLIEGEN (Top 5 - prominent placement)
□ Depression / Niedergeschlagenheit
□ Ängste / Panikattacken
□ Burnout / Erschöpfung
□ Schlafstörungen
□ Stress / Überforderung

STIMMUNG & GEFÜHLE
□ Trauer / Verlust
□ Reizbarkeit / Wutausbrüche
□ Stimmungsschwankungen
□ Innere Leere
□ Einsamkeit

DENKEN & GRÜBELN
□ Sorgen / Grübeln
□ Selbstzweifel
□ Konzentrationsprobleme
□ Negative Gedanken
□ Entscheidungsschwierigkeiten

KÖRPER & GESUNDHEIT
□ Psychosomatische Beschwerden
□ Chronische Schmerzen
□ Essstörungen
□ Suchtprobleme (Alkohol/Drogen)
□ Sexuelle Probleme

BEZIEHUNGEN & SOZIALES
□ Beziehungsprobleme
□ Familienkonflikte
□ Sozialer Rückzug
□ Mobbing
□ Trennungsschmerz

BESONDERE BELASTUNGEN
□ Traumatische Erlebnisse
□ Zwänge
□ Selbstverletzung
□ Suizidgedanken
□ Identitätskrise
```

### Database Changes
- **Modify:** `symptome` field from TEXT to JSONB array
- **Remove:** `hat_ptv11` field (completely)
- **Remove:** `psychotherapeutische_sprechstunde` field (completely)
- **Remove:** All PTV11-related logic and triggers

### Validation Implementation
```python
# Application layer validation
VALID_SYMPTOMS = [
    "Depression / Niedergeschlagenheit",
    "Ängste / Panikattacken",
    # ... full list
]

def validate_symptoms(symptoms):
    if not 1 <= len(symptoms) <= 3:
        raise ValueError("Between 1 and 3 symptoms required")
    for symptom in symptoms:
        if symptom not in VALID_SYMPTOMS:
            raise ValueError(f"Invalid symptom: {symptom}")
```

---

## 2. STATIC PDF CONTRACT

### Implementation Details
- **Type:** Static PDF file (pre-created, not generated)
- **Storage:** `/private` directory
- **Filename:** `[PDF_FILENAME]` (placeholder - to be provided)
- **Delivery:** Via backend email after patient import
- **Frontend:** Remove PDF generation logic entirely

### Files to Remove
- `generate_contract.php`
- `contract-pdf-generator.php`
- All PDF generation dependencies

### Files to Update
- `verify_token.php`: Remove PDF generation, keep download button (serves static file)

---

## 3. BACKEND PDF SENDING

### Workflow
1. Patient completes registration (PHP frontend)
2. Patient data imported to backend
3. **Backend immediately sends PDF via email** (not tied to payment)
4. Success page shows: "PDF will be sent within 15 minutes"

### Implementation
- **Location:** Patient import process
- **Timing:** Immediately after successful import
- **Method:** Simple email with PDF attachment
- **Retry logic:** Not needed for Phase 1
- **Staff notifications:** Not needed for Phase 1

### Communication Service Changes
- Add PDF attachment capability to email sending
- No retry mechanism needed initially
- No staff notification system needed initially

---

## 4. CSS REPLACEMENT

### Implementation
- **Replace:** `curavani-styles.css` with `curavani-simple.css`
- **Multi-step form:** Keep with minimal progress bar
- **Contract display:** Simple bordered boxes
- **Mobile support:** Required

### Additional CSS Required
```css
/* Add to curavani-simple.css */

/* Progress Bar */
.progress-container {
    margin-bottom: var(--space-lg);
}

.progress-steps {
    display: flex;
    justify-content: space-between;
    position: relative;
    margin-bottom: var(--space-md);
}

.progress-step {
    flex: 1;
    text-align: center;
    position: relative;
}

.progress-step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--gray-light);
    color: var(--text-light);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin: 0 auto var(--space-xs);
}

.progress-step.active .progress-step-number {
    background: var(--primary);
    color: white;
}

.progress-step.completed .progress-step-number {
    background: var(--primary);
    color: white;
}

/* Multi-step form */
.step-content {
    display: none;
}

.step-content.active {
    display: block;
}

/* Contract containers */
.contract-container {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--space-md);
    max-height: 400px;
    overflow-y: auto;
    margin-bottom: var(--space-md);
}

/* Checkbox groups for symptoms */
.symptom-group {
    margin-bottom: var(--space-md);
}

.symptom-group h4 {
    color: var(--primary);
    margin-bottom: var(--space-sm);
}

.symptom-checkbox {
    display: flex;
    align-items: center;
    margin-bottom: var(--space-xs);
}

.symptom-checkbox input[type="checkbox"] {
    margin-right: var(--space-sm);
}
```

---

## 5. DIAGNOSIS FIELD REMOVAL

### Decision
- **Remove completely from database**
- **Remove from all frontends**
- **No migration for existing data**

### Database Changes
```sql
ALTER TABLE patient_service.patienten 
DROP COLUMN diagnose;
```

### Code Changes
- Remove from patient model
- Remove from API endpoints
- Remove from PHP registration form
- Remove from import logic

---

## 6. PAYMENT & STATUS LOGIC

### Remove Completely
- All voucher/gutschein logic
- Voucher validation
- Voucher-based pricing
- PTV11 checks

### Add Payment Field
```sql
ALTER TABLE patient_service.patienten 
ADD COLUMN zahlung_eingegangen BOOLEAN DEFAULT FALSE;
```

### Automated Status Transitions
When staff sets `zahlung_eingegangen = true` in React frontend:
1. **Backend automatically:**
   - Sets `startdatum = today` (if `vertraege_unterschrieben = true`)
   - Changes `status` from "offen" → "auf_der_suche"
2. **Triggers:** Matching service notifications

### React Frontend Requirements
- Add payment confirmation checkbox
- Display payment status
- Allow staff to mark payment received
- Show automatic status changes

---

## 7. PHP FRONTEND CHANGES

### Remove Sections
1. **PTV11 Section (complete removal):**
```html
<!-- REMOVE THIS ENTIRE SECTION -->
<div class="form-group">
    <label>Haben Sie ein aktuelles PTV11-Formular (nicht älter als vier Wochen)? <span class="required">*</span></label>
    <div class="section-intro" style="...">
        <strong>Hinweis:</strong> Dieses Formular bekommen Sie normalerweise...
    </div>
    <div class="checkbox-group">
        <input type="radio" id="ptv11_ja" name="hat_ptv11" value="true" required>
        <label for="ptv11_ja">Ja</label>
        <input type="radio" id="ptv11_nein" name="hat_ptv11" value="false" required>
        <label for="ptv11_nein">Nein</label>
    </div>
</div>
```

2. **Voucher/Gutschein fields**
3. **All voucher validation logic**

### Success Page (`verify_token.php`)
**Keep:**
- Payment instructions (IBAN, reference number)
- Contract download button (serves static PDF)
- Success message

**Remove:**
- PTV11 references
- Voucher/discount information
- Dynamic PDF generation

**Update message to:**
"Vielen Dank für Ihre Registrierung! Sie erhalten in den nächsten 15 Minuten eine E-Mail mit den Vertragsunterlagen."

### Symptom Selection
- Replace text field with checkbox interface
- Group symptoms by category
- Enforce 1-3 selection limit
- Store as JSONB array

---

## 8. IMPORT ERROR HANDLING

### Current Implementation (Sufficient for Phase 1)
- **Patient Import Errors:** Send to system notifications
- **Therapist Import Errors:** Send to system notifications
- **Manual handling:** Staff reviews and fixes errors
- **No automatic retry:** Manual re-import if needed

### System Notifications
- Email to configured admin address
- Include error details and affected file
- Daily summary for therapist imports

---

## 9. EXISTING PATIENT MIGRATION

### Approach
- **Manual updates** for small patient count
- No automated migration script needed
- Staff updates symptoms through React frontend

### Process
1. Export current patient list
2. Map text symptoms to new symptom list
3. Update via React admin interface
4. Verify all patients have valid symptom arrays

---

## IMPLEMENTATION PHASES

## Phase 1: Frontend Changes (Priority)
**Timeline: Week 1**

### PHP Frontend (`curavani_com/`)
1. Update `registrierung.html`:
   - Replace CSS reference to `curavani-simple.css`
   - Replace symptom text with checkbox selection
   - Remove PTV11 section completely
   - Remove voucher fields

2. Update `verify_token.php`:
   - Remove PDF generation code
   - Update success messages
   - Keep payment instructions
   - Serve static PDF on download

3. Remove files:
   - `generate_contract.php`
   - `contract-pdf-generator.php`

### Database Migrations
```sql
-- Remove diagnosis field
ALTER TABLE patient_service.patienten DROP COLUMN diagnose;

-- Remove PTV11 fields
ALTER TABLE patient_service.patienten DROP COLUMN hat_ptv11;
ALTER TABLE patient_service.patienten DROP COLUMN psychotherapeutische_sprechstunde;

-- Change symptome to JSONB
ALTER TABLE patient_service.patienten 
ALTER COLUMN symptome TYPE JSONB USING symptome::JSONB;

-- Add payment field
ALTER TABLE patient_service.patienten 
ADD COLUMN zahlung_eingegangen BOOLEAN DEFAULT FALSE;
```

---

## Phase 2: Backend Updates
**Timeline: Week 1-2**

### Patient Service
1. Update models:
   - Remove diagnosis field
   - Remove PTV11 fields
   - Change symptome to JSONB
   - Add zahlung_eingegangen field

2. Update import logic:
   - Handle new symptom format
   - Remove diagnosis handling
   - Add PDF sending after import

3. Update API:
   - Add payment confirmation endpoint
   - Automatic status transition logic

### Communication Service
1. Add PDF attachment capability
2. Static PDF serving
3. Simple email sending (no retry logic needed)

### Status Transition Logic
```python
def confirm_payment(patient_id):
    patient = get_patient(patient_id)
    patient.zahlung_eingegangen = True
    
    if patient.vertraege_unterschrieben:
        patient.startdatum = date.today()
        patient.status = "auf_der_suche"
        # Trigger matching service
        publish_search_started(patient_id)
    
    save(patient)
```

---

## Phase 3: Therapist Email Deduplication (Future)
**Timeline: Phase 2 completion + 2 weeks**

### Matching Service Implementation
Location: `matching_service/algorithms/anfrage_creator.py`

### Core Logic
1. Group therapists by email (NULL emails not grouped)
2. Apply group-wide exclusions (cooling period, blocked status)
3. Identify practice owner:
   - Check last name in email (with umlaut handling)
   - Prefer professional titles (Dr., Prof.)
   - Fall back to earliest created
4. Return only practice owners for selection

### No Database Changes Required
- All logic in matching service
- Dynamic grouping based on current emails
- Individual cooling periods maintained

---

## Phase 4: Testing & Deployment
**Timeline: 1 week after Phase 2**

### Testing Checklist
1. **Registration Flow:**
   - [ ] Symptom selection (1-3 limit)
   - [ ] No PTV11 questions
   - [ ] No voucher fields
   - [ ] Contract acceptance

2. **Backend Processing:**
   - [ ] Patient import successful
   - [ ] PDF sent via email
   - [ ] Payment confirmation works
   - [ ] Automatic status change

3. **React Frontend:**
   - [ ] Payment marking interface
   - [ ] Status displays correctly
   - [ ] Patient management works

4. **Error Handling:**
   - [ ] Import errors notify admins
   - [ ] System remains stable

---

## FILES TO BE MODIFIED

### Frontend - PHP
- `curavani_com/registrierung.html` - Update form
- `curavani_com/verify_token.php` - Update success page
- `curavani_com/send_verification.php` - Remove voucher logic
- `curavani_com/css/curavani-simple.css` - Extend with new styles
- **Remove:** `curavani_com/generate_contract.php`
- **Remove:** `curavani_com/contract-pdf-generator.php`

### Backend - Patient Service
- `patient_service/models/patient.py` - Update model
- `patient_service/api/patients.py` - Update endpoints
- `patient_service/imports/patient_importer.py` - Add PDF sending

### Backend - Communication Service
- `communication_service/api/emails.py` - Add PDF attachment
- `communication_service/services/email_service.py` - PDF handling

### Backend - Matching Service
- **Phase 3:** `matching_service/algorithms/anfrage_creator.py` - Email deduplication

### Database Migrations
- New migration scripts for schema changes

---

## CONFIGURATION REQUIREMENTS

### Environment Variables
```bash
# PDF Configuration
PDF_STATIC_FILE="/private/[PDF_FILENAME]"
PDF_SEND_DELAY_MINUTES=15

# Payment Settings
AUTO_STATUS_CHANGE_ON_PAYMENT=true
DEFAULT_SEARCH_STATUS="auf_der_suche"

# Import Settings
IMPORT_ERROR_EMAIL="admin@curavani.de"
```

---

## OPERATIONAL NOTES

### Manual Processes
1. **Payment Confirmation:** Staff marks in React frontend
2. **Import Errors:** Staff reviews email notifications
3. **Existing Patients:** Manual symptom updates

### Automated Processes
1. **PDF Sending:** After patient import
2. **Status Changes:** On payment confirmation
3. **Search Initiation:** When startdatum is set

### Future Enhancements (Not Phase 1)
- Automated payment detection
- Import retry mechanism
- Advanced staff notifications
- Therapist email deduplication (Phase 3)
- Patient portal for status tracking

---

## SUCCESS CRITERIA

### Phase 1 Complete When:
- [ ] Registration works without PTV11/voucher
- [ ] Symptoms stored as JSONB array
- [ ] Static PDF sent via email
- [ ] Payment can be confirmed manually
- [ ] Status changes automatically

### Phase 2 Complete When:
- [ ] All backend services updated
- [ ] Import process handles new format
- [ ] React frontend shows payment status
- [ ] Automatic workflows functioning

### Phase 3 Complete When:
- [ ] Therapist deduplication working
- [ ] No duplicate emails to practices
- [ ] Practice owner identification correct

---

## RISK MITIGATION

### Potential Issues & Solutions
1. **PDF Delivery Failures**
   - Monitor email logs
   - Manual resend option in React

2. **Import Format Changes**
   - Validate before import
   - Clear error messages

3. **Payment Status Confusion**
   - Clear UI in React frontend
   - Audit log for changes

4. **Symptom Data Quality**
   - Frontend validation
   - Backend validation
   - Regular data audits

---

## NOTES
- This plan prioritizes simplicity and reliability
- Manual processes acceptable for low volume
- Automation can be added incrementally
- Focus on staff usability in React frontend
- Patient experience simplified in PHP frontend