# Curavani System Refactoring - Implementation Plan

## Overview
This document outlines the planned changes to the Curavani patient registration system, including frontend modifications, backend updates, and database schema changes.

---

## 1. SYMPTOM SELECTION SYSTEM ✅

### Current State
- Text field for symptoms (100 characters max)
- Boolean field `hat_ptv11`
- Field `psychotherapeutische_sprechstunde`

### New Implementation
- Replace free text with structured symptom selection
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
- Remove: `hat_ptv11` field
- Remove: `psychotherapeutische_sprechstunde` field
- Modify: `symptome` field from TEXT to JSONB array
- Remove: All PTV11-related logic

---

## 2. STATIC PDF CONTRACT ✅

### Current State
- Dynamic PDF generation using `contract-pdf-generator.php`
- PDF generated from markdown contract files
- Sent immediately after registration

### New Implementation
- **Static PDF file:** Already prepared
- **Storage location:** `/private` directory
- **Single universal PDF:** Works for all cases
- **Naming:** Standard filename (no date customization)
- **Type:** Static document for reference (no fillable fields)
- **Database tracking:** Keep contract acceptance tracking (timestamp, version, etc.)
- **Contract text:** Still store in database for legal documentation

### Files to Modify
- Remove: `generate_contract.php`
- Remove: `contract-pdf-generator.php`
- Update: `verify_token.php` to serve static PDF

---

## 3. BACKEND PDF SENDING ✅

### Current State
- PDF sent via PHP in `sendSuccessEmailWithContract()` function
- Sent immediately after registration

### New Implementation
- **Trigger:** Send from backend after patient import (not from PHP)
- **Timing:** Independent of payment
- **Frontend message:** "PDF will be sent within 15 minutes"
- **Download button:** Keep on success page
- **Email service:** Only for email address verification
- **Error handling:** Backend retry mechanism + staff notifications

### Backend Requirements
- Add PDF sending to patient import process
- Implement retry mechanism
- Add failure notifications to staff
- Remove PDF sending from PHP frontend

---

## 4. CSS REPLACEMENT ✅

### Current State
- Using `curavani-styles.css` (1200+ lines)
- Complex styling with animations, gradients, shadows

### New Implementation
- **New file:** `curavani-simple.css` (provided)
- **Approach:** Minimal and functional
- **Mobile:** Still required
- **Multi-step form:** Keep with minimal progress bar
- **Contract sections:** Simple bordered boxes

### CSS Additions Needed
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

.progress-line {
    position: absolute;
    top: 16px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--border);
    z-index: -1;
}

.progress-line-fill {
    height: 100%;
    background: var(--primary);
    transition: width 0.3s ease;
}

/* Multi-step form additions */
.step-content {
    display: none;
}

.step-content.active {
    display: block;
}

/* Navigation buttons */
.nav-button {
    /* Extends .btn */
}

.nav-button.secondary {
    background-color: var(--gray-light);
    color: var(--text);
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

### Files to Update
- `registrierung.html` - change CSS reference
- `verify_token.php` - change CSS reference, adjust HTML classes

---

## 5. PATIENT STATUS LOGIC & PAYMENT ✅

### Current State
- `startdatum` set when `vertraege_unterschrieben` AND `psychotherapeutische_sprechstunde` are TRUE
- Status transitions unclear
- Voucher system in place

### New Implementation
- **Remove completely:**
  - All voucher logic
  - `gutschein` field
  - Voucher validation
  - Voucher-based pricing

- **New payment field:**
  - Add: `zahlung_eingegangen` (boolean)
  - Future: Separate invoice entity (not in this phase)

- **Status triggers:**
  - `startdatum` = Set when `vertraege_unterschrieben` AND `zahlung_eingegangen` are TRUE
  - Status "offen" → "auf_der_Suche" = When `startdatum` is set

### Database Changes
```sql
-- Add payment field
ALTER TABLE patient_service.patienten 
ADD COLUMN zahlung_eingegangen BOOLEAN DEFAULT FALSE;

-- Remove voucher-related fields (if they exist)
-- Remove gutschein or any voucher tracking
```

### Backend Logic Changes
- Update patient model
- Update status transition logic
- Remove all voucher validation
- Add payment confirmation workflow

---

## 6. THERAPIST EMAIL DEDUPLICATION ✅

### Problem Statement
- Multiple therapists can have the same email address (typical for practices)
- Practices often share one email for all therapists
- Need to avoid duplicate communications to the same practice

### Implementation Decision: Matching-Service Logic
The deduplication logic will be implemented entirely within the matching-service, keeping the therapist-service unchanged. This approach treats therapists with the same email as one logical unit for anfragen purposes.

### Core Logic
1. **Email Grouping (Dynamic)**
   - Group therapists by email address
   - Important: NULL/empty emails are NOT grouped (each is separate)
   - Grouping happens on-demand during therapist selection

2. **Exclusion Rules**
   - If ANY therapist in email group has cooling period → exclude entire group
   - If ANY therapist in email group is gesperrt → exclude entire group
   - If ANY therapist in email group has pending anfragen → exclude entire group

3. **Practice Owner Identification**
   Hierarchical rules to identify who to contact:
   
   **Rule 1: Last Name in Email (with umlaut variations)**
   - Check if therapist's nachname appears in email
   - Handle German umlauts: ä→ae/a, ö→oe/o, ü→ue/u, ß→ss
   - Example: "Mueller" matches "dr.mueller@praxis.de" or "dr.muller@praxis.de"
   
   **Rule 2: Professional Title**
   - Prefer therapist with "Dr." or "Prof." in titel field
   - If multiple have titles, use the one created first
   
   **Rule 3: Created First**
   - Fallback: Choose therapist with earliest created_at date

4. **Cooling Period Management**
   - When anfrage is sent: Update ONLY the contacted therapist's `naechster_kontakt_moeglich`
   - When checking eligibility: Consider cooling period of ANY therapist in email group
   - This ensures practice-level cooling while maintaining accurate individual records

### Implementation Location
```
matching_service/algorithms/anfrage_creator.py
└── get_therapists_for_selection()
    ├── Group therapists by email
    ├── Apply email-group-wide exclusions
    ├── Identify practice owner for each group
    └── Return only practice owners (or individual therapists without email groups)
```

### Edge Cases Handled
1. **Therapist Changes Practice**
   - When email changes, therapist automatically becomes independent
   - Old practice can be contacted again (remaining therapists have no cooling period)
   - Natural ungrouping through email change

2. **New Therapist Joins Practice**
   - Automatically grouped when imported with same email
   - Inherits group's exclusion status (if any member has cooling/blocking)

3. **Missing Email**
   - Therapists without email are treated individually
   - Never grouped with others

### No Database Changes Required
- All logic contained in matching-service
- Therapist-service remains unchanged
- Dynamic grouping based on current email values
- Historical accuracy maintained (only contacted therapist has cooling period)

### Benefits of This Approach
- **Flexibility:** Logic can be adjusted without affecting other services
- **Context-appropriate:** "Who to contact" is a matching concern, not therapist data
- **Import-friendly:** New therapists automatically handled correctly
- **Clean architecture:** Each service maintains its domain boundaries
- **Accurate history:** Individual cooling periods reflect actual contact

---

## 7. MINOR ITEMS ❓ PENDING

### Diagnosis Field
- **Question:** Remove from frontend but keep in backend?
- **Current:** `diagnose` field exists in database
- **Options:**
  1. Keep in DB but don't collect in registration
  2. Remove completely
  3. Add through different process later

---

## IMPLEMENTATION PHASES

### Phase 1: Frontend Changes
1. Update `registrierung.html` to use `curavani-simple.css`
2. Modify `verify_token.php`:
   - Replace symptom text field with checkbox selection
   - Remove PTV11 sections
   - Remove voucher field
   - Update CSS references
   - Simplify contract display
3. Remove email sending from PHP
4. Update success messages

### Phase 2: Backend Changes
1. Database migrations:
   - Add `zahlung_eingegangen` field
   - Modify `symptome` to JSONB
   - Remove PTV11 fields
2. Update patient import logic:
   - Handle new symptom format
   - Add PDF sending
   - Implement retry mechanism
3. Update status transition logic
4. Remove voucher validation

### Phase 3: Matching Service - Email Deduplication
1. Implement email grouping logic in `get_therapists_for_selection()`
2. Add practice owner identification with umlaut handling
3. Update exclusion checks for email groups
4. Test with various email scenarios
5. Add logging for transparency

### Phase 4: Testing & Deployment
1. Test registration flow
2. Test payment confirmation
3. Test PDF delivery
4. Test import processes
5. Test email deduplication logic
6. Test practice owner identification

---

## OPEN QUESTIONS FOR NEXT SESSION

1. **Diagnosis field handling** - keep in backend only or remove completely?
2. **Payment confirmation workflow** - manual process or automated integration?
3. **Staff notification preferences** - email, dashboard, or both?
4. **Import error handling details** - retry intervals, max attempts?
5. **Backwards compatibility** - handling existing patients without new fields?

---

## FILES TO BE MODIFIED

### Frontend
- `curavani_com/registrierung.html`
- `curavani_com/verify_token.php`
- `curavani_com/send_verification.php`
- `curavani_com/curavani-simple.css` (extend)
- Remove: `curavani_com/generate_contract.php`

### Backend - Patient Service
- `patient_service/models/patient.py`
- `patient_service/api/patients.py`
- `patient_service/imports/patient_importer.py`
- Database migration scripts (new)

### Backend - Communication Service
- Add PDF sending capability
- Add retry mechanism
- Add staff notifications

### Backend - Matching Service
- `matching_service/algorithms/anfrage_creator.py` (add email deduplication)
- No database changes required

### Backend - Therapist Service
- No changes required (deduplication handled in matching-service)

---

## NOTES
- This plan represents a significant simplification of the registration process
- Focus on reliability over complexity
- All changes should maintain backwards compatibility where possible
- Consider gradual rollout strategy
- Email deduplication keeps services decoupled and maintainable