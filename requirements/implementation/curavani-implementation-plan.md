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

## 6. THERAPIST EMAIL DEDUPLICATION ❓ PENDING

### Problem Statement
- Multiple therapists can have the same email address
- Practices often share one email
- Need to avoid duplicate communications

### Questions to Resolve
1. **Practice Owner Concept:**
   - Add field `praxis_inhaber_id` (references another therapist)?
   - Or add boolean `ist_praxis_inhaber`?
   - Different approach?

2. **Owner Identification:**
   - First registered = owner?
   - Manual designation?
   - Other criteria?

3. **Contact Rules:**
   - Only contact if `ist_praxis_inhaber = true` OR no practice link?
   - Add `kontaktierbar` boolean?

4. **Data Migration:**
   - Auto-mark first per email as owner?
   - Manual review?
   - Default all as contactable?

5. **Import Behavior:**
   - Auto-link to existing owner if email matches?
   - Create separate but non-contactable?

### Proposed Solution (TO BE DISCUSSED)
```sql
-- Option 1: Boolean flag
ALTER TABLE therapist_service.therapeuten
ADD COLUMN ist_praxis_inhaber BOOLEAN DEFAULT TRUE,
ADD COLUMN kontaktierbar BOOLEAN DEFAULT TRUE;

-- Option 2: Reference to owner
ALTER TABLE therapist_service.therapeuten
ADD COLUMN praxis_inhaber_id INTEGER REFERENCES therapist_service.therapeuten(id);
```

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

### Phase 3: Therapist Deduplication
- TO BE DEFINED

### Phase 4: Testing & Deployment
1. Test registration flow
2. Test payment confirmation
3. Test PDF delivery
4. Test import processes

---

## OPEN QUESTIONS FOR NEXT SESSION

1. **Therapist email deduplication approach** - needs decision
2. **Diagnosis field handling** - keep or remove?
3. **Payment confirmation workflow** - manual or automated?
4. **Staff notification preferences** - email, dashboard, both?
5. **Import error handling details** - retry intervals, max attempts?
6. **Backwards compatibility** - handling existing patients without new fields?

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

### Backend - Therapist Service
- TBD based on deduplication approach

---

## NOTES
- This plan represents a significant simplification of the registration process
- Focus on reliability over complexity
- All changes should maintain backwards compatibility where possible
- Consider gradual rollout strategy