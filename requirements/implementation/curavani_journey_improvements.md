# Curavani User Journey Improvements - Complete Implementation Guide
**Version:** 5.0  
**Date:** January 2025  
**Status:** Phase 1 (Contracts) & Phase 4 (Email) Completed!
**Last Updated:** January 2025

---

## Implementation Status Overview

### ✅ COMPLETED ITEMS (January 2025)

#### Phase 1: Contract Simplification - COMPLETED!
- ✅ Reduced from 6 to 4 contract parts
- ✅ Created `teil_a_vereinbarung.md` - Merged and simplified Teil A + Teil E
- ✅ Updated `teil_d_widerruf.md` - Removed Muster-Widerrufsformular reference
- ✅ Deleted `anlage_widerrufsformular.md` 
- ✅ Implemented price-independent contract language
- ✅ Added differentiated guarantees: 1 month (group) / 3 months (individual)
- ✅ Generated PDF versions of all contract documents
- ✅ Simplified language and removed unnecessary legal complexity

#### Phase 4: Email Confirmation System - COMPLETED!
- ✅ Created `email_bestaetigen.html` with improved UX
- ✅ Updated `verification_email.md` template
- ✅ Fixed template variables and fallbacks
- ✅ Implemented 4-step process indicators
- ✅ Updated email subject lines

#### Phase 3: Service Overview Page - COMPLETED!
- ✅ Created `service_buchen.html` 
- ✅ Implemented dynamic pricing from `prices.json`
- ✅ Removed all "Sonderaktion" references
- ✅ Clear guarantee differentiation

#### Terminology & Pricing Updates - COMPLETED!
- ✅ Changed "Registrierung" → "Therapieplatzsuche"
- ✅ Changed buttons to "Therapieplatz finden lassen"
- ✅ Centralized pricing in `prices.json`
- ✅ Removed hardcoded prices throughout

### ⏳ PENDING ITEMS

#### Phase 1b: Update PHP for New Contract Structure
- ⏳ Update `verify_token_functions.php` to use 4-part structure
- ⏳ Update `verify_token.php` to show only 4 contract steps
- ⏳ Update progress indicator from 7 steps to 5 steps
- ⏳ Remove references to Teil E and Widerrufsformular

#### Phase 2: Live Helper Chat Integration
- ⏳ Choose and configure chat solution
- ⏳ Add widget to all pages
- ⏳ Set up operator accounts

#### Phase 5: Main Registration Form Updates
- ⏳ Increase symptom selection from 3 to 6
- ⏳ Reduce availability requirement from 20 to 10 hours
- ⏳ Update contract display method (PDF links instead of inline)
- ⏳ Implement dynamic pricing display

#### Phase 6: Backend Email Automation
- ⏳ Payment confirmation emails
- ⏳ Weekly progress updates
- ⏳ Webinar invitations

---

## Phase 1b: Update PHP for New Contract Structure (NEXT PRIORITY)

### Required PHP Updates

#### 1. Update verify_token_functions.php

**Current Code (6 parts):**
```php
function getAllContractTexts() {
    $parts = ['a', 'b', 'c', 'd', 'e', 'widerrufsformular'];
    // ...
}
```

**New Code (4 parts):**
```php
function getAllContractTexts() {
    $parts = ['a', 'b', 'c', 'd'];
    // ...
}
```

**Update contract file mappings:**
```php
switch ($part) {
    case 'a':
        $filename = 'teil_a_vereinbarung.md';
        break;
    case 'b':
        $filename = 'teil_b_vollmacht.md';
        break;
    case 'c':
        $filename = 'teil_c_datenschutz.md';
        break;
    case 'd':
        $filename = 'teil_d_widerruf.md';
        break;
}
```

#### 2. Update verify_token.php Multi-Step Form

**Current Structure (7 steps):**
1. Personal Information
2. Contract Part A
3. Contract Part B  
4. Contract Part C
5. Contract Part D + Widerrufsformular
6. Contract Part E
7. Confirmation

**New Structure (5 steps):**
1. Personal Information
2. Contract Part A (simplified)
3. Contract Part B (Vollmacht)
4. Contract Part C (Datenschutz)
5. Contract Part D (Widerruf) + Confirmation

**Remove these consent checkboxes:**
- `consent_part_e`
- `consent_widerrufsformular`

**Update confirmation section in Step 5:**
```php
// Remove references to:
$requiredConsents = ['consent_part_a', 'consent_part_b', 'consent_part_c', 'consent_part_d'];
// Remove consent_part_e and consent_widerrufsformular
```

#### 3. Contract PDF Access

**Add PDF download functionality:**
```php
// In verify_token.php, add PDF download links
<a href="/contracts/teil_a_vereinbarung.pdf" target="_blank">Teil A als PDF</a>
<a href="/contracts/teil_b_vollmacht.pdf" target="_blank">Teil B als PDF</a>
<a href="/contracts/teil_c_datenschutz.pdf" target="_blank">Teil C als PDF</a>
<a href="/contracts/teil_d_widerruf.pdf" target="_blank">Teil D als PDF</a>
```

---

## Phase 5: Main Registration Form Updates (After Phase 1b)

### Form Field Changes Required

#### 1. Symptom Selection
```javascript
// Current validation
if (selectedSymptoms.length > 3) {
    alert('Sie können maximal 3 Symptome auswählen.');
}

// New validation
if (selectedSymptoms.length > 6) {
    alert('Sie können maximal 6 Symptome auswählen.');