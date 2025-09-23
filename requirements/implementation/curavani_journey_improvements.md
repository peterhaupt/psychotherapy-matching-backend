# Curavani User Journey Improvements - Complete Implementation Guide
**Version:** 3.0  
**Date:** January 2025  
**Status:** Partially Implemented
**Last Updated:** January 2025

---

## Implementation Status Overview

### ✅ COMPLETED ITEMS (January 2025)

#### Terminology Updates
- ✅ Changed "Jetzt Therapieplatz finden" → "Therapieplatz finden lassen" throughout
- ✅ Replaced "Service" → "Therapieplatzsuche" or "professionelle Unterstützung"
- ✅ Updated "Registrierung" → "Therapieplatzsuche starten"
- ✅ All links from `registrierung.html` → `service_buchen.html`

#### Pricing System Overhaul
- ✅ Implemented dynamic pricing from `prices.json`
- ✅ Removed all hardcoded prices
- ✅ Removed "Sonderaktion" (special offers) completely
- ✅ Added JavaScript fallback to "-" or "Preis auf Anfrage" on error
- ✅ Single source of truth for all pricing

#### Guarantee Time Differentiation
- ✅ Updated all guarantees to show: 1 Monat (Gruppentherapie) / 3 Monate (Einzeltherapie)
- ✅ Consistent messaging across all pages
- ✅ FAQ sections updated accordingly

#### Group Therapy Positioning
- ✅ Removed "upgrade" terminology
- ✅ Changed to "Wechsel zur Einzeltherapie möglich" (switch possible)
- ✅ Added benefits highlighting for group therapy
- ✅ Positioned as legitimate first choice, not budget option

#### Page Updates
- ✅ **patienten.html** - Fully updated with all changes
- ✅ **service_buchen.html** - Created with new approach and content

### ⏳ PENDING ITEMS

- ⏳ Phase 1: Contract simplification
- ⏳ Phase 2: Live Helper Chat integration
- ⏳ Phase 4: Email confirmation page updates
- ⏳ Phase 5: Main registration form updates
- ⏳ Phase 6: Backend email automation

---

## Current Problems Being Solved

### Already Addressed:
- ✅ Unclear pricing (now dynamic and centralized)
- ✅ Poor group therapy positioning (now presented as valuable option)
- ✅ Confusing terminology (standardized across site)

### Still To Address:
1. Confusing "Registrierung" terminology in email verification
2. Complex legal documents overwhelming patients
3. Form requirements too restrictive (3 symptoms max, 20 hours minimum)
4. No regular communication updates during therapy search
5. Missing support options during registration

---

## New User Journey

### Current Implementation:
1. **Click "Therapieplatz finden lassen"** → Service Overview Page (`service_buchen.html`)
2. **Service Overview** → Email Validation (still needs rename to `email_bestaetigen.html`)
3. **Email Confirmation** → Main Registration Form with service booking
4. **Form Submission** → Success page with payment instructions
5. **Payment Received** → Confirmation email (manual process currently)
6. **Weekly Updates** → Not yet implemented

---

## Pricing Management System (NEW - IMPLEMENTED)

### Current Setup
**Single Source of Truth:** `/prices.json`
```json
{
  "einzeltherapie": 95,
  "gruppentherapie": 45
}
```

### Implementation Details
- All pages load prices dynamically via JavaScript
- Consistent price loading script across pages
- Fallback handling for network/loading errors
- Price displays use span elements with IDs: `price-gruppe` and `price-einzel`

### Pages Using Dynamic Pricing:
- `patienten.html` ✅
- `service_buchen.html` ✅
- `verify_token.php` (pending update)
- Email templates (pending update)

---

## Phase 1: Create New Contract Files (PENDING)

### 1.1 Contract Structure Changes

**New Structure (4 parts instead of 6):**
- **teil_a_vereinbarung_simplified.md** - Merged version of Teil A + Teil E
- **teil_b_vollmacht.md** - Keep as is (power of attorney)
- **teil_c_datenschutz.md** - Keep as is (data protection)
- **teil_d_widerruf.md** - Keep as is (withdrawal rights)
- **DELETE:** anlage_widerrufsformular.md - Not needed, email withdrawal sufficient

### 1.2 Content for Simplified Teil A

**Remove these sections completely:**
- § 3(1) - Patient's obligation to report psychological changes
- § 3(2) - PTV-11 form submission requirement  
- § 4 - Entire liability section (Haftung)
- § 5(2) - Payment processor details
- § 6 - Data protection paragraphs 2-3 (keep only first sentence)
- From Teil E: Salvatorische Klausel (§2), Schriftformerfordernis (§3)

**Simplify but keep:**
- § 3(3) - 48-hour response requirement → Use simpler language
- § 3(4) - Keep therapist exclusion list as is
- § 3(5) - Keep digital communication consent

**Note:** Prices in contracts must be loaded dynamically or reference external pricing

### 1.3 Implementation Tasks

**Files to create/modify:**
- Create `/contracts/teil_a_vereinbarung_simplified.md`
- Update `verify_token_functions.php` to use new structure
- Update `getContractText()` function to handle simplified version
- Ensure contract PDFs show dynamic pricing

**Open Questions:**
- [ ] Legal review of simplified language needed
- [ ] Archive strategy for old contract versions
- [ ] Handling of patients who signed old contracts
- [ ] PDF generation with dynamic prices

---

## Phase 2: Configure Live Helper Chat (PENDING)

### 2.1 Service Setup

**Provider:** LiveHelperChat (https://livehelperchat.com)
- Open source option available
- Self-hosted or cloud version
- GDPR compliant

### 2.2 Configuration Requirements

**Trigger Settings:**
- **Proactive invitation after:** 30 seconds on page
- **Pages to monitor:** `service_buchen.html`, `email_bestaetigen.html`, `verify_token.php`
- **Show widget on:** All pages

### 2.3 Chat Messages

**Initial greeting:**
```
"Hallo! 👋 Haben Sie Fragen zur Therapieplatzsuche? Ich helfe Ihnen gerne!"
```

### 2.4 Implementation Tasks

- Install LiveHelperChat
- Add JavaScript snippet to all HTML pages
- Configure operators and hours
- Create canned responses

**Decision Needed:**
- [ ] Self-hosted vs cloud version
- [ ] Operating hours
- [ ] Number of operators

---

## Phase 3: Process Overview Page (✅ COMPLETED - Modified)

### 3.1 Status: IMPLEMENTED

**URL:** `/service_buchen.html` ✅
**Title:** "Therapieplatz finden lassen - Ihre persönliche Therapieplatzsuche | Curavani" ✅

### 3.2 Actual Implementation vs Plan

**What was implemented:**
- Clear 4-step booking process visualization
- Dynamic pricing from `prices.json`
- Improved group therapy information and positioning
- Support section with contact options
- Mobile-responsive design

**What differs from original plan:**
- No crossed-out regular prices (removed Sonderaktion completely)
- More emphasis on group therapy benefits
- Added info box about group therapy satisfaction rates

**Still pending:**
- LiveHelperChat widget integration
- A/B testing setup

---

## Phase 4: Update Email Confirmation Logic (PENDING)

### 4.1 Page Rename Required

**Current:** `registrierung.html`
**Target:** `email_bestaetigen.html`

### 4.2 Required Updates

- Change page title and headings
- Add clear warnings about email-only confirmation
- Update button text to "E-Mail-Adresse bestätigen"
- Modify email template in `send_verification.php`

**Note:** All buttons/links pointing to this page have been updated to use new URL

### 4.3 Implementation Tasks

- Rename file (server-side)
- Update .htaccess redirects from old URL
- Test email flow end-to-end

---

## Phase 5: Update Main Registration Form (PENDING)

### 5.1 Form Field Changes

**Location:** `verify_token.php`

### 5.2 Required Updates

#### Symptoms Selection
- **Current:** Max 3 symptoms
- **Target:** Max 6 symptoms
- Update validation in PHP and JavaScript

#### Previous Therapy Field
- **Current:** Date picker
- **Target:** Dropdown with 3 options
- Add validation for <2 years restriction

#### Availability Requirements  
- **Current:** Minimum 20 hours
- **Target:** Minimum 10 hours
- Update all validation logic

#### Contract Display
- **Current:** Full text in form
- **Target:** Summary + modal approach
- Create PDF download endpoints

#### Pricing Display
- Must load from `prices.json` (not hardcoded)
- Show both therapy options with benefits

### 5.3 Implementation Tasks

- Update form validations
- Create modal system for contracts
- Integrate dynamic pricing
- Test multi-step form flow

---

## Phase 6: Backend Email Automation (PENDING)

### 6.1 Payment Confirmation Email

**Trigger:** Payment marked as received
**Content:** Welcome message + webinar invitation

### 6.2 Weekly Progress Updates

**Trigger:** Every Monday at 9:00 AM
**Content:** Number of therapists contacted + encouragement

### 6.3 Implementation Requirements

**Database changes:**
- Add payment_confirmed_at timestamp
- Add email_log table
- Add weekly_update_last_sent field

**Services to create:**
- Payment confirmation service
- Weekly update cron job
- Email template system

---

## File Change Summary

### ✅ Files COMPLETED:
1. `/service_buchen.html` - Created with new content and approach
2. `/patienten.html` - Updated with all terminology and pricing changes
3. `/prices.json` - Now single source of truth for pricing

### ⏳ Files to CREATE:
1. `/contracts/teil_a_vereinbarung_simplified.md` - Simplified contract
2. `/services/weekly_update_service.py` - Email automation
3. `/services/payment_confirmation_service.py` - Payment emails

### ⏳ Files to RENAME:
1. `/registrierung.html` → `/email_bestaetigen.html`

### ⏳ Files to UPDATE:
1. `/email_bestaetigen.html` - New warnings and text
2. `/send_verification.php` - New email template
3. `/verify_token.php` - Form changes, dynamic pricing
4. `/verify_token_functions.php` - Validation changes
5. `/curavani-simple.css` - Styles for modals
6. All pages - Add LiveHelperChat widget

### ⏳ Files to DELETE:
1. `/contracts/anlage_widerrufsformular.md`

---

## Testing Checklist

### ✅ Completed Testing:
- [x] "Therapieplatz finden lassen" buttons work correctly
- [x] Dynamic price loading from JSON
- [x] Fallback handling for price loading errors
- [x] Mobile responsiveness of service_buchen.html
- [x] Correct guarantee times displayed

### ⏳ Pending Testing:
- [ ] Email validation page warnings
- [ ] Contract modal functionality
- [ ] PDF downloads
- [ ] Payment confirmation emails
- [ ] Weekly update triggers
- [ ] Live chat widget
- [ ] Form validation changes

---

## Rollback Plan

### For Completed Changes:
- Git revert to previous versions if issues arise
- Prices can be updated instantly via `prices.json`
- Terminology changes are reversible via content update

### For Pending Changes:
- Phase-by-phase rollout with feature flags
- Each phase independently reversible
- Database changes with migration scripts

---

## Success Metrics

### Currently Tracking:
- Page load times with dynamic pricing
- JavaScript error rates
- User engagement with new service_buchen.html page

### To Implement:
- Registration completion rate
- Drop-off at each step
- Support ticket reduction
- Live chat engagement
- Email open rates
- Weekly update effectiveness

---

## Outstanding Decisions

### Immediate Priorities:
1. **Contract Simplification:** Need legal review timeline
2. **Email Page Rename:** Schedule for minimal disruption
3. **Live Chat:** Choose between self-hosted vs cloud

### Before Full Launch:
1. A/B testing strategy for form changes
2. Email service provider selection
3. Webinar platform decision
4. Support staffing for live chat

---

## Next Steps Priority Order

1. **HIGH:** Rename registrierung.html → email_bestaetigen.html (user confusion)
2. **HIGH:** Implement simplified contracts (reduce drop-off)
3. **MEDIUM:** Set up live chat (improve support)
4. **MEDIUM:** Update form validations (reduce restrictions)
5. **LOW:** Implement email automation (nice to have)

---

## Version History

- **v3.0** (January 2025): Updated with completed implementations, dynamic pricing system
- **v2.0** (January 2025): Initial comprehensive plan
- **v1.0** (December 2024): Original requirements

**Document Status:** Living document, updated as implementation progresses
**Next Review:** After Phase 4 implementation
**Owner:** Development Team